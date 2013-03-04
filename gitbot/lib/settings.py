# -*- coding: utf-8 -*-
from datetime import datetime

from commando.conf import AutoProp, ConfigDict
from fswrap import Folder
from gitbot.lib import yinja
from gitbot.lib.git import Tree
from gitbot.lib.r53 import Route
from gitbot.lib.s3 import Bucket


ANNOTATION_TEMPLATE = '{project} version {version} built on {date}.\n'
DEPENDS_TEMPLATE = '\n    {project}={revision}'


class Release(AutoProp):

    def __init__(self, config=None, projects=None):
        config = config or dict()
        projects = projects or dict()

        self.config = ConfigDict(config)
        self.projects = {name: self.make_project(name, config)
                            for name, config in projects.iteritems()}

    def make_project(self, name, config):
        return Project(name, self, config)

    @AutoProp.default
    def repo_base(self):
        return self.config.get('repo_base', 'https://github.com')

    @AutoProp.default
    def repo_owner(self):
        return self.config.get('repo_owner')

    @AutoProp.default
    def source_root(self):
        return self.config.get('source_root')

    @AutoProp.default
    def build_root(self):
        return self.config.get('build_root')

    @AutoProp.default
    def tools_root(self):
        return self.config.get('tools_root')

    @AutoProp.default
    def dateformat(self):
        return self.config.get('dateformat', '%A, %d. %B %Y %I:%M%p')

    @classmethod
    def load(cls,
            file_name='build.yaml',
            context=None):
        config = yinja.load(file_name, context=context)
        projects = config.get('projects', dict())
        config = config.get('config', dict())
        return cls(config, projects)

    def pull(self, tip_only=False):
        for project in self.projects.itervalues():
            if project.needs_source:
                project.pull(tip_only)


class Project(AutoProp):

    def __init__(self, name, release, config=None):
        if not name or not release:
            raise ValueError("name and release are required")
        self.name = name
        self.release = release
        self.bucket = None
        self.config = ConfigDict(config or {})
        self.annotation_header_template = config.get(
                                        'annotation_header_template',
                                        ANNOTATION_TEMPLATE)
        self.depends_template = config.get(
                                        'depends_template',
                                        DEPENDS_TEMPLATE)

    @property
    def depends(self):
        return [self.release.projects[project] for project in
                                self.config.get('depends', [])]

    @property
    def needs_source(self):
        return self.config.get('needs_source', True)

    @AutoProp.default
    def version(self):
        return self.config.get('version')

    @AutoProp.default
    def source_dir(self):
        return self.config.get('source_dir',
            '%s/%s' % (self.release.source_root, self.name))

    @AutoProp.default
    def build_dir(self):
        return self.config.get('build_dir',
            '%s/%s' % (self.release.build_root, self.name))

    @AutoProp.default
    def repo_owner(self):
        return self.config.get('repo_owner', self.release.repo_owner)

    @AutoProp.default
    def repo(self):
        return self.config.get('repo',
            '%s/%s/%s' % (self.release.repo_base, self.repo_owner, self.name))

    @AutoProp.default
    def remote(self):
        return self.config.get('remote', 'origin')

    @AutoProp.default
    def branch(self):
        return self.config.get('branch', 'master')

    @property
    def version_published(self):
        return self.tree.tagger.check(str(self.version))

    @property
    def tree(self):
        return Tree(self.source_dir,
                        self.repo,
                        self.remote,
                        self.branch)

    def has_source_changed(self):
        return self.tree.has_changes()

    @property
    def revision(self):
        return self.tree.get_revision(short=False).strip()

    @property
    def modified(self):
        return self.tree.get_last_committed().strftime(
                                    self.release.dateformat)

    def pull(self, tip_only=False):
        self.tree.pull(tip_only)

    def merge(self, ref):
        if not Folder(self.source_dir).exists:
            self.pull()
        self.tree.fetch_ref(ref, local='gitbot/local', notags=True)
        self.tree.merge('gitbot/local', ff_only=False)

    def tag(self, version=None):
        version = version or str(self.version)
        annotation = self.tag_annotation()
        self.tree.tagger.add(version, message=annotation, push=True, sync=True)

    def tag_annotation(self):
        annotation = self.annotation_header_template.format(
                        project=self.name,
                        version=self.version,
                        date=datetime.utcnow())
        if self.depends:
            annotation += 'Uses: \n'
        for project in self.depends:
            annotation += self.depends_template.format(
                            project=project.name,
                            revision=project.revision)
        return annotation

    def get_route(self):
        return Route(self.release.config.zone,
                    aws_access_key_id=self.release.config.awskeys.access_key,
                    aws_secret_access_key=self.release.config.awskeys.secret)

    def make_bucket(self, bucket_name, error='404.html', make_route=False):
        bucket = Bucket(bucket_name,
                    aws_access_key_id=self.release.config.awskeys.access_key,
                    aws_secret_access_key=self.release.config.awskeys.secret)
        bucket.make()
        bucket.set_policy()
        bucket.serve(error=error)

        if make_route:
            route = self.get_route()
            try:
                route.add_route_to_bucket(bucket_name)
            except:
                pass

        return bucket

    def get_bucket(self, bucket_name):
        bucket = Bucket(bucket_name,
                    aws_access_key_id=self.release.config.awskeys.access_key,
                    aws_secret_access_key=self.release.config.awskeys.secret)
        bucket.connect()
        return bucket


    def delete_bucket(self, bucket_name, delete_route=False):
        bucket = Bucket(bucket_name,
                    aws_access_key_id=self.release.config.awskeys.access_key,
                    aws_secret_access_key=self.release.config.awskeys.secret)

        if delete_route:
            route = self.get_route()
            try:
                route.delete_route_to_bucket(bucket_name)
            except:
                # Route does not exist
                pass

        if bucket.connect():
            bucket.delete(recurse=True)


__all__ = ['Release', 'Project']