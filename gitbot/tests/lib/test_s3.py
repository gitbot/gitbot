# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""

from fswrap import File, Folder
from gitbot.lib.s3 import Bucket
from nose.tools import with_setup, nottest
import requests

from datetime import datetime, timedelta
import urllib2
import time

data_folder = File(__file__).parent.child_folder('data')
_bucket_name = None


def teardown_module():
    cleanup()


@nottest
def bucket_name():
    global _bucket_name
    _bucket_name = 'lakshmivyas.gitbot.s3.testbucket' + str(hash(time.time()))
    return _bucket_name


@nottest
def cleanup():
    if not _bucket_name:
        return
    bucket = Bucket(_bucket_name)
    try:
        bucket.connect()
        bucket.delete(recurse=True)
    except:
        pass
    data_folder.delete()

@nottest
def get_expires(timeout=60):
    expires = datetime.utcnow() + timedelta(minutes=timeout)
    return expires.strftime("%a, %d %b %Y %H:%M:%S GMT")


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


def assert_headers_present(url, headers):
    res = requests.head(url)
    errors = []
    for meta_name, value in headers.items():
        name = meta_name.lower()
        if not name in res.headers:
            errors.append("Header [{0}] does not exist.".format(name))
        if res.headers[name] != value:
            errors.append("Header {0} does not match {1} != {2}".format(
                name,
                res.headers[meta_name.lower()],
                value
            ))
    assert len(errors) == 0, unicode(errors)

@with_setup(cleanup)
def test_expires():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    content = '<h1>A new html file on S3</h1>'
    data_folder.make()
    f = File(data_folder.child('index.html'))
    f.write(content)
    home = Folder('/home')
    headers = {"Expires":get_expires()}
    bucket.add_file(f, target_folder=home.name, headers=headers)
    assert_headers_present(bucket.get_url() + '/home/index.html', headers)

@with_setup(cleanup)
def test_expires_on_update():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    content = '<h1>A new html file on S3</h1>'
    data_folder.make()
    f = File(data_folder.child('index.html'))
    f.write(content)
    home = Folder('/home')
    headers = {"Expires":get_expires()}
    bucket.add_file(f, target_folder=home.name, headers=headers)
    assert_headers_present(bucket.get_url() + '/home/index.html', headers)

    # Do it again with a different expires
    headers = {"Expires":get_expires(300)}
    bucket.add_file(f, target_folder=home.name, headers=headers)
    assert_headers_present(bucket.get_url() + '/home/index.html', headers)


@with_setup(cleanup)
def test_updating_headers_does_not_overwrite_existing():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    content = '<h1>A new html file on S3</h1>'
    data_folder.make()
    f = File(data_folder.child('index.html'))
    f.write(content)
    home = Folder('/home')
    headers = {"Expires":get_expires()}
    url = bucket.get_url() + '/home/index.html'
    bucket.add_file(f, target_folder=home.name, headers=headers)
    assert_headers_present(url, headers)

    res = requests.head(url)
    orig_headers = res.headers
    del orig_headers['x-amz-id-2']
    del orig_headers['x-amz-request-id']
    del orig_headers['last-modified']
    del orig_headers['date']

    bucket.add_file(f, target_folder=home.name, headers=headers)
    assert_headers_present(url, orig_headers)


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
def upload_folder(bucket, skip_css=False, headers=None):
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
    bucket.add_folder(data_folder, headers=headers)
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
def test_add_folder_header_callback():
    bucket = new_bucket()
    bucket.make()
    bucket.set_policy()
    bucket.serve()
    url = bucket.get_url()
    def headers(afile):
        if '/css/' in afile.path:
            return {'Expires': 10}
        elif '/js/' in afile.path:
            return {'Expires': 20}
        else:
            return {'Expires': 30}

    upload_folder(bucket, headers=headers)

    res = requests.head(url + '/media/css/site.css')
    assert res.headers['expires'] == '10'

    res = requests.head(url + '/media/js/site.js')
    assert res.headers['expires'] == '20'

    res = requests.head(url + '/home')
    assert res.headers['expires'] == '30'

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
