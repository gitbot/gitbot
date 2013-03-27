# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""

from gitbot.lib.build import Project
from fswrap import File, Folder
import yaml

HERE = File(__file__).parent
CONF = HERE.child_folder('build_data')

BUILD = yaml.load(CONF.child_file('build.yaml').read_all())


class TestProj1(Project):

    @property
    def subdomain(self):
        return self.config.domain


class TestProj2or3(Project):

    @property
    def subdomain(self):
        return self.config.prefix + '.' + self.config.domain


def setup_module():
    pass


def teardown_module():
    pass


def test_load_one_project():
    proj1 = Project.load('proj1', 'build', conf_path=CONF.path)
    assert proj1.config.domain == BUILD['config']['domain']
    assert proj1.subdomain == proj1.config.domain

def test_project_dependencies():
    proj1 = Project.load('proj1', 'build', conf_path=CONF.path)
    proj2 = proj1.depends['proj2']
    assert proj2.config.domain == proj1.config.domain
    assert proj2.subdomain == BUILD['projects']['proj2']['prefix'] + '.' \
                                + proj2.config.domain

def test_config_overrides():
    proj1 = Project.load('proj1', 'build', conf_path=CONF.path)
    proj3 = proj1.depends['proj3']
    assert proj3.config.domain != proj1.config.domain
    assert proj3.subdomain == BUILD['projects']['proj3']['prefix'] + '.' \
                                + proj3.config.domain

def test_source_dir():
    proj2 = Project.load('proj2', 'build', conf_path=CONF.path)
    assert proj2.source_dir == Folder(proj2.source_root).child('proj2')
    assert proj2.build_dir == Folder(proj2.build_root).child('proj2')
    proj2 = Project.load('proj2', 'adhoc', conf_path=CONF.path)
    assert proj2.source_dir == Folder(proj2.source_root).child('projx')
    assert proj2.build_dir == Folder(proj2.build_root).child('projx')


def test_repo():
    proj2 = Project.load('proj2', 'build', conf_path=CONF.path)
    assert proj2.repo == '%s/%s/%s' % (proj2.repo_base, proj2.repo_owner, 'proj2')
    proj2 = Project.load('proj2', 'adhoc', conf_path=CONF.path)
    assert proj2.repo == '%s/%s/%s' % (proj2.repo_base, proj2.repo_owner, 'projy')


def test_multiple_environments_proj1():
    proj1 = Project.load('proj1', 'adhoc', conf_path=CONF.path)
    assert proj1.config.domain == 'proj1adhoc.example.com'
    assert proj1.config.s3bucket == 'proj1adhoc.example.com'
    proj2 = proj1.depends['proj2']
    assert proj2.subdomain == 'second.dev.example.com'
    proj3 = proj1.depends['proj3']
    assert proj3.subdomain == 'third.stage3.example.com'


def test_multiple_environments_proj2():
    proj2 = Project.load('proj2', 'adhoc', conf_path=CONF.path)
    assert proj2.config.domain == 'proj2adhoc.example.com'
    assert proj2.config.s3bucket == 'proj2adhoc.example.com'
    proj1 = proj2.depends['proj1']
    assert proj1.config.domain == 'dev.example.com'

def test_multiple_environments_proj3():
    proj3 = Project.load('proj3', 'adhoc', conf_path=CONF.path)
    assert proj3.config.domain == '3proj3adhoc.example.com'
    assert proj3.config.s3bucket == 'proj3adhoc.example.com'
    proj2 = proj3.depends['proj2']
    assert proj2.subdomain == 'second.dev.example.com'

