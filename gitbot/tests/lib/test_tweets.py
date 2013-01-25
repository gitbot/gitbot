# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from fswrap import File
from gitbot.lib.tweets import Tweeter, twokenize
from util import assert_yaml_equals
import yaml


TEST_ACCOUNT = 'rmantester'
JUNK_ACCOUNT = 'r1m1a1n1t1e1s1t1e1r1'

FAVES = File(File(__file__).parent.child('favorite_tweets.yaml'))
FAVORITES = yaml.load(FAVES.read_all())


def test_lookup_user():
    tweeter = Tweeter(TEST_ACCOUNT)
    assert tweeter.lookup_user()
    tweeter = Tweeter(JUNK_ACCOUNT)
    assert not tweeter.lookup_user()


def test_twokenize():
    tweet = 'An article on the @flowplayer secure plugin based on my code' + \
            ' - http://t.co/jkhOASZY #php #js'
    expected = [
        {'type': 'text', 'value': 'An article on the'},
        {'type': 'user', 'value': '@flowplayer'},
        {'type': 'text', 'value': 'secure plugin based on my code -'},
        {'type': 'link', 'value': 'http://t.co/jkhOASZY'},
        {'type': 'hashtag', 'value': '#php'},
        {'type': 'hashtag', 'value': '#js'}
    ]
    actual = twokenize(tweet)
    assert expected == actual


def test_favorites():
    tweeter = Tweeter(TEST_ACCOUNT)
    faves = tweeter.get_favorites()
    assert_yaml_equals(faves, FAVORITES)
