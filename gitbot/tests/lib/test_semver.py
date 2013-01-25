# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""

from gitbot.lib.semver import Semver
from nose.tools import raises


def test_parts():
    semver = Semver(5)
    assert unicode(semver) == '5.0.0'

    semver = Semver(5, 2)
    assert unicode(semver) == '5.2.0'

    semver = Semver(5, 2, 4)
    assert unicode(semver) == '5.2.4'

    semver = Semver(5, tag='build')
    assert unicode(semver) == '5.0.0+build'

    semver = Semver(5, tag='beta', number=2)
    assert unicode(semver) == '5.0.0-beta.2'

    semver = Semver(5, number=2)
    assert unicode(semver) == '5.0.0'

    semver = Semver(5, revision=2)
    assert unicode(semver) == '5.0.0'

    semver = Semver(5, number=2, revision=2)
    assert unicode(semver) == '5.0.0'

    semver = Semver(5, tag='alpha', number=2, revision=2)
    assert unicode(semver) == '5.0.0-alpha.2.2'


def test_parse():
    semver = Semver()
    semver.parse('5.0.0-alpha.2.2')
    assert semver.major == 5
    assert semver.minor == 0
    assert semver.patch == 0
    assert semver.prefix == '-'
    assert semver.tag == 'alpha'
    assert semver.number == 2
    assert semver.revision == '2'


@raises(ValueError)
def test_bad():
    semver = Semver()
    semver.parse('5.0-alpha.2.2')


def test_next():
    semver = Semver()
    next = semver.next()
    assert str(next) == '0.0.1'


def test_next_beta():
    semver = Semver(tag='beta', number=1)
    next = semver.next()
    assert str(next) == '0.0.0-beta.2'


def test_next_build():
    semver = Semver(tag='build', number=1, revision='a2345')
    next = semver.next()
    assert str(next) == '0.0.0+build.2'
