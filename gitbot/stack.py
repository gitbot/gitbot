from boto.cloudformation import connect_to_region
from gitbot import generator
from gitbot.conf import ConfigDict
from gitbot.lib.s3 import Bucket
from jinja2 import contextfunction, Environment
import json


def validate_stack(config):
    config, env, files = generator.render_project(config)
    cf = connect_to_region(config.region)
    for rpath, (source, target) in files.iteritems():
        if not target.exists:
            generator.render_source_file(env, config, source, target)
            txt = target.read_all()
            cf.validate_template(template_body=txt)


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
        print (param, value)
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
    bucket = Bucket(bucket_name)
    bucket.make()
    result = {}
    for rpath, (source, target) in files.iteritems():
        full_path = bucket.add_file(target, acl='private', target_folder=path)
        url = bucket.get_signed_url(full_path)
        result[rpath] = dict(url=url, source=source, target=target)
    return ConfigDict(dict(result=result, files=files, config=config))


def _transform_params(config, params, uploaded):
    @contextfunction
    def url(context, rpath):
        return uploaded[rpath]['url']
    context = dict(config=config)
    result = []
    env = Environment(trim_blocks=True)
    for name, value in params.iteritems():
        t = env.from_string(value, globals=dict(url=url))
        result.append((name, t.render(context)))
    return result


def publish_stack(config, params, debug=False):
    uploaded = upload_stack(config)
    main_stack = _get_main_stack(uploaded.config, uploaded.files)
    try:
        stack = uploaded[main_stack]
    except KeyError:
        raise Exception(
            'Cannot find the main stack[{main}]'.format(main=main_stack))
    try:
        stack_name = config.publish.stack_name
    except KeyError:
        raise Exception('Stack name is required in configuration[publish.stack_name].')

    region = config.publish.get('region', 'us-east-1')

    # Connect to cloud formation and create the stack
    cf = connect_to_region(region)
    try:
        cf.describe_stacks(stack_name)
        update = True
    except:
        update = False
    params = [(k, v) for k, v in params.iteritems()]
    fn = cf.update_stack if update else cf.create_stack
    try:
        fn(stack_name,
            disable_rollback=debug,
            capabilities=['CAPABILITY_IAM'],
            template_url=uploaded[stack]['url'],
            parameters=params)
    except Exception as e:
        print json.dumps(e)
        raise
