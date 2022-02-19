from otree.api import (
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
)
import common.SessionConfigFunctions as scf

from common.ParticipantFuctions import generate_participant_ids

doc = """
This application handles the final pay off
"""


def set_payoffs(subsession):
    for player in subsession.get_players():
        payoff = max(min(player.payoff, scf.get_bonus_cap(subsession)), 0)
        player.payoff = payoff


class Constants(BaseConstants):
    name_in_url = 'payment'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    @staticmethod
    def creating_session(subsession: BaseSubsession):
        generate_participant_ids(subsession)
        set_payoffs(subsession)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass
