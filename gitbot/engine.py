import logging
import os
import yaml

from commando import Application, command, store, subcommand, true, version
from fswrap import File, Folder

from gitbot import generator
from gitbot.util import getLoggerWithConsoleHandler
from gitbot.version import __version__

logger = getLoggerWithConsoleHandler('gitbot')


class Engine(Application):

    def __init__(self, raise_exceptions=False):
        self.raise_exceptions = raise_exceptions
        super(Engine, self).__init__()

    def run(self, args=None):
        """
        The engine entry point.
        """

        # Catch any errors thrown and log the message.

        try:
            super(Engine, self).run(args)
        except Exception, e:
            if self.raise_exceptions:
                raise
            elif self.__parser__:
                self.__parser__.error(e.message)
            else:
                logger.error(e.message)
                return -1

    @command(description='gitbot - gitbot toolkit',
        epilog='Use %(prog)s {command} -h to get help on individual commands')
    @true('-v', '--verbose', help="Show detailed information in console")
    @version('--version', version='%(prog)s ' + __version__)
    @store('-c', '--config', default='project.yaml', help="Config file")
    def main(self, args, skip=False):
        if args.verbose:
            logger.setLevel(logging.DEBUG)
        conf = File(Folder(os.getcwd()).child(args.config))
        if not conf.exists:
            raise Exception(
                'Config file [{conf}] does not exist'.format(conf=conf.path))
        self.config = yaml.load(conf.read_all())
        self.config['file_path'] = conf.path
        if not skip:
            generator.render_project(self.config)
        print 'Done.'

    @subcommand('validate',
        help='Generates the templates and validates the stacks.')
    def validate(self, args):
        self.main(args, skip=True)
        generator.validate_stack(self.config)
        print 'Done.'

    @subcommand('publish', help='Publishes the stacks in the given config.')
    def publish(self, args):
        self.main(args, skip=True)
        generator.publish_project(self.config)
        print 'Done.'

    @subcommand('create',
        help='Creates a new stack. Regenerates unless specified.')
    @true('-i', '--interactive',
        help="Asks for parameter overrides interactively.")
    def create(self, args):
        self.main(args, skip=True)
        generator.create_project(self.config)
        print 'Done.'

    @subcommand('update',
        help='Updates a stack. Regenerates unless specified.')
    @true('-i', '--interactive',
        help="Asks for parameter overrides interactively.")
    def update(self, args):
        self.main(args, skip=True)
        generator.update_project(self.config)
        print 'Done.'
