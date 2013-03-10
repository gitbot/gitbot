# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""

from gitbot.lib.git import GitException, Tree
from nose.tools import with_setup, raises
from fswrap import File, Folder
import tempfile

TEMP = tempfile.gettempdir()
GIT_REMOTE_DIR = Folder(TEMP).child_folder('repos/remote')
GIT_REMOTE = 'file:///' + GIT_REMOTE_DIR.path
GIT_TEST_DIR1 = Folder(TEMP).parent.child_folder('repos/local1')
GIT_TEST_DIR2 = Folder(TEMP).parent.child_folder('repos/local2')

HTML = '<h1>This is a simple html file</h1>'
CSS = 'body { background-color: black; }'
JS = '$(function(){ alert("All done."); });'

HTML_FILE = 'home/index.html'
CSS_FILE = 'media/css/site.css'
JS_FILE = 'media/js/site.js'

remote_tree = None
local_repo1 = None
local_repo2 = None


def setup_module():
    teardown_module()
    assert not GIT_REMOTE_DIR.exists
    assert not GIT_TEST_DIR1.exists
    assert not GIT_TEST_DIR2.exists
    global remote_tree
    global local_repo1
    global local_repo2

    print 'setting up remote'
    GIT_REMOTE_DIR.make()
    remote_tree = Tree(GIT_REMOTE_DIR)
    remote_tree.make(bare=True)

    print 'setting up local 1'

    GIT_TEST_DIR1.make()
    home = File(GIT_TEST_DIR1.child(HTML_FILE))
    home.parent.make()
    home.write(HTML)

    css = File(GIT_TEST_DIR1.child(CSS_FILE))
    css.parent.make()
    css.write(CSS)

    js = File(GIT_TEST_DIR1.child(JS_FILE))
    js.parent.make()
    js.write(JS)

    local_repo1 = Tree(GIT_TEST_DIR1, GIT_REMOTE)
    local_repo1.make()
    local_repo1.add_remote()
    local_repo1.commit("Initial commit")
    local_repo1.push(set_upstream=True)

    local_repo2 = Tree(GIT_TEST_DIR2, GIT_REMOTE)
    local_repo2.clone()


def teardown_module():
    GIT_REMOTE_DIR.delete()
    GIT_TEST_DIR1.delete()
    GIT_TEST_DIR2.delete()
    GIT_REMOTE_DIR.parent.delete()



def reset():
    local_repo1.reset()
    local_repo2.reset()


def clean():
    setup_module()


@with_setup(teardown=clean)
def test_fetch():
    new_css = 'body { background-color: white; }'
    new_branch = 'new_css'
    local_repo1.new_branch(new_branch)
    revision = None
    with local_repo1.branch(new_branch):
        File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
        local_repo1.commit('Changed background-color')
        local_repo1.push()
        revision = local_repo1.get_revision()
        modified = local_repo1.get_last_committed()
    local_repo2.fetch()
    with local_repo2.branch(new_branch):
        css = File(GIT_TEST_DIR2.child(CSS_FILE)).read_all()
        assert css == new_css
        assert local_repo2.get_revision() == revision
        assert local_repo2.get_last_committed() == modified


@with_setup(teardown=clean)
def test_fetch_ref():
    new_css = 'body { background-color: white; }'
    new_branch = 'new_css'
    local_repo1.new_branch(new_branch)
    revision = None
    with local_repo1.branch(new_branch):
        File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
        local_repo1.commit('Changed background-color')
        local_repo1.push()

        revision = local_repo1.get_revision(short=False)
        modified = local_repo1.get_last_committed()
        local_repo1.make_ref('refs/test/testref', revision)
        local_repo1.push(ref='refs/test/testref')
    GIT_TEST_DIR2.delete()
    local_repo2 = Tree(GIT_TEST_DIR2, GIT_REMOTE)
    local_repo2.fetch_ref('refs/test/testref', 'localrev')
    css = File(GIT_TEST_DIR2.child(CSS_FILE)).read_all()
    assert css == new_css
    assert local_repo2.get_revision(short=False) == revision
    assert local_repo2.get_last_committed() == modified

@with_setup(teardown=clean)
def test_merge():
    new_css = 'body { background-color: white; }'
    new_branch = 'new_css'
    local_repo1.new_branch(new_branch)
    revision = None
    with local_repo1.branch(new_branch):
        File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
        local_repo1.commit('Changed background-color')
        local_repo1.push()
        revision = local_repo1.get_revision()
        modified = local_repo1.get_last_committed()
    local_repo2.fetch()
    local_repo2.merge('origin/' + new_branch)
    css = File(GIT_TEST_DIR2.child(CSS_FILE)).read_all()
    assert css == new_css
    assert local_repo2.get_revision() == revision
    assert local_repo2.get_last_committed() == modified

@with_setup(teardown=clean)
def test_merge_noff():
    new_css = 'body { background-color: white; }'
    new_branch = 'new_css'
    local_repo1.new_branch(new_branch)
    with local_repo1.branch(new_branch):
        File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
        local_repo1.commit('Changed background-color')
        local_repo1.push()
    local_repo2.new_branch(new_branch)
    new_js = '$(function(){ console.log("All done."); });'
    with local_repo2.branch(new_branch):
        File(GIT_TEST_DIR2.child(JS_FILE)).write(new_js)
        local_repo2.commit('Removed debug alert')
    local_repo2.fetch()
    with local_repo2.branch(new_branch):
        local_repo2.merge('origin/' + new_branch, ff_only=False)
        css = File(GIT_TEST_DIR2.child(CSS_FILE)).read_all()
        assert css == new_css
        js = File(GIT_TEST_DIR2.child(JS_FILE)).read_all()
        assert js == new_js

@with_setup(teardown=clean)
@raises(GitException)
def test_merge_noff_fail():
    new_css = 'body { background-color: white; }'
    new_branch = 'new_css'
    local_repo1.new_branch(new_branch)
    with local_repo1.branch(new_branch):
        File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
        local_repo1.commit('Changed background-color')
        local_repo1.push()
    local_repo2.new_branch(new_branch)
    new_css2 = 'body.page { background-color: black; }'
    with local_repo2.branch(new_branch):
        File(GIT_TEST_DIR2.child(CSS_FILE)).write(new_css2)
        local_repo2.commit('Changed background-color')
    local_repo2.fetch()
    with local_repo2.branch(new_branch):
        local_repo2.merge('origin/' + new_branch, ff_only=False)

@with_setup(teardown=clean)
def test_merge_ff():
    new_css = 'body { background-color: white; }'
    new_branch = 'new_css'
    local_repo1.new_branch(new_branch)
    with local_repo1.branch(new_branch):
        File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
        local_repo1.commit('Changed background-color')
        local_repo1.push()
    local_repo2.fetch()
    local_repo2.new_branch(new_branch)
    new_js = '$(function(){ console.log("All done."); });'
    with local_repo2.branch(new_branch):
        local_repo2.merge('origin/' + new_branch, ff_only=True)
        css = File(GIT_TEST_DIR2.child(CSS_FILE)).read_all()
        assert css == new_css
        File(GIT_TEST_DIR2.child(JS_FILE)).write(new_js)
        local_repo2.commit('Removed debug alert')
        local_repo2.push()
    local_repo1.fetch()
    with local_repo1.branch(new_branch):
        local_repo1.merge('origin/' + new_branch, ff_only=True)
        js = File(GIT_TEST_DIR1.child(JS_FILE)).read_all()
        assert js == new_js


@with_setup(teardown=clean)
@raises(GitException)
def test_merge_ff_fail():
    new_css = 'body { background-color: white; }'
    new_branch = 'new_css'
    local_repo1.new_branch(new_branch)
    with local_repo1.branch(new_branch):
        File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
        local_repo1.commit('Changed background-color')
        local_repo1.push()
    local_repo2.new_branch(new_branch)
    new_css2 = 'body.page { background-color: black; }'
    with local_repo2.branch(new_branch):
        File(GIT_TEST_DIR2.child(CSS_FILE)).write(new_css2)
        local_repo2.commit('Changed background-color')
    local_repo2.fetch()
    with local_repo2.branch(new_branch):
        local_repo2.merge('origin/' + new_branch, ff_only=True)

@with_setup(teardown=clean)
def test_get_revision_remote():
    test_tree = Tree(GIT_TEST_DIR2, GIT_REMOTE)
    remote_rev = test_tree.get_revision_remote()
    local_rev = local_repo1.get_revision(short=False)
    assert remote_rev == local_rev


@with_setup(teardown=reset)
def test_has_changes_local_uncommitted():
    assert not local_repo1.has_changes()
    new_css = 'body { background-color: gray; }'
    File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
    assert local_repo1.has_changes()


@with_setup(teardown=clean)
def test_has_changes_local_committed():
    assert not local_repo1.has_changes()
    new_css = 'body { background-color: gray; }'
    File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
    local_repo1.commit('Changed background to gray')
    assert local_repo1.has_changes()


@with_setup(teardown=clean)
def test_has_changes_remote():
    assert not local_repo1.has_changes()
    assert not local_repo2.has_changes()
    new_css = 'body { background-color: gray; }'
    File(GIT_TEST_DIR1.child(CSS_FILE)).write(new_css)
    local_repo1.commit('Changed background to gray')
    local_repo1.push()
    assert local_repo2.has_changes()


@with_setup(teardown=reset)
def test_tag_add_remove(message=None):
    tag = '0.1'
    assert not local_repo2.tagger.check(tag)
    local_repo2.tagger.add(tag)
    assert local_repo2.tagger.check(tag)
    local_repo2.tagger.remove(tag)
    assert not local_repo2.tagger.check(tag)


@with_setup(teardown=clean)
def test_tag_push(message=None):
    tag = '0.1'
    local_repo2.tagger.add(tag, push=True)
    revision2 = local_repo2.get_revision(tag)
    local_repo1.fetch()
    assert local_repo1.tagger.check(tag)
    assert revision2 == local_repo1.get_revision(tag)
    local_repo1.tagger.remove(tag, push=True)
    assert not local_repo1.tagger.check(tag)
    local_repo2.tagger.sync()
    assert not local_repo2.tagger.check(tag)


def test_tag_generator():
    yield test_tag_add_remove
    yield test_tag_push

    yield test_tag_add_remove, 'Annotation1'
    yield test_tag_push, 'Annotation1'
