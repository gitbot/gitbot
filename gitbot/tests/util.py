import difflib
import json


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
