from boto.cloudformation import connect_to_region
from gitbot import generator
from gitbot.conf import ConfigDict
from gitbot.lib.s3 import Bucket
from jinja2 import contextfunction, Environment
import json
import time


def validate_stack(config):
    config, env, files = generator.render_project(config)
    cf = connect_to_region(config.region)
    for rpath, (source, target) in files.iteritems():
        cf.validate_template(template_body=target.read_all())


def _get_main_stack(config, files):
    if len(files) == 1:
        main_stack = tuple(files)[0]
    else:
        try:
            main_stack = config.publish.main
        except AttributeError:
            raise Exception(
                'You must specify a `main` stack in configuration')
    return main_stack


def get_params(config):
    config, env, files = generator.render_project(config)
    main_stack = _get_main_stack(config, files)
    try:
        source, target = files[main_stack]
    except KeyError:
        raise Exception(
            'Cannot find the main stack[{main}]'.format(main=main_stack))

    obj = json.loads(target.read_all())
    params = obj.get('Parameters', {})

    result = ConfigDict()
    for param, info in params.iteritems():
        value = config.publish.params.get(param, None)
        if not value:
            value = info.get('Default', None)
        info['value'] = value
        result[param] = ConfigDict(info)
    return result


def upload_stack(config):
    config, env, files = generator.render_project(config)
    bucket_name = config.publish.get('bucket', None)
    if not bucket_name:
        raise Exception(
            'You need to provide a bucket name for publishing your stack.')
    path = config.publish.get('path', None)
    if path:
        path = path.rstrip('/') + '/'
    bucket = Bucket(bucket_name)
    bucket.make()
    result = {}
    url_format = 'http://{bucket_name}.s3.amazonaws.com/{path}{template_name}'
    for rpath, (source, target) in files.iteritems():
        full_path = bucket.add_file(target, acl='private', target_folder=path)
        signed_url = bucket.get_signed_url(full_path)
        url = url_format.format(bucket_name=bucket_name,
                                path=path,
                                template_name=rpath)
        result[rpath] = dict(url=url, source=source, target=target)
    return ConfigDict(dict(result=result, files=files, config=config))


def _transform_params(config, params, uploaded):

    @contextfunction
    def url(context, rpath):
        return uploaded.result[rpath]['url']

    context = dict(config=config)
    result = []
    env = Environment(trim_blocks=True)
    for name, value in params.iteritems():
        t = env.from_string(value, globals=dict(url_for=url))
        result.append((name, t.render(context)))
    return result


def publish_stack(config, params=None, debug=False, wait=False):
    uploaded = upload_stack(config)
    config = uploaded.config
    main_stack = _get_main_stack(uploaded.config, uploaded.files)
    try:
        main = uploaded.result[main_stack]
    except KeyError:
        raise Exception(
            'Cannot find the main stack[{main}]'.format(main=main_stack))
    try:
        stack_name = config.publish.stack_name
    except AttributeError:
        raise Exception('Stack name is required in configuration[publish.stack_name].')

    defaults = get_params(config)
    args = ConfigDict({name: info['value'] for name, info in defaults.iteritems()})
    args.patch(params)
    params = args
    region = config.publish.get('region', 'us-east-1')

    # Connect to cloud formation and create the stack
    cf = connect_to_region(region)
    try:
        cf.describe_stacks(stack_name)
        update = True
    except:
        update = False
    params = _transform_params(config, params, uploaded)
    print params
    print uploaded
    fn = cf.update_stack if update else cf.create_stack
    try:
        fn(stack_name,
            disable_rollback=debug,
            capabilities=['CAPABILITY_IAM'],
            template_url=main['url'],
            parameters=params)
    except Exception as e:
        raise

    if wait:
        while True:
            stacks = cf.list_stacks()
            if any((s.stack_status == 'CREATE_IN_PROGRESS' for s in stacks)):
                time.sleep(15)
            else:
                break


def delete_stack(config, wait=False):
    try:
        stack_name = config.publish.stack_name
    except KeyError:
        raise Exception('Stack name is required in configuration[publish.stack_name].')

    region = config.publish.get('region', 'us-east-1')

    # Connect to cloud formation and create the stack
    cf = connect_to_region(region)
    cf.delete_stack(stack_name)
    if wait:
        while True:
            stacks = cf.list_stacks()
            if any((s.stack_status == 'DELETE_IN_PROGRESS' for s in stacks)):
                time.sleep(15)
            else:
                break
