import json

import requests
from requests.auth import HTTPBasicAuth
from util import get_auth


def list_status(orgOrUser, repo, sha):
    url_templ = 'https://api.github.com/repos/{owner}/{repo}/statuses/{sha}'

    auth = HTTPBasicAuth(*get_auth())
    url = url_templ.format(owner=orgOrUser, repo=repo, sha=sha)
    r = requests.get(url, auth=auth)
    res = r.json()
    statuses = []
    for status in res:
        statuses.append(dict(
            id=status['id'],
            state=status['state'],
            target_url=status['target_url'],
            description=status['description']
        ))
    return statuses

def add_status(orgOrUser, repo, sha, data):
    url_templ = 'https://api.github.com/repos/{owner}/{repo}/statuses/{sha}'
    auth = HTTPBasicAuth(*get_auth())
    url = url_templ.format(owner=orgOrUser, repo=repo, sha=sha)
    r = requests.post(url, data=json.dumps(data), auth=auth)
    if r.status_code == 201:
        return list_status(orgOrUser, repo, sha)
    else:
        raise Exception(r.text)

__all__ = ['add_status', 'list_status']