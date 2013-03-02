import requests
from requests.auth import HTTPBasicAuth
from util import get_auth

def list_hooks(orgOrUser, repoOrRepos, hook_type=None):
    url_templ = 'https://api.github.com/repos/{owner}/{repo}/hooks'

    if not isinstance(repoOrRepos, list):
        repoOrRepos = [repoOrRepos]
    hooks = []
    auth = HTTPBasicAuth(*get_auth())
    for repo in repoOrRepos:
        url = url_templ.format(owner=orgOrUser, repo=repo)
        r = requests.get(url, auth=auth)
        res = r.json()
        for hook in res:
            if not hook_type or hook['name'] == hook_type:
                hooks.append(dict(
                    events=hook['events'],
                    repo=repo,
                    hook=hook['id']
                ))
    return hooks

def delete_hooks(orgOrUser, repoOrRepos, hook_type=None):
    hooks = list_hooks(orgOrUser, repoOrRepos, hook_type)
    url_templ = 'https://api.github.com/repos/{owner}/{repo}/hooks/{hook}'
    auth = HTTPBasicAuth(*get_auth())
    for hook in hooks:
        url = url_templ.format(**hook)
        r = requests.delete(url, auth=auth)

__all__ = ['list_hooks', 'delete_hooks']

