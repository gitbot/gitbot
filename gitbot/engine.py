import os
import yaml

from commando import Application, command, store, subcommand, true, version
from fswrap import File, Folder

from gitbot import generator, stack
from gitbot.version import __version__


class Engine(Application):

    @command(description='gitbot - gitbot toolkit',
        epilog='Use %(prog)s {command} -h to get help on individual commands')
    @true('-v', '--verbose', help="Show detailed information in console")
    @version('--version', version='%(prog)s ' + __version__)
    @store('-c', '--config', default='project.yaml', help="Config file")
    def main(self, args, skip=False):
        conf = File(Folder(os.getcwd()).child(args.config))
        if not conf.exists:
            raise Exception(
                'Config file [{conf}] does not exist'.format(conf=conf.path))
        self.config = yaml.load(conf.read_all())
        self.config['file_path'] = conf.path
        if not skip:
            generator.render_project(self.config)

    @subcommand('validate',
        help='Generates the templates and validates the stacks.')
    @true('-i', '--interactive',
        help="Asks for parameter overrides interactively.")
    def validate(self, args):
        self.main(args, skip=True)
        stack.validate_stack(self.config)
        print 'done.'

    @subcommand('upload', help='Uploads the stack(s) in the given config.')
    @true('-i', '--interactive',
        help="Asks for parameter overrides interactively.")
    def upload(self, args):
        self.main(args, skip=True)
        stack.upload_stack(self.config)
        print 'done.'

    @subcommand('publish',
        help='Creates or updates a stack. Always regenerates.')
    @true('-i', '--interactive',
        help="Asks for parameter overrides interactively.")
    def publish_stack(self, args):
        self.main(args, skip=True)
        stack.publish_stack(self.config)
        print 'done.'
