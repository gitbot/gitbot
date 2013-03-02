import json
import urllib

import requests
from requests.auth import HTTPBasicAuth
from util import get_auth

def trigger_push_action(proj, repo, branch, sha):
    url_templ = 'http://api.gitbot.io/hooks/projects/{project}/trigger'
    event = 'push'
    data = dict(
        project=proj,
        repo=repo,
        branch=branch,
        sha=sha,
        event=event
    )
    headers = {
        "Content-type": "application/json",
        "Accept": "text/plain"
    }
    url = url_templ.format(project=urllib.quote_plus(proj))
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print 'Build triggerred successfully.'
    else:
        print 'Cannot trigger build'
        print response.text

def trigger_pull_action(proj, repo, number):

    # Fetch pull request from github
    url_templ = 'https://api.github.com/repos/{repo}/pulls/{number}'
    api_url = url_templ.format(repo=repo, number=number)
    auth = HTTPBasicAuth(*get_auth())
    r = requests.get(api_url, auth=auth)
    if r.status_code / 100 != 2:
        raise Exception('Cannot get the pull request', r.text)

    res = r.json()

    # Call trigger action

    pull_request = res['pull_request']
    base = pull_request['base']
    head = pull_request['head']
    data = dict(
        project=proj,
        repo=repo,
        branch=base['ref'].replace('refs/heads/',''),
        sha=base['sha'],
        ref=base['ref'],
        event='pull_request',
        praction=res['action'],
        number=res['number'],
        source=dict(
            repo=head['repo']['full_name'],
            branch=head['ref'].replace('refs/heads/',''),
            sha=head['sha'],
            ref=head['ref']
        )
    )
    headers = {
        "Content-type": "application/json",
        "Accept": "text/plain"
    }
    url_templ = 'http://api.gitbot.io/hooks/projects/{project}/trigger'
    url = url_templ.format(project=urllib.quote_plus(proj))
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print 'Build triggerred successfully.'
    else:
        print 'Cannot trigger build'
        print response.text


def trigger_status(build_id, status, url=None, message=None):
    url_templ = 'http://api.gitbot.io/hooks/jobs/{build}/status'
    data = dict(
        state=status,
        message=message,
        url=url
    )
    headers = {
        "Content-type": "application/json",
        "Accept": "text/plain"
    }
    url = url_templ.format(build=urllib.quote_plus(build_id))
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print 'Status set successfully.'
    else:
        print 'Cannot set status'
        print response.text

__all__ = ['trigger_push_action', 'trigger_pull_action', 'trigger_status']