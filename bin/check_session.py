#!python

import requests  # pip3 install requests
from pprint import pprint
from os import environ
import sys
import getopt

GET = requests.get
POST = requests.post

# if using Heroku, change this to https://YOURAPP.herokuapp.com
LOCAL_SERVER_URL = 'http://localhost:8000'
SERVER_URL = 'https://vt-market-experiment.herokuapp.com'
BASE_URL = [SERVER_URL]
REST_KEY = environ.get('REST_FKEY')

def call_api(method, *path_parts, **params) -> dict:
    path_parts = '/'.join(path_parts)
    url = f'{BASE_URL[0]}/api/{path_parts}/'
    resp = method(url, json=params, headers={'otree-rest-key': REST_KEY})
    if not resp.ok:
        msg = (
            f'Request to "{url}" failed '
            f'with status code {resp.status_code}: {resp.text}'
        )
        raise Exception(msg)
    return resp.json()

res = call_api(GET, 'sessions', 'jz45cs81')
pprint(res)