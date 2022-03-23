from otree.api import (
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
)
import common.SessionConfigFunctions as scf

from common.ParticipantFuctions import generate_participant_ids, is_button_click

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

    @staticmethod
    def vars_for_admin_report(subsession: BaseSubsession):
        clickers = list(filter(lambda x: is_button_click(x), subsession.get_players()))
        player_data = [to_variable_dict(p) for p in clickers]
        total = sum(d['total'] for d in player_data)
        if len(clickers) > 0:
            average = total/ len(clickers)
        else:
            average = 'N/A'
        return {'players': player_data, 'total': total, 'average': average}


def to_variable_dict(player: BasePlayer):
    part = player.participant
    session = player.session
    return dict(label=part.label,
                bonus=part.payoff.to_real_world_currency(session),
                total=part.payoff_plus_participation_fee()
                )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass
