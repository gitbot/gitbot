# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from fswrap import File
from gitbot import stack

from nose.tools import nottest
import urllib2
import yaml


TEST_ROOT = File(__file__).parent
MULTI_ROOT = TEST_ROOT.child_folder('multi')
SOURCE_ROOT = MULTI_ROOT.child_folder('source')
SCRIPT_ROOT = MULTI_ROOT.child_folder('scripts')
TEMP = MULTI_ROOT.child_folder('tmp')

conf_path = MULTI_ROOT.child('gitbot.yaml')
settings = yaml.load(File(conf_path).read_all())
settings['file_path'] = conf_path


def teardown():
    TEMP.delete()


def test_validate():
    stack.validate_stack(settings)


# Marked as nottest to prevent this from running during every test run.
@nottest
def test_publish_stack():
    try:
        stack.publish_stack(settings)
        out = stack.get_outputs(settings, wait=True)
        url = out['WebsiteURL']
        response = urllib2.urlopen(url)
        html = response.read()
        assert html == 'Hello, World!'
    finally:
        stack.delete_stack(settings, wait=True)
