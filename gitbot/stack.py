from gitbot import generator
from gitbot.conf import ConfigDict
from gitbot.lib.s3 import Bucket
import json


def validate_stack(config):
    config, env = generator.render_project(config)
    from boto.cloudformation import connect_to_region

    cf = connect_to_region(config.region)
    files = generator.get_source_files(config)
    for rpath, (source, target) in files.iteritems():
        if not target.exists:
            generator.render_source_file(env, config, source, target)
            txt = target.read_all()
            cf.validate_template(template_body=txt)


def get_params(config):
    config, env = generator.render_project(config)
    files = generator.get_source_files(config)

    if len(files) == 1:
        main_stack = tuple(files)[0]
    else:
        try:
            main_stack = config.publish.main
        except AttributeError:
            raise Exception(
                'You must specify a `main` stack in configuration')

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


def publish_stack(config):
    config, env = generator.render_project(config)
    files = generator.get_source_files(config)
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
    return ConfigDict(result)


def create_stack(config):
    pass


def update_stack(config):

    pass
