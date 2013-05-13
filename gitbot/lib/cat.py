from fnmatch import fnmatch
from fswrap import File, Folder
from commando.util import getLoggerWithConsoleHandler

logger = getLoggerWithConsoleHandler('gitbot.cat')


class FILES(object):

    def __init__(self, patterns=None, replace=None):
        if not patterns:
            self.patterns = ["*"]
        elif not isinstance(patterns, (list)):
            self.patterns = [patterns]
        self.patterns = [unicode(pattern) for pattern in self.patterns]
        self.replace = replace or {}

    def walk(self, base_dir):
        return (f for f in Folder(base_dir).walker.walk_files()
                        if any(fnmatch(f.path, pattern)
                            for pattern in self.patterns))

    def walk_lines(self, base_dir):
        for file_name in self.walk(base_dir):
            with open(str(file_name), 'r') as f:
                for line in f:
                    yield line


class END(object):
    pass


class BEGIN_INDENT(object):
    def __init__(self, indent=' '):
        self.indent = indent


class END_INDENT(object):
    pass


class Concat(object):

    def __init__(self, out_file,
                    base_dir='.',
                    overwrite=True,
                    replace=None):
        if not replace:
            self.replace = {}
        elif not isinstance(replace, dict):
            raise Exception("vars must be a dictionary")
        else:
            self.replace = replace
        self.out_file = File(out_file)
        self.fp = None
        self.indent = ''
        if overwrite:
            self.out_file.delete()
        self.out_file.parent.make()
        self.base_dir = Folder(base_dir)

    def open(self, mode='a'):
        self.fp = open(self.out_file.path, mode)
        return self

    def __lshift__(self, stream):
        if not self.fp:
            self.open()
        if isinstance(stream, FILES):
            self.concat_files(stream, self.indent)
        elif isinstance(stream, BEGIN_INDENT):
            self.indent = stream.indent
        elif stream == END_INDENT or isinstance(stream, END_INDENT):
            self.indent = ''
        elif stream == END or isinstance(stream, END):
            self.indent = ''
            self.close()
        else:
            self.concat_string(unicode(stream), self.indent)
        return self

    def concat_files(self, files, indent=''):
        for line in files.walk_lines(self.base_dir):
            self.write(indent, line)

    def concat_string(self, text, indent=''):
        for line in text.splitlines(True):
            self.write(indent, line)

    def write(self, indent, line):
        text = indent + line
        for key, value in self.replace.iteritems():
            text = text.replace(key, value)
        self.fp.write(text)

    def close(self):
        if self.fp:
            self.fp.close()
