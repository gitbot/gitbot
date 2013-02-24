import json
import urllib

import requests
from util import get_auth

def trigger_action(proj, repo, branch, sha, event='push'):
    url_templ = 'http://api.gitbot.io/hooks/projects/{project}/trigger'
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