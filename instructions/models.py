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
import common.SessionConfigFunctions as scf
import rounds
import numpy as np
from common.ParticipantFuctions import generate_participant_ids


doc = """
Instructions for the Short-squeeze market experiment
"""


class Constants(BaseConstants):
    name_in_url = 'instructions'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    @staticmethod
    def creating_session(subsession: BaseSubsession):
        generate_participant_ids(subsession)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    ## QUIZ 1
    qz1q1 = models.IntegerField(choices=[1, 2, 3, 4, 5, 6, 7, 8],
                                label='What is the maximum number of orders that you may place in each round?')
    qz1q2 = models.BooleanField(label="It is possible to both buy and sell shares in a single market round.")
    qz1q3 = models.BooleanField(label="When you short the STOCK you must pay out the dividend.")
    qz1q4 = models.StringField(label='What is the interest rate paid out on CASH?')

    @staticmethod
    def qz1q1_error_message(player, value):
        if value != 6:
            return "You are allowed up to 6 orders per market period."

    @staticmethod
    def qz1q2_error_message(player, value):
        if value:
            return "You may not BUY and SELL at the same time."

    @staticmethod
    def qz1q3_error_message(player, value):
        if not value:
            return "When you short the STOCK, dividends  will be deducted from you CASH holdings."

    @staticmethod
    def qz1q4_error_message(player, value):
        ir = scf.as_wnp(scf.get_interest_rate(player))
        if value != ir:
            return f"Interest on CASH is earned at {ir}."

    @staticmethod
    def qz1q4_choices(player):
        interest_rate = scf.get_interest_rate(player)
        start = interest_rate - .04
        end = interest_rate + .02
        choices = [scf.as_wnp(x) for x in np.arange(start, end, .01)]
        return choices

    ## QUIZ 2
    qz2q1 = models.CurrencyField(
        label="At what price will shares of STOCK be bought back at the end of the experiment?")
    qz2q2 = models.IntegerField(label="An automatic BUY-IN will occur when:",
                                widget=widgets.RadioSelect)
    qz2q3 = models.IntegerField(label="How many market periods will you participate in today?")

    @staticmethod
    def qz2q1_error_message(player, value):
        fundamental = scf.get_fundamental_value(player)
        if value != fundamental:
            return f'The system will buy back share of STOCK at a price of {fundamental} points'

    @staticmethod
    def qz2q2_error_message(player, value):
        mr = scf.get_margin_ratio(player, wnp=True)
        if value != 1:
            return f'The value of you shorted shares of STOCK is more that {mr} of your amount of CASH'

    @staticmethod
    def qz2q3_error_message(player, value):
        num = rounds.Constants.num_rounds
        if value != num:
            return f'The market will last for {num} periods'

    @staticmethod
    def qz2q1_choices(player):
        fv = scf.get_fundamental_value(player)
        start = fv - 500
        end = fv + 300
        return [int(x) for x in np.arange(start, end, 100)]

    @staticmethod
    def qz2q2_choices(player):
        mr = scf.get_margin_ratio(player, wnp=True)
        return [[0, f'The amount of CASH you borrowed is more than {mr} of the value of you STOCK holdings'],
                [1, f'The value of your shorted shares of STOCK is more that {mr} of your amount of CASH'],
                [2, 'Every two rounds to ensure an equal distribution of STOCK']]

    @staticmethod
    def qz2q3_choices(player):
        num_rounds = rounds.Constants.num_rounds
        start = max(num_rounds - 20, 0)
        end = num_rounds + 30
        return np.arange(start, end, 5)
