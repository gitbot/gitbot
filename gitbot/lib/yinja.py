'''
Use jinja2 to templatize a yaml document.
'''
from commando.conf import ConfigDict
from fswrap import File
from jinja2 import Environment
import yaml

def _get_jinja2_env(jinja_env):
    defaults = {
        'env': { 'trim_blocks': True },
        'globals' : {},
        'filters' : {},
        'tests' : {}
    }
    defaults.update(jinja_env or {})
    env = Environment(**defaults['env'])
    env.globals.update(defaults['globals'])
    env.filters.update(defaults['filters'])
    env.tests.update(defaults['tests'])
    return env

def transform(path, result_path, context=None, jinja_env=None):
    """
    Loads a yaml document from the given `path` and processes
    it as a jinja2 template.
    `result_path` The target file path for writing the output.
    `context` is passed to the template processor as data.
    `jinja_env` can contain custom extensions, filters and functions.
    See jinja2 documentation on the `environment` variable.
    """
    f = File(path)
    env = _get_jinja2_env(jinja_env)
    source = f.read_all() if f.exists else path
    t = env.from_string(source)
    result = t.render(context or dict())
    File(result_path).write(result)
    return result_path


def load(path, context=None, jinja_env=None, patchable=True):
    """
    Loads a yaml document from the given `path` and processes
    it as a jinja2 template.
    `context` is passed to the template processor as data.
    `jinja_env` can contain custom extensions, filters and functions.
    See jinja2 documentation on the `environment` variable.
    `patchable` if this is True, any valid yaml file specified in the
    `patches` key at the document root is taken as base and the values in
    this document are patched on top of it.
    """
    f = File(path)
    env = _get_jinja2_env(jinja_env)
    def read(text):
        if isinstance(text, File):
            text = text.read_all()
        t = env.from_string(text)
        data = yaml.load(t.render(context or dict()))
        conf = ConfigDict(data)
        if 'patches' in conf and patchable:
            leaf = conf
            parent = leaf['patches']
            del leaf['patches']
            parent = File(f.parent.child(parent))
            conf = read(parent)
            conf.patch(leaf)

        return conf
    return read(f if f.exists else path)
