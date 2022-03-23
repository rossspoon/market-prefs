import random

from otree.api import (
    BaseSubsession,
)
from otree.models import Participant

PARTICIPANT_ID_SPACE = 99 * 26 + 26


def generate_participant_id(x):
    id_num = x // 26
    id_letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[x % 26]
    part_id = f"{id_num:02d}{id_letter}"
    return part_id


def generate_participant_ids(subsession: BaseSubsession):
    population = list(range(PARTICIPANT_ID_SPACE))
    players = subsession.get_players()
    num_parts = len(players)
    ids = [generate_participant_id(x) for x in random.sample(population, num_parts)]
    for pid, player in zip(ids, players):
        existing = player.participant.vars.get('PART_ID')
        if not existing:
            player.participant.PART_ID = pid
            player.participant.label = pid


# def generate_participant_ids(subsession: BaseSubsession):
#    for player in subsession.get_players():
#        participant = player.participant
#        existing = player.participant.vars.get('PART_ID')
#        pid = participant.code[-3:].upper()
#        if not existing:
#            player.participant.PART_ID = pid

def ensure_participant(obj):
    if type(obj) == Participant:
        return obj
    else:
        return obj.participant


def is_button_click(obj):
    participant = ensure_participant(obj)
    return bool(participant.vars.get('CONSENT_BUTTON_CLICKED'))
