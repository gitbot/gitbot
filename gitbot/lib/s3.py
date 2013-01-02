from boto.s3.connection import S3Connection
from boto.s3.key import Key
from fnmatch import fnmatch
from fswrap import File, Folder
from gitbot.util import getLoggerWithConsoleHandler


logger = getLoggerWithConsoleHandler('gitbot.lib.s3')


PUBLIC_POLICY_TEMPLATE = '''
{
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::%(bucket)s/*"
        }
    ]
}'''


class Bucket(object):

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        try:
            self.connection = S3Connection()
        except:
            raise Exception(
                'Please setup AWS security credentials in your environment.'
                'Add this to your startup file or virtualenv activate script:'
                'AWS_ACCESS_KEY_ID=<your aws key>'
                'AWS_SECRET_ACCESS_KEY=<your aws secret>'
                'export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY')

    def check_bucket(self):
        if not hasattr(self, 'bucket') or not self.bucket:
            raise Exception('You have not initialized a bucket yet.'
                ' Call `make` or `connect` before you call this method')

    def connect(self):
        try:
            self.bucket = self.connection.get_bucket(self.bucket_name)
        except:
            self.bucket = None

    def make(self):
        self.bucket = self.connection.create_bucket(self.bucket_name)

    def delete(self, recurse=False):
        if self.bucket:
            if recurse:
                keys = self.bucket.list()
                self.bucket.delete_keys([key.name for key in keys])
            self.bucket.delete()
        self.bucket = None

    def serve(self, index='index.html', error=None):
        self.bucket.configure_website(index, error_key=error)

    def set_policy(self, policy=None):
        self.check_bucket()
        if not policy:
            policy = PUBLIC_POLICY_TEMPLATE
            policy = (policy % dict(bucket=self.bucket_name)).strip()

        self.bucket.set_policy(policy)

    def get_url(self):
        self.check_bucket()
        return 'http://' + self.bucket.get_website_endpoint()

    def check_etag(self, key, source):
        source = File(source)
        if not source.exists or not key:
            return False
        etag = getattr(key, "etag", None)
        etag = etag.strip('\"\'').strip()
        return etag == source.etag

    def add_file(self, file_path,
                        check_etag=True,
                        target_folder=None,
                        acl='public-read',
                        headers=None):
        self.check_bucket()
        source = File(file_path)
        target_folder = Folder(target_folder or '')
        target = target_folder.child(source.name)
        key = self.bucket.get_key(target)
        if check_etag and self.check_etag(key, source):
            logger.info("Skipping [%s]..." % source.name)
            return target
        if not key:
            key = Key(self.bucket, target)

        def progress_logger(done, all):
            logger.info('%f/%f transferred' % (done, all))
        logger.info('beginning transfer of %s' % target)
        key.set_contents_from_filename(file_path.path, cb=progress_logger)
        logger.info('transfer complete')
        return target

    def get_signed_url(self, path, ttl=3000):
        return self.bucket.get_key(path).generate_url(ttl)

    def add_folder(self,
                        folder_path,
                        ignore_patterns=None,
                        target_folder=None,
                        acl='public-read',
                        headers=None):
        self.check_bucket()
        source = Folder(folder_path)
        added_files = []
        with source.walker as walker:
            def ignore(name):
                if not ignore_patterns:
                    return False
                return any(fnmatch(name, pattern)
                    for pattern in ignore_patterns)

            @walker.folder_visitor
            def visit_folder(folder):
                if ignore(folder.name):
                    logger.debug("Ignoring folder: %s" % folder.name)
                    return False
                return True

            @walker.file_visitor
            def visit_file(afile):
                prefix = afile.parent.get_mirror(target_folder or '', source)
                if not ignore(afile.name):
                    added = self.add_file(
                        afile,
                        target_folder=prefix,
                        acl=acl,
                        headers=headers)
                    added_files.append(added)

        for key in self.bucket.list(prefix=target_folder or ''):
            if not key.name in added_files:
                key.delete()
