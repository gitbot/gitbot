from subprocess import check_output

def get_auth():
    user = check_output(['git', 'config', '--get', 'github.user']).strip()
    password = check_output(['git', 'config',
                                '--get', 'github.password']).strip()
    if not user or not password:
        print 'Please setup your github auth information in git config'
        print 'git config --global github.user <username>'
        print 'git config --global github.password <password>'
        raise Exception("Need github authentication information.")
    return  (user, password)


__all__ = ['get_auth']