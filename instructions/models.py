import numpy as np
from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer, cu,
)

import common.SessionConfigFunctions as scf
import rounds
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
    # qz1q1 = models.IntegerField(choices=[1, 2, 3, 4, 5, 6, 7, 8],
    #                             label='What is the maximum number of orders that you may place in each round?',
    #                             blank=True)

    # qz1q3 = models.BooleanField(label="When you short the STOCK you must pay out the dividend.",
    #                             blank=True)
    # qz1q4 = models.StringField(label='What is the interest rate paid out on CASH?',
    #                            blank=True)
    # qz1_attempted = models.BooleanField(initial=False)

    # @staticmethod
    # def qz1q4_choices(player):
    #     interest_rate = scf.get_interest_rate(player)
    #     start = interest_rate - .04
    #     end = interest_rate + .02
    #     choices = [scf.as_wnp(x) for x in np.arange(start, end, .01)]
    #     return choices

    ## QUIZ 2
    quiz_1 = models.BooleanField(label="In each round, all of your BUY prices must be greater than all of your SELL "
                                       "prices.",
                                 blank=True)

    quiz_2 = models.IntegerField(
        label="At what price will shares of STOCK be bought back at the end of the experiment?",
        blank=True)
    quiz_3 = models.IntegerField(label="""After the final trading period, you have 4 remaining units of STOCK. The 
    market price in the final period is 29. How many units of experiment CASH do you receive in exchange for your 
    STOCK?""",
                                 blank=True,
                                 choices=[[4, cu(4)], [29, cu(29)], [56, cu(56)], [116, cu(116)]]
                                 )
    quiz_4 = models.IntegerField(label="""Your account has 5 STOCK and 100 CASH at the start of a trading period, 
    and you do not BUY or SELL during that period. The dividend for that round is 1.00. How much CASH do you have at 
    the start of the next round?""",
                                 blank=True,
                                 choices=[[105, cu(105)], [110, cu(110)], [100, cu(100)], [114, cu(114)]]
                                 )
    qz_attempted = models.BooleanField(initial=False)

    @staticmethod
    def quiz_2_choices(player):
        fv = scf.get_fundamental_value(player)
        start = fv - 5.00
        end = fv + 3.00
        return [[int(x), f"{x}"] for x in np.arange(start, end, 1.00)]

    # @staticmethod
    # def qz2q2_choices(player):
    #     mr = scf.get_margin_ratio(player, wnp=True)
    #     return [[0, f'The amount of CASH you borrowed is more than {mr} of the value of you STOCK holdings'],
    #             [1, f'You have shorted the STOCK and your margin ratio drops below {mr}'],
    #             [2, 'Every two rounds to ensure an equal distribution of STOCK']]

    # @staticmethod
    # def qz2q3_choices(player):
    #     num_rounds = rounds.Constants.num_rounds
    #     start = max(num_rounds - 20, 0)
    #     end = num_rounds + 30
    #     return np.arange(start, end, 5)
