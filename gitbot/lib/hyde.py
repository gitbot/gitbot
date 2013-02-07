from commando.util import ShellCommand
from fswrap import Folder
from gitbot.lib.yinja import transform


def gen(source, data, target=None):
    source_command = ShellCommand(cwd=source.path)
    if source.child_file('requirements.txt').exists:
        source_command.call('pip', 'install', '-r', 'requirements.txt')
    if source.child_file('package.json').exists:
        source_command.call('npm', 'install')
    
    # Generate
    target = target or data.target or source.parent.child('dist/www')
    dist = Folder(target)
    dist.make()


    template = source.child_file(data.config_template or 'env.yaml')
    conf = source.child_file(data.config_file_name or 'settings.gitbot')
    transform(source, conf, data)

    source_command.call('hyde',
                            'gen', '-r',
                            '-c', conf.name,
                            '-d', dist.path)
    return dist
