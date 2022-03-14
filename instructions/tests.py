from otree.api import SubmissionMustFail

from ._builtin import Bot
from .pages import _01_Assets, _02_Trading, _03_BorrowingCash, _04_ShortingStock, _05_MarketRestrictions_1, \
    _06_MarketRestrictions_2, _06_MarketRestrictions_3, _07_MarketPeriod, _08_Equity, _09_AutoTransactions, \
    _10_Bankruptcy, _11_MarketPeriod_2, _12_MarketPage, _13_ForecastingPage, _14_PeriodSummary, _15_EndOfMarket, \
    IntroPage, Quiz01, Quiz02, OutroPage


class PlayerBot(Bot):
    def play_round(self):
        yield IntroPage
        yield _01_Assets
        yield _02_Trading
        yield _03_BorrowingCash
        yield _04_ShortingStock
        yield _05_MarketRestrictions_1
        yield _06_MarketRestrictions_2
        yield _06_MarketRestrictions_3
        yield _07_MarketPeriod
        yield SubmissionMustFail(Quiz01)
        yield Quiz01
        yield _08_Equity
        yield _09_AutoTransactions
        yield _10_Bankruptcy
        yield _11_MarketPeriod_2
        yield _12_MarketPage
        yield _13_ForecastingPage
        yield _14_PeriodSummary
        yield _15_EndOfMarket
        yield SubmissionMustFail(Quiz02)
        yield Quiz02
        yield OutroPage
