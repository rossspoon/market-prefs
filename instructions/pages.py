import inspect
import sys

from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, Player

def vars_for_temp_common(player: Player):
    pass

class IntroPage(Page):
    pass


class _01_Assets(Page):
    pass


class _02_Trading(Page):
    pass


class _03_BorrowingCash(Page):
    pass


class _04_ShortingStock(Page):
    pass


class _05_MarketRestrictions_1(Page):
    pass


class _06_MarketRestrictions_2(Page):
    pass


class _07_MarketPeriod(Page):
    pass


class _08_AutoBuyIn(Page):
    pass


class _09_AutoSellOff(Page):
    pass


class _10_Bankruptcy(Page):
    pass


class _11_MarketPeriod_2(Page):
    pass


class _12_MarketPage(Page):
    pass


class _13_ForecastingPage(Page):
    pass


class _14_PeriodSummary(Page):
    pass


class _15_EndOfMarket(Page):
    pass


class Quiz01(Page):
    form_model = Player
    form_fields = ['qz1q1', 'qz1q2', 'qz1q3', 'qz1q4']


class Quiz02(Page):
    form_model = Player
    form_fields = ['qz2q1', 'qz2q2', 'qz2q3']

class OutroPage(Page):
    pass


page_sequence = [IntroPage,
                 _01_Assets,
                 _02_Trading,
                 _03_BorrowingCash,
                 _04_ShortingStock,
                 _05_MarketRestrictions_1,
                 _06_MarketRestrictions_2,
                 _07_MarketPeriod,
                 Quiz01,
                 _08_AutoBuyIn,
                 _09_AutoSellOff,
                 _10_Bankruptcy,
                 _11_MarketPeriod_2,
                 _12_MarketPage,
                 _13_ForecastingPage,
                 _14_PeriodSummary,
                 _15_EndOfMarket,
                 Quiz02,
                 OutroPage]
