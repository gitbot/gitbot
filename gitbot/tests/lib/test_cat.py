# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from fswrap import File, Folder
from gitbot.lib.cat import Concat, FILES, BEGIN_INDENT, END_INDENT, END
from nose.tools import with_setup
import tempfile

TEMP = Folder(tempfile.gettempdir())

START = '''
<!doctype html>
<html>'''
HEAD = '''
<head>
    <style>
        body {
            background-color: @black;
        }
    </style>
    <title>@title</title>
</head>'''
BODY = '''
<body>
    <h1>This is a simple html file</h1>
    <h2>That split up and combined.</h2>
</body>'''
STOP = '''
</html>'''

START_FILE = File(TEMP.child('templates/start_part.html'))
HEAD_FILE = File(TEMP.child('templates/head.html'))
BODY_FILE = File(TEMP.child('templates/body.html'))
STOP_FILE = File(TEMP.child('templates/end_part.html'))
OUT_FILE = File(TEMP.child('output.html'))

HTML = START + HEAD + BODY + STOP


def indent(text):
    result = ''
    for line in text.split('\n'):
        result += '    ' + line + '\n'
    return result.strip('\n')

HTML_INDENTED = START + indent(HEAD) + indent(BODY) + STOP


def setup_module():
    teardown_module()
    START_FILE.parent.make()
    START_FILE.write(START)
    HEAD_FILE.write(HEAD)
    BODY_FILE.write(BODY)
    STOP_FILE.write(STOP)


def teardown_module():
    START_FILE.parent.delete()


def cleanup():
    OUT_FILE.delete()


@with_setup(teardown=cleanup)
def test_cat_all_files():
    Concat(OUT_FILE, base_dir=START_FILE.parent) \
            << FILES(START_FILE) \
            << FILES(HEAD_FILE) \
            << FILES(BODY_FILE) \
            << FILES(STOP_FILE) \
            << END
    actual = OUT_FILE.read_all()
    assert actual == HTML


@with_setup(teardown=cleanup)
def test_cat_all_files_with_indent():
    Concat(OUT_FILE, base_dir=START_FILE.parent) \
            << FILES(START_FILE) \
            << BEGIN_INDENT('    ')\
            << FILES(HEAD_FILE) \
            << FILES(BODY_FILE) \
            << END_INDENT \
            << FILES(STOP_FILE) \
            << END
    actual = OUT_FILE.read_all()
    assert actual.strip() == HTML_INDENTED.strip()


@with_setup(teardown=cleanup)
def test_cat_wrap_text():

    Concat(OUT_FILE, base_dir=START_FILE.parent) \
            << START \
            << BEGIN_INDENT('    ')\
            << FILES(HEAD_FILE) \
            << FILES(BODY_FILE) \
            << END_INDENT \
            << STOP \
            << END
    actual = OUT_FILE.read_all()
    assert actual.strip() == HTML_INDENTED.strip()


@with_setup(teardown=cleanup)
def test_cat_files_with_substituiton():
    replace = {"@black": "#000", "@title": "Cat Rocks"}
    Concat(OUT_FILE, base_dir=START_FILE.parent) \
            << FILES(START_FILE) \
            << FILES(HEAD_FILE) \
            << FILES(BODY_FILE) \
            << FILES(STOP_FILE) \
            << END
    actual = OUT_FILE.read_all()
    expected = HTML
    for key, value in replace.iteritems():
        expected.replace(key, value)
    assert actual == expected


@with_setup(teardown=cleanup)
def test_cat_files_with_local_substituiton():
    replace = {"@black": "#000", "@title": "Cat Rocks"}
    Concat(OUT_FILE, base_dir=START_FILE.parent) \
            << FILES(START_FILE) \
            << FILES(HEAD_FILE, replace=replace) \
            << FILES(BODY_FILE) \
            << FILES(STOP_FILE) \
            << END
    actual = OUT_FILE.read_all()
    expected = HTML
    for key, value in replace.iteritems():
        expected.replace(key, value)
    assert actual == expected
