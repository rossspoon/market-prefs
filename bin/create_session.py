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

def check_session(code):
    resp_check = call_api(GET, 'sessions', code)
    del resp_check['participants']
    return resp_check

def make_exp(N, l, is_pilot, start_time, is_prolific, is_mturk, dist):

    participation_fee = 8.00 if is_pilot else 16.00

    session_configs = dict(
        is_pilot = is_pilot,
        is_prolific = is_prolific,
        is_mturk = is_mturk,
        endow_stock = dist,
        participation_fee = participation_fee,
        start_time = start_time,
    )

    # Create the experiment session
    resp_exp_create = call_api(POST, 'sessions',
                session_config_name='whole_experiment',
                room_name='market2',
                num_participants=N,
                modified_session_config_fields=session_configs,
                )
    exp_code = resp_exp_create['code']
    resp_exp_check = check_session(exp_code)

    # Create the landing session
    resp_land_create = call_api(POST, 'sessions',
                session_config_name='landing',
                room_name='landing',
                num_participants=l,
                modified_session_config_fields=session_configs,
                )
    land_code = resp_land_create['code']
    resp_land_check = check_session(land_code)

    return {exp_code: resp_exp_check, land_code: resp_land_check}


def make_screen(N, is_pilot, is_prolific, is_mturk, times, participation_fee=0.75):
    session_configs = dict(
        is_pilot = is_pilot,
        is_prolific = is_prolific,
        is_mturk = is_mturk,
        participation_fee = participation_fee,
        slot_01='',
        slot_02='',
        slot_03='',
        slot_04='',
        slot_05='',
        slot_06='',
        slot_07='',
        slot_08='',
        slot_09='',
        slot_10='',
    )

    # set the times in the times on the slots
    for idx, t in enumerate(times.split()):
        slot_num = idx+1
        slot = f"slot_{slot_num:0>2}"
        session_configs[slot] = t

    resp_screen_create = call_api(POST, 'sessions',
                session_config_name='prescreen',
                room_name='prescreen',
                num_participants=40,
                modified_session_config_fields=session_configs,
                )
    screen_code = resp_screen_create['code']
    resp_screen_check = check_session(screen_code)

    return {screen_code: resp_screen_check}


USAGE = 'create_session.py  -s <exp | screen> -n <num_participants> -l <landing_page_participants> p ' \
        't <start time> --dist=<share distribution>  --prolific --mturk --local'

def main(argv):
    stage = ''               # s:
    dist = '0 2 4'           # dist=
    is_pilot = False         # p
    N = 0                    # n:
    l_num = 0                # l:
    start_time = None        # t:
    is_prolific = True       # prolific
    is_mturk = False         # mturk
    base_url = SERVER_URL    # --local
    times = ""               # times=

    try:
        opts, args = getopt.getopt(argv, "ps:n:l:t:", ["dist=", "local", "prolific", "mturk", "times="])
    except getopt.GetoptError as e:
        print("Error parsing options: ", e)
        print (USAGE)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-p':
            is_pilot = True

        elif opt == '-s':
            stage = arg

        elif opt == '-n':
            N = int(arg)

        elif opt == '-l':
            l_num = int(arg)

        elif opt == '-t':
            start_time = arg

        elif opt == '--dist':
            dist = arg

        elif opt == '--prolific':
            is_prolific = True
            is_mturk = False

        elif opt == '--mturk':
            is_prolific = False
            is_mturk = True

        elif opt == '--local':
            BASE_URL[0] = LOCAL_SERVER_URL
            print(BASE_URL[0])

        elif opt == '--times':
            times = arg


    print (opts)
    if stage not in ['exp', 'screen'] or (stage == 'exp' and not start_time):
        print(USAGE)
        sys.exit(2)

    if stage == 'exp':
        resp = make_exp(N, l_num, is_pilot, start_time, is_prolific, is_mturk, dist)
        pprint(resp)

    if stage == 'screen':
        resp = make_screen(N, is_pilot, is_prolific, is_mturk, times)
        pprint(resp)


if __name__ == "__main__":
    main(sys.argv[1:])