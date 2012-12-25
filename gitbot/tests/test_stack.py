# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from fswrap import File
from gitbot import stack

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


def test_validate():
    conf_path = BEES_ROOT.child('project.yaml')
    conf = yaml.load(File(conf_path).read_all())
    conf['file_path'] = conf_path
    stack.validate_stack(conf)


def test_publish_stack():
    conf_path = BEES_ROOT.child('project.yaml')
    conf = yaml.load(File(conf_path).read_all())
    conf['file_path'] = conf_path
    published = stack.publish_stack(conf)
    for rpath, info in published.iteritems():
        print info.url
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
