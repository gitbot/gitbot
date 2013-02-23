import requests
from util import get_auth
import json
import urllib

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