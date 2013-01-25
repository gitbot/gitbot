# -*- coding: utf-8 -*-
import copy
import re

SEMVER_VERSION = '2.0.0-rc.1'
SEMVER_REGEX = re.compile(
    '^(?P<major>[0-9]+)'
    '\.(?P<minor>[0-9]+)'
    '\.(?P<patch>[0-9]+)'
    '('
        '(?P<prefix>\+|\-)'
        '(?P<tag>[0-9A-Za-z]+)'
        '('
            '\.(?P<number>[0-9]+)'
            '('
                '\.(?P<revision>[0-9a-z]+)'
            ')*'
        ')*'
    ')*?$')


class Semver(object):

    def __init__(self, major=0,
                        minor=0,
                        patch=0,
                        tag=None,
                        number=None,
                        revision=None,
                        prefix=None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.tag = tag
        self.prefix = prefix or '+' if tag == 'build' else '-'
        self.number = number
        self.revision = revision

    @property
    def has_tag(self):
        return self.tag is not None

    @property
    def has_number(self):
        return self.has_tag and self.number is not None

    @property
    def has_revision(self):
        return self.has_number and self.revision is not None

    def next(self, revision=None):
        copied = copy.copy(self)
        if not copied.has_tag:
            copied.patch += 1
        else:
            number = copied.number or 0
            copied.number = number + 1
            copied.revision = revision

        return copied

    @property
    def version(self):
        def _make_revision():
            return '.%s' % self.revision if self.has_revision else ''

        def _make_number():
            number = '.%d' % self.number if self.has_number else ''
            return number + _make_revision()

        def _make_tag():
            tag = '%s%s' % (self.prefix, self.tag) if self.has_tag else ''
            return tag + _make_number()

        version = '%d.%d.%d' % (self.major, self.minor, self.patch)
        version += _make_tag()
        return version

    def parse(self, version):
        match = SEMVER_REGEX.match(version)
        if match is None:
            raise ValueError(
                '%s is not a valid Semantic Version string' % version)
        values = match.groupdict()
        self.major = int(values.get('major', 0))
        self.minor = int(values.get('minor', 0))
        self.patch = int(values.get('patch', 0))
        self.prefix = values.get('prefix', '-')
        self.tag = values.get('tag', None)
        self.number = int(values.get('number') or 0)
        self.revision = values.get('revision', None)

    @classmethod
    def from_string(cls, version):
        semver = cls()
        semver.parse(version)
        return semver

    def __str__(self):
        return self.version

    def __repr__(self):
        return super(Semver, self).__repr__() + '[%s]' % unicode(self)
