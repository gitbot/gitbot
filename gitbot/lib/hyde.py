from commando.util import ShellCommand
from fswrap import Folder


def gen(source, data, target=None):
    source_command = ShellCommand(cwd=source.path)
    if source.child_file('requirements.txt').exists:
        source_command.call('pip', 'install', '-r', 'requirements.txt')
    if source.child_file('package.json').exists:
        source_command.call('npm', 'install')
    # Generate
    target = target or source.parent.child('dist/www')
    dist = Folder(target)
    dist.make()
    config = source.child_file(data.config or 'prod.yaml')
    txt = config.read_all()
    config.write(txt.format(data=data))
    source_command.call('hyde',
                            'gen', '-r',
                            '-c', config.name,
                            '-d', dist.path)
    return dist
