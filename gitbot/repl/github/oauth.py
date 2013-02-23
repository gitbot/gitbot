import json
import requests
from requests.auth import HTTPBasicAuth
from util import get_auth

def get_token(scopes, note):
    auth = HTTPBasicAuth(*get_auth())
    url = 'https://api.github.com/authorizations'
    data = dict(scopes=scopes, note=note)
    r = requests.post(url, data=json.dumps(data), auth=auth)
    if r.status_code == 201:
        res = r.json()
        return res['token']
    else:
        raise Exception(r.text)

