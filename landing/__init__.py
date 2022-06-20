import os
import threading
from datetime import datetime

from otree.api import *
from otree.database import db

import common.SessionConfigFunctions as scf

doc = """
Landing app used to queue up users.
"""

lock = threading.Lock()
COUNT = [0]


def inc_and_get():
    cnt = 0
    with lock:
        COUNT[0] += 1
        cnt = COUNT[0]
    return cnt


LIMIT_ENV = os.getenv('LANDING_LIMIT')
URL = os.getenv('EXPERIMENT_URL')


class C(BaseConstants):
    NAME_IN_URL = 'landing'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    if LIMIT_ENV:
        LIMIT = int(LIMIT_ENV)
    else:
        LIMIT = 0


def creating_session(subsession):
    COUNT[0] = 0


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    count = models.IntegerField(blank=True)
    clicked = models.BooleanField(initial=False)


# Live methods
def button_page_live(player, d):
    func = d['func']

    if func == 'click':
        cnt = inc_and_get()
        player.count = cnt
        player.clicked = True
        db.commit()

        bar_info = get_bar_info(cnt)
        filled = cnt >= C.LIMIT

        return {0: dict(func='bar', bar_info=bar_info, filled=filled)}

    elif func == 'is_in':
        return {player.id_in_group: dict(func='is_in', is_in=player.count <= C.LIMIT)}


def get_bar_info(cnt):
    # percentage should never exceed 100%
    # cnt should never exceed n
    cnt_capped = min(cnt, C.LIMIT)
    if cnt == 0:
        pct_as_decimal = .1
    else:
        pct_as_decimal = max(cnt_capped / C.LIMIT, .1)
    pct = f"{pct_as_decimal: .0%}"
    bar_info = dict(pct=pct, count=cnt_capped, N=C.LIMIT)
    return bar_info


def get_url(player):
    base_url = URL
    if not base_url:
        base_url = scf.get_default_url(player)

    label = player.participant.label
    if not label:
        label = player.participant.code

    url = base_url.format(label)
    return url


# PAGES
class LandingPage(Page):
    timer_text = ''

    @staticmethod
    def get_timeout_seconds(player: Player):
        start_time = scf.get_start_time(player)
        now = datetime.now()
        # dattime.timestamp() returns the number of seconds since the epoch
        diff = (start_time.timestamp() - now.timestamp())
        return diff

    @staticmethod
    def vars_for_template(player: Player):
        start_time = scf.get_start_time(player)
        start_time_txt = datetime.strftime(start_time, '%I:%M %p')
        show_next = scf.show_next_button(player)
        return {'start_time': start_time_txt,
                'show_next': show_next}


class ButtonPage(Page):

    @staticmethod
    def vars_for_template(player: Player):
        cnt = COUNT[0]

        ret = get_bar_info(cnt)
        return ret

    @staticmethod
    def js_vars(player: Player):
        return {'clicked': player.clicked}

    live_method = button_page_live


class ExperimentRedirect(Page):
    @staticmethod
    def js_vars(player: Player):
        return {'url': get_url(player)}

    def is_displayed(player: Player):
        return player.field_maybe_none('count') is not None and player.count <= C.LIMIT


class ExperimentFull(Page):
    pass


page_sequence = [LandingPage, ButtonPage, ExperimentRedirect, ExperimentFull]
