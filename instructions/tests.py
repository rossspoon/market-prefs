from otree.api import SubmissionMustFail

import instructions.pages
from ._builtin import Bot
from .pages import _01_Assets, _02_Trading, _03_BorrowingCash, _04_ShortingStock, _05_MarketRestrictions_1, \
    _06_MarketRestrictions_2, _06_MarketRestrictions_3, _07_MarketPeriod, _08_Equity, _09_AutoTransactions, \
    _10_Bankruptcy, _11_MarketPeriod_2, _12_MarketPage, _13_ForecastingPage, _14_PeriodSummary, _15_EndOfMarket, \
    IntroPage, Quiz01, Quiz02, OutroPage


class PlayerBot(Bot):
    def play_round(self):
        for page in instructions.pages.page_sequence:
            if page == Quiz02:
                yield SubmissionMustFail(page)

            yield page
