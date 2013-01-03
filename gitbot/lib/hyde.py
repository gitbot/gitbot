from fswrap import File
from gitbot.util import CommandBuilder


def gen(source, data):
    source_command = CommandBuilder(cwd=source.path)
    if File(source.child('requirements.txt')).exists:
        source_command.call('pip', 'install', '-r', 'requirements.txt')
    if File(source.child('package.json')).exists:
        source_command.call('npm', 'install')
    # Generate
    dist = source.parent.child_folder('dist/www')
    dist.make()
    config = File(source.child(data.config or 'prod.yaml'))
    txt = config.read_all()
    config.write(txt.format(data=data))
    source_command.call('hyde',
                            'gen', '-r',
                            '-c', config.name,
                            '-d', dist.path)
    return dist
