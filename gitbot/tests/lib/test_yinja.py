from commando.conf import ConfigDict
from fswrap import File, Folder
from functools import reduce
from gitbot.lib.yinja import load
import tempfile
from util import compare, assert_dotted_key_matches
import yaml

TEMP = Folder(tempfile.gettempdir())
HERE = File(__file__).parent

def test_context():
    context = {
        "version": "5.0.1",
        "project": "yinja"
    }
    yaml_text = \
'''
yinja:
    text: project
    text2: version
    url: http://{{ project }}.com/v{{ version }}
'''
    result = load(yaml_text, context, patchable=False)
    result = result['yinja']
    assert result['text'] == 'project'
    assert result['text2'] == 'version'
    assert result['url'] == 'http://yinja.com/v5.0.1'


def test_function():
    
    from jinja2 import contextfunction

    @contextfunction
    def url(context, base):
        return base + '/' + context['project'] + '/' + context['version'] + '/'

    context = {
            "version": "5.0.1",
            "project": "yinja"
        }
    
    yaml_text = \
'''
yinja:
    text: project
    text2: version
    url: {{ url ('http://example.com') }}
'''
    env = dict(globals=dict(url=url))
    result = load(yaml_text, context, jinja_env=env, patchable=False)
    result = result['yinja']
    assert result['text'] == 'project'
    assert result['text2'] == 'version'
    assert result['url'] == 'http://example.com/yinja/5.0.1/'



def test_filter():
    from jinja2 import contextfilter

    @contextfilter
    def url(context, base):
        return base + '/' + context['project'] + '/' + context['version'] + '/'

    context = {
            "version": "5.0.1",
            "project": "yinja"
        }
    
    yaml_text = \
'''
yinja:
    text: project
    text2: version
    url: {{ 'http://example.com'|url }}
'''
    env = dict(filters=dict(url=url))
    result = load(yaml_text, context, jinja_env=env, patchable=False)
    result = result['yinja']
    assert result['text'] == 'project'
    assert result['text2'] == 'version'
    assert result['url'] == 'http://example.com/yinja/5.0.1/'    

def test_test():
    from jinja2 import contextfilter

    @contextfilter
    def url(context, base):
        return base + '/' + context['project'] + '/' + context['version'] + '/'

    def is_fiveOrAbove(val):
        return int(val.split('.')[0]) >= 5


    context = {
            "version": "5.0.1",
            "project": "yinja"
        }
    
    yaml_text = \
'''
yinja:
    text: project
    text2: version
    url: {{ 'http://example.com'|url if version is above5 else 'http://example.com' }}
'''
    env = dict(filters=dict(url=url), tests=dict(above5=is_fiveOrAbove))
    result = load(yaml_text, context, jinja_env=env, patchable=False)
    result = result['yinja']
    assert result['text'] == 'project'
    assert result['text2'] == 'version'
    assert result['url'] == 'http://example.com/yinja/5.0.1/'        

    context['version'] = '3.0.0'
    result = load(yaml_text, context, jinja_env=env, patchable=False)
    result = result['yinja']
    assert result['text'] == 'project'
    assert result['text2'] == 'version'
    assert result['url'] == 'http://example.com'        

p0 = HERE.child_file('p0.yaml')
p1 = HERE.child_file('p1.yaml')
p2 = HERE.child_file('p2.yaml')
p0d = yaml.load(p0.read_all())
p1d = yaml.load(p1.read_all())
p2d = yaml.load(p2.read_all())

def test_load():
    assert(compare(p0d, load(p0.path)))

def test_patch_level1():
    p1a = load(p1.path)
    assert 'patches' not in p1a
    assert_dotted_key_matches('config.env', p1d, p1a)
    assert_dotted_key_matches('config.branch', p1d, p1a)
    assert_dotted_key_matches('projects.comp1.version_type', p1d, p1a)
    assert_dotted_key_matches('projects.comp2.version_type', p1d, p1a)
    assert_dotted_key_matches('projects.comp3.version_type', p0d, p1a)
    

def test_patch_level2():
    p2a = load(p2.path)
    assert 'patches' not in p2a
    assert_dotted_key_matches('config.env', p2d, p2a)
    assert_dotted_key_matches('config.branch', p2d, p2a)
    assert_dotted_key_matches('projects.comp1.version_type', p1d, p2a)
    assert_dotted_key_matches('projects.comp2.version_type', p2d, p2a)
    assert_dotted_key_matches('projects.comp3.version_type', p2d, p2a)

def test_patch_level2_no_patching():
    p2a = load(p2.path, patchable=False)
    assert 'patches' in p2a
    assert_dotted_key_matches('config.env', p2d, p2a)
    assert_dotted_key_matches('config.branch', p2d, p2a)
    assert_dotted_key_matches('projects.comp2.version_type', p2d, p2a)
    assert_dotted_key_matches('projects.comp3.version_type', p2d, p2a)
    assert_dotted_key_matches('projects.comp1.version_type', ConfigDict(), p2a)
    

