import difflib
from itertools import izip
import json
import yaml


def assert_dotted_key_matches(key, wish, reality):
    parts = key.split('.')
    expected = reduce(lambda d, part: d[part], parts, wish)
    actual = reduce(lambda d, part: d[part], parts, reality)
    assert expected == actual


def assert_text_equals(first, second, msg=None):
    """Assert that two multi-line strings are equal.

    If they aren't, show a nice diff.

    """
    assert isinstance(first, (str, unicode)), 'First argument is not a string'
    assert isinstance(second, (str, unicode)), 'Second argument is not a string'

    if first != second:
        diffs = difflib.ndiff(first.splitlines(True), second.splitlines(True))
        diffs = [line for line in diffs if line[0] in ('+', '-', '?')]
        message = ''.join(diffs)
        if msg:
            message += " : " + msg
        assert False, "Multi-line strings are unequal:\n" + message


def assert_json_equals(actual, expected, msg=None):
    assert_text_equals(
        json.dumps(json.loads(actual), sort_keys=True),
        json.dumps(json.loads(expected), sort_keys=True))


def assert_yaml_equals(actual, expected, msg=None):
    assert_text_equals(
        yaml.dump(actual, default_flow_style=True),
        yaml.dump(expected, default_flow_style=True))


def compare(wish, reality):
    if isinstance(wish, (list, tuple, set)):
        return seq_compare(wish, reality)
    if isinstance(wish, dict):
        return dict_compare(wish, reality)
    return wish == reality


def seq_compare(expected, actual):
    for wish, reality in izip(expected, actual):
        if not compare(wish, reality):
            print 'diff found. [%s] is different from [%s]' % (wish, reality)
            return False
    return True


def dict_compare(wish, reality):
    for key, value in wish.iteritems():
        expected = value
        actual = reality[key]
        if not compare(expected, actual):
            print 'diff found. [%s] is different from [%s]' % (wish, reality)
            return False
    return True
