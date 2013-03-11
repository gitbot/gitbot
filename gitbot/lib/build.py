# -*- coding: utf-8 -*-
from datetime import datetime
import os

from commando.conf import AutoProp, ConfigDict
from commando.util import load_python_object
from fswrap import Folder
from gitbot.lib import yinja
from gitbot.lib.git import GitException, Tree
from gitbot.lib.r53 import Route
from gitbot.lib.s3 import Bucket


ANNOTATION_TEMPLATE = '{project} version {version} \n    built on {date}.\n'
DEPENDS_TEMPLATE = '\n    {project}={revision}'

__PROJECTS__ = {}
__ENV__ = {}

BuildStatus = type(
    'BuildStatus', (),
    {s.capitalize():s for s in [
    'queued', 'started', 'running',
    'completed',
    'failed', 'error', 'conflicted']})


class BuildException(Exception):

    def __init__(self, description, status):
        self.description = description
        self.status = getattr(BuildStatus, status)
        super(BuildException, self).__init__(description, status)


class BuildFailedException(BuildException):

    def __init__(self, description):
        super(BuildFailedException, self).__init__(
                                    description,
                                    BuildStatus.Failed)

class BuildErrorException(BuildException):

    def __init__(self, description):
        super(BuildFailedException, self).__init__(
                                    description,
                                    BuildStatus.Error)

class BuildConflictedException(BuildException):

    def __init__(self, description):
        super(BuildConflictedException, self).__init__(
                                    description,
                                    BuildStatus.Conflicted)


class Project(AutoProp):

    def __init__(self, name, config=None,
                    env=None,
                    settings=None,
                    context=None,
                    conf_path=None):
        if not name:
            raise ValueError("project name is required")
        self.name = name
        self.config = ConfigDict(config or {})
        self.config.work_root = self.config.get('work_root',
                                    Folder(os.getcwd()).child('out'))
        self.env = env
        self.settings = settings
        self.conf_path = conf_path
        self.context = context
        self.annotation_header_template = config.get(
            'annotation_header_template',
            ANNOTATION_TEMPLATE)
        self.depends_template = config.get(
            'depends_template',
            DEPENDS_TEMPLATE)
        self._depends = None

    @property
    def depends(self):
        if not self._depends:
            depends = self.config.get('depends', {})
            self._depends = {
                                project_name: self.load_dependent(project_name,
                                                    project_env)
                                for project_name, project_env in depends.items()
                            }
        return self._depends


    @AutoProp.default
    def work_root(self):
        return self.config.get('work_root')

    @AutoProp.default
    def source_root(self):
        return self.config.get('source_root',
            Folder(self.work_root).child('sources'))

    @AutoProp.default
    def build_root(self):
        return self.config.get('build_root',
            Folder(self.work_root).child('dist'))

    @AutoProp.default
    def tools_root(self):
        return self.config.get('tools_root',
            Folder(self.work_root).child('tools'))

    @AutoProp.default
    def dateformat(self):
        return self.config.get('dateformat', '%A, %d. %B %Y %I:%M%p')

    @property
    def needs_source(self):
        return self.config.get('needs_source', True)

    @AutoProp.default
    def version(self):
        return self.config.get('version')

    @AutoProp.default
    def source_dir(self):
        return self.config.get('source_dir',
                               '%s/%s' % (self.source_root, self.name))

    @AutoProp.default
    def build_dir(self):
        return self.config.get('build_dir',
                               '%s/%s' % (self.build_root, self.name))

    @AutoProp.default
    def repo_base(self):
        return self.config.get('repo_base', 'https://github.com')

    @AutoProp.default
    def repo_owner(self):
        return self.config.get('repo_owner')

    @AutoProp.default
    def repo_name(self):
        return self.config.get('repo_name', self.name)

    @AutoProp.default
    def repo(self):
        return self.config.get('repo',
                '%s/%s/%s' % (self.repo_base, self.repo_owner, self.repo_name))

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
        try:
            return self.tree.get_revision(short=False).strip()
        except GitException:
            return self.tree.get_revision_remote().strip()

    @property
    def modified(self):
        return self.tree.get_last_committed().strftime(
            self.dateformat)

    def pull(self, tip_only=False, pull_depends=False):
        self.tree.pull(tip_only)
        if pull_depends:
            for dep in self.depends.itervalues():
                dep.pull(tip_only=tip_only)

    def merge(self, ref):
        if not Folder(self.source_dir).exists:
            self.pull()
        self.tree.fetch_ref(ref, local='gitbot/local', notags=True)
        try:
            self.tree.merge('gitbot/local', ff_only=False)
        except GitException, gitex:
            raise BuildConflictedException(unicode(gitex))

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
        for project in self.depends.itervalues():
            annotation += self.depends_template.format(
                project=project.name,
                revision=project.revision)
        return annotation

    def get_route(self):
        return Route(self.config.zone,
                     aws_access_key_id=self.config.awskeys.access_key,
                     aws_secret_access_key=self.config.awskeys.secret)

    def make_bucket(self, bucket_name, error='404.html', make_route=False):
        bucket = Bucket(bucket_name,
                        aws_access_key_id=self.config.awskeys.access_key,
                        aws_secret_access_key=self.config.awskeys.secret)
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
                        aws_access_key_id=self.config.awskeys.access_key,
                        aws_secret_access_key=self.config.awskeys.secret)
        bucket.connect()
        return bucket

    def delete_bucket(self, bucket_name, delete_route=False):
        bucket = Bucket(bucket_name,
                        aws_access_key_id=self.config.awskeys.access_key,
                        aws_secret_access_key=self.config.awskeys.secret)

        if delete_route:
            route = self.get_route()
            try:
                route.delete_route_to_bucket(bucket_name)
            except:
                # Route does not exist
                pass

        if bucket.connect():
            bucket.delete(recurse=True)


    def load_dependent(self, project_name, env='build'):
        return self._load(project_name, env, self.context, self.conf_path)


    @classmethod
    def _load(cls, project_name, env='build', context=None, conf_path=None):
        if project_name in __PROJECTS__:
            return __PROJECTS__[project_name]
        settings = __ENV__.get(env, None)
        if not settings:
            file_name = env + '.yaml'
            if conf_path:
                file_name = Folder(conf_path).child(file_name)
            settings = yinja.load(file_name, context=context)
            __ENV__[env] = settings

        config = ConfigDict()
        config.update(settings.config)
        config.patch(settings.projects.get(project_name, dict()))
        project_type = config.get('type_name', 'gitbot.lib.build.Project')
        project_class = load_python_object(project_type)
        project = project_class(project_name,
                                    config,
                                    env,
                                    settings,
                                    context,
                                    conf_path)
        __PROJECTS__[project_name] = project
        return project


    @classmethod
    def load(cls, project_name, env='build', context=None, conf_path=None):
        global __PROJECTS__, __ENV__
        __PROJECTS__ = {}
        __ENV__ = {}
        context = context or {}
        context['env'] = env
        context['project_name'] = project_name
        return cls._load(project_name, env, context, conf_path)

    @classmethod
    def load_with_trigger(cls, trigger, conf_path=None):
        try:
            env = trigger['action']['env']
        except KeyError:
            env = 'adhoc'
        trigger = ConfigDict(trigger)
        project_name = trigger.action.component_name
        project = cls.load(project_name, env, trigger, conf_path)
        project.config.main = True
        project.config.trigger = trigger
        project.config.fetch = trigger.fetch
        project.config.sha = trigger.sha
        project.config.ref = trigger.ref
        project.config.branch = trigger.branch
        return project

__all__ = ['Project']
