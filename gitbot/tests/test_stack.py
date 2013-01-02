# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from fswrap import File
from gitbot import stack
from gitbot.lib.s3 import Bucket
from nose import with_setup
import urllib2
from util import assert_text_equals
import yaml


TEST_ROOT = File(__file__).parent
BEES_ROOT = TEST_ROOT.child_folder('bees')
SOURCE_ROOT = BEES_ROOT.child_folder('source')
SCRIPT_ROOT = BEES_ROOT.child_folder('scripts')
TEMP = BEES_ROOT.child_folder('tmp')


def teardown():
    TEMP.delete()


def delete_bucket():
    conf_path = BEES_ROOT.child('project.yaml')
    config = yaml.load(File(conf_path).read_all())
    config['file_path'] = conf_path
    bucket_name = config['publish']['bucket']
    bucket = Bucket(bucket_name)
    bucket.connect()
    bucket.delete(recurse=True)


def test_validate():
    conf_path = BEES_ROOT.child('project.yaml')
    conf = yaml.load(File(conf_path).read_all())
    conf['file_path'] = conf_path
    stack.validate_stack(conf)


@with_setup(teardown=delete_bucket)
def test_upload_stack():
    conf_path = BEES_ROOT.child('project.yaml')
    conf = yaml.load(File(conf_path).read_all())
    conf['file_path'] = conf_path
    uploaded = stack.upload_stack(conf)['result']
    bucket_name = conf['publish']['bucket']
    bucket = Bucket(bucket_name)
    bucket.connect()
    bucket.set_policy()
    for rpath, info in uploaded.iteritems():
        response = urllib2.urlopen(info.url)
        html = response.read()
        source_text = File(info.target).read_all()
        assert_text_equals(html, source_text)


def test_get_stack_parameters():
    conf_path = BEES_ROOT.child('project.yaml')
    conf = yaml.load(File(conf_path).read_all())
    conf['file_path'] = conf_path
    expected = dict(
        KeyName='beesKey',
        BeeCount='5',
        BeesControllerInstanceType='c1.medium',
        TotalConnections='200000',
        SpotPrice=None,
        ConcurrentConnections='1000',
        AppInstanceType='c1.medium',
        AppInstanceCountMin='2',
        AppInstanceCountMax='2',
        AppInstanceCountDesired='2',
        RunTests='true'
    )
    params = stack.get_params(conf)
    for name, info in params.iteritems():
        assert expected[name] == info['value']


def test_parameter_transformation():
    params = dict(
        KeyName='beesKey',
        ChildStackUrl1='{{ url_for("templates/child1.template") }}',
        ChildStackUrl2='{{ url_for("templates/child2.template") }}'
    )
    mapper = {
        'ChildStackUrl1': 'templates/child1.template',
        'ChildStackUrl2': 'templates/child2.template'
    }
    uploaded = {
        'templates/child1.template': {
            'url': 'http://s3host/templates.child1.json'
        },
        'templates/child2.template': {
            'url': 'http://s3host/templates.child2.json'
        }
    }
    config = {}
    transformed = stack._transform_params(config, params, uploaded)
    for key, value in transformed:
        if mapper.get(key, False):
            assert uploaded[mapper[key]]['url'] == value
