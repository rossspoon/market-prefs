import pandas as pd
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
BASE_URL = [LOCAL_SERVER_URL]
REST_KEY = "s+Uj_g5Zunap3?TfZ6uUQ7" #"environ.get('REST_FKEY')"

landing_data = pd.read_csv('~/Downloads/landing_data.csv')
test_url_ext = '/room/market2'
for p in landing_data['participant.label'].values:
    print(f"{BASE_URL[0]}{test_url_ext}?participant_label={p}")

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


for row in landing_data[landing_data['player.consent_given']==1][['participant.label', 'player.quiz_grade']].values:
    p = row[0]
    q = row[1]
    print(p, q)
    res = call_api(POST, 'participant_vars', room_name='market2', participant_label=p, vars={'quiz_grade': q})

    res = call_api(POST, 'participant_vars', room_name='market2', participant_label='lkjlkj', vars={'quiz_grade': q})
