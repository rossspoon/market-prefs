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

doc = """
Instructions for the Short-squeeze market experiment
"""


class Constants(BaseConstants):
    name_in_url = 'instructions'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    ## QUIZ 1
    qz1q1 = models.IntegerField(choices=[1, 2, 3, 4, 5, 6, 7, 8],
                                label='What is the maximum number of orders that you may place in each round?')
    qz1q2 = models.BooleanField(label="It is possible to both buy and sell shares in a single market round.")
    qz1q3 = models.BooleanField(label="When you short the STOCK you must pay out the dividend.")
    qz1q4 = models.StringField(choices=['1%', '2%', '3%', '4%', '5%', '6%', '7%'],
                               label='What is the interest rate paid out on CASH?')

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
        if value != '5%':
            return "Interest on CASH is earned at 5%."

    ## QUIZ 2
    qz2q1 = models.CurrencyField(label="At what price will shares of STOCK be bought back at the end of the experiment?",
                                 choices=[1000, 1100, 1200, 1300, 1400, 1500])
    qz2q2 = models.IntegerField(label="An automatic BUY-IN will occur when:",
                                widget=widgets.RadioSelect,
                                choices=[[0, 'The amount of CASH you borrowed is more than 50% of the value of you STOCK holdings'],
                                         [1, 'The value of your shorted shares of STOCK is more that 50% of your amount of CASH'],
                                         [2, 'Every two rounds to ensure an equal distribution of STOCK']])
    qz2q3 = models.IntegerField(label="How many market periods will you participate in today?",
                                choices=[10, 20, 30, 40, 50, 60])

    @staticmethod
    def qz2q1_error_message(player, value):
        if value != 1400:
            return 'The system will buy back share of STOCK at a price of 1400 points'

    @staticmethod
    def qz2q2_error_message(player, value):
        if value != 1:
            return 'The value of you shorted shares of STOCK is more that 50% of your amount of CASH'

    @staticmethod
    def qz2q3_error_message(player, value):
        if value != 50:
            return 'The market will last for 50 periods'


