from commando.conf import AutoProp, ConfigDict
import fnmatch
from fswrap import File, Folder
from gitbot import splitter
from jinja2 import (contextfunction, contextfilter,
                    Environment, FileSystemLoader, Markup)
import json
import os


def extappend(l, stuff):
    if isinstance(stuff, basestring):
        stuff = [stuff]
    try:
        l.extend(stuff)
    except TypeError:
        l.append(stuff)


class Config(AutoProp):

    def __init__(self, data=None):
        if isinstance(data, Config):
            self.data = data.data
        else:
            # Assume dict
            self.data = ConfigDict(data)
        self.default_search_paths = [os.getcwd()]

    def flatten(self):
        return dict(self.data)

    @AutoProp.default
    def publish(self):
        return self.data.get('publish', None)

    @AutoProp.default
    def source_dir(self):
        try:
            default_source = File(self.data.file_path).parent.path
        except AttributeError:
            default_source = os.getcwd()

        source = self.data.get('source_dir', default_source)
        return Folder(default_source).child_folder(source)

    @AutoProp.default
    def source_patterns(self):
        patterns = []
        config_patterns = self.data.get('source_patterns', ['*.json'])
        extappend(patterns, config_patterns)
        return patterns

    @AutoProp.default
    def output_dir(self):
        out = self.data.get('output_dir', 'out')
        return Folder(self.source_dir).parent.child_folder(out)

    @AutoProp.default
    def search_paths(self):
        paths = []
        paths.extend(self.default_search_paths)
        paths.append(self.source_dir.path)
        config_paths = []
        extappend(config_paths, self.data.get('search_paths', []))
        config_paths = [Folder(self.source_dir).parent.child(path)
                            for path in config_paths]
        extappend(paths, config_paths)
        return list(set(paths))

    @AutoProp.default
    def context(self):
        return self.data.get('context')

    @AutoProp.default
    def region(self):
        return self.data.get('region', 'us-east-1')


@contextfunction
def contents(context, file_name, append_line_break=True):
    template = context.environment.get_template(file_name)
    txt = template.render(context)
    return splitter.split(txt, append_line_break)


@contextfilter
def json_filter(context, value):
    result = json.dumps(value, indent=4, separators=(',', ': '))

    if context.eval_ctx.autoescape:
        result = Markup(result)

    return result


def _setup_env(config):
    loader = FileSystemLoader(config.search_paths)
    env = Environment(loader=loader, trim_blocks=False)
    env.globals['contents'] = contents
    env.filters['json'] = json_filter
    return env


def _render(env, file_name, config):
    template = env.get_template(file_name)
    context = template.new_context(config.context)
    return template.render(context).lstrip()


def render(file_name, search_paths, context_data=None):
    config = Config({})
    config.search_paths = search_paths
    config.context = context_data
    env = _setup_env(config)
    return _render(env, file_name, config)


def get_source_files(config):
    files = {}
    with config.source_dir.walker as walker:
        @walker.file_visitor
        def visit_file(afile):
            for pattern in config.source_patterns:
                if fnmatch.fnmatch(afile.name, pattern):
                    rpath = afile.get_relative_path(config.source_dir)
                    target = File(config.output_dir.child(rpath))
                    files[rpath] = (afile, target)
    return files


def render_source_file(env, config, source, target):
    target.parent.make()
    txt = _render(env, source.name, config)
    target.write(txt)


def render_project(config):
    config = Config(config)
    env = _setup_env(config)
    files = get_source_files(config)
    out = config.output_dir
    out.make()
    for rpath, (source, target) in files.iteritems():
        render_source_file(env, config, source, target)
    return config, env, files
