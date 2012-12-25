# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from fswrap import File
from util import assert_text_equals, assert_json_equals

from gitbot import generator

import yaml


TEST_ROOT = File(__file__).parent
BEES_ROOT = TEST_ROOT.child_folder('bees')
SOURCE_ROOT = BEES_ROOT.child_folder('source')
SCRIPT_ROOT = BEES_ROOT.child_folder('scripts')
TEMP = BEES_ROOT.child_folder('tmp')


def teardown():
    TEMP.delete()


def test_bees_template():
    expected = File(BEES_ROOT.child('expected/bees_with_guns.json')).read_all()
    actual = generator.render('cfn.template', search_paths=[
                            SOURCE_ROOT.path, SCRIPT_ROOT.path])
    assert_text_equals(actual, expected)


def test_bees_project():
    expected = File(BEES_ROOT.child('expected/bees_with_guns.json')).read_all()
    conf_path = BEES_ROOT.child('project.yaml')
    conf = yaml.load(File(conf_path).read_all())
    conf['file_path'] = conf_path
    generator.render_project(conf)
    actual = File(TEMP.child('cfn.template')).read_all()
    assert_text_equals(actual, expected)


def test_bees_template_with_context():
    expected = File(BEES_ROOT.child('expected/bees_with_guns.json')).read_all()
    context = yaml.load(File(SOURCE_ROOT.child('cfn.context.yaml')).read_all())
    actual = generator.render('cfn.context', search_paths=[
                            SOURCE_ROOT.path, SCRIPT_ROOT.path],
                            context_data=context)
    assert_json_equals(actual, expected)
