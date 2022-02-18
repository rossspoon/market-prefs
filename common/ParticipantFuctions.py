from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)
from otree.models import Session
import numpy as np
import random

PARTICIPANT_ID_SPACE = 99 * 26 + 26

def generate_participant_id(x):
    id_num = x // 26
    id_letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[x % 26]
    part_id = f"{id_num:02d}{id_letter}"
    return part_id


#def generate_participant_ids(subsession: BaseSubsession):
#    population = list(range(PARTICIPANT_ID_SPACE))
#    players = subsession.get_players()
#    num_parts = len(players)
#    ids = [generate_participant_id(x) for x in random.sample(population, num_parts)]
#    existing = player.participant.vars.get('PART_ID')
#    if not existing:
#        player.participant.PART_ID = pid

def generate_participant_ids(subsession: BaseSubsession):
    for player in subsession.get_players():
        participant = player.participant
        existing = player.participant.vars.get('PART_ID')
        pid = participant.code[-3:].upper()
        if not existing:
            player.participant.PART_ID = pid