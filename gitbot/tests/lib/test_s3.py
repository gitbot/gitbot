# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""

from fswrap import File, Folder
from gitbot.lib.s3 import Bucket
from nose.tools import with_setup, nottest
import urllib2
import time

data_folder = File(__file__).parent.child_folder('data')
_bucket_name = None


def teardown_module():
    cleanup()


@nottest
def bucket_name():
    global _bucket_name
    _bucket_name = 'lakshmivyas.rman.s3.testbucket' + str(hash(time.time()))
    return _bucket_name


@nottest
def cleanup():
    if not _bucket_name:
        return
    bucket = Bucket(_bucket_name)
    try:
        bucket.connect()
        if not bucket.bucket:
            return
        for key in bucket.bucket.list():
            key.delete()
        bucket.delete()
    except:
        pass
    data_folder.delete()


@nottest
def new_bucket():
    return Bucket(bucket_name())


@with_setup(cleanup)
def test_website():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    content = '<h1>A new html file on S3</h1>'
    data_folder.make()
    f = File(data_folder.child('index.html'))
    f.write(content)
    home = Folder('/home')
    bucket.add_file(f, target_folder=home.name)
    url = bucket.get_url()
    response = urllib2.urlopen(url + home.path)
    html = response.read()
    assert html == content

@with_setup(cleanup)
def test_signed_url():
    bucket = new_bucket()
    bucket.make()
    content = '<h1>A new html file on S3</h1>'
    data_folder.make()
    f = File(data_folder.child('index.html'))
    f.write(content)
    home = Folder('/home')
    full_path = bucket.add_file(f, target_folder=home.name)
    url = bucket.get_signed_url(full_path)
    response = urllib2.urlopen(url)
    html = response.read()
    assert html == content


@with_setup(cleanup)
def test_etag():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    content = '<h1>A new html file on S3</h1>'
    data_folder.make()
    f = File(data_folder.child('index.html'))
    f.write(content)
    home = Folder('/home')
    bucket.add_file(f, target_folder=home.name)
    key = bucket.bucket.get_key('home/index.html')
    assert bucket.check_etag(key, f)


@with_setup(cleanup)
def test_mime_type():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    content = '<h1>A new html file on S3</h1>'
    data_folder.make()
    f = File(data_folder.child('index.html'))
    f.write(content)
    home = Folder('/home')
    bucket.add_file(f, target_folder=home.name)
    key = bucket.bucket.get_key('home/index.html')
    assert key.content_type == 'text/html'


@nottest
def upload_folder(bucket, skip_css=False):
    data_folder.make()
    html_content = '<h1>A new html file on S3</h1>'
    css_content = 'body:after { content: "new css"; }'
    js_content = 'function new_js() { document.write("somethign fancy"); }'
    home = File(data_folder.child_folder('home').child('index.html'))
    home.parent.make()
    home.write(html_content)
    if not skip_css:
        css = File(data_folder.child_folder('media/css').child('site.css'))
        css.parent.make()
        css.write(css_content)
    js = File(data_folder.child_folder('media/js').child('site.js'))
    js.parent.make()
    js.write(js_content)
    bucket.add_folder(data_folder)
    return (html_content, css_content, js_content)


@with_setup(cleanup)
def test_add_new_folder():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    url = bucket.get_url()
    html_content, css_content, js_content = upload_folder(bucket)
    uploaded = []
    for key in bucket.bucket.list():
        uploaded.append(key.name)
    assert len(uploaded) == 3
    assert 'home/index.html' in uploaded
    assert 'media/css/site.css' in uploaded
    assert 'media/js/site.js' in uploaded
    response = urllib2.urlopen(url + '/home')
    html = response.read()
    assert html == html_content
    response = urllib2.urlopen(url + '/media/css/site.css')
    css = response.read()
    assert css == css_content
    response = urllib2.urlopen(url + '/media/js/site.js')
    js = response.read()
    assert js == js_content


@with_setup(cleanup)
def test_check_delete_overwrite():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    upload_folder(bucket)
    data_folder.delete()
    html_content, \
        css_content, \
        js_content = upload_folder(bucket, skip_css=True)
    uploaded = []
    for key in bucket.bucket.list():
        uploaded.append(key.name)
    assert len(uploaded) == 2
    assert 'home/index.html' in uploaded
    assert 'media/js/site.js' in uploaded
