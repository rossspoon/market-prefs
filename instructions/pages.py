import inspect
import sys
from otree.api import Currency as c, currency_range

import rounds
from ._builtin import Page, WaitPage
from .models import  Player
import common.SessionConfigFunctions as scf
import numpy as np

SK_08_example_cash = '_08_example_cash'
SK_08_example_short = '_08_example_short'


def vars_for_temp_common(player: Player):
    ret = scf.ensure_config(player)

    margin_ratio = scf.get_margin_ratio(player)
    marg_ratio_pct = scf.get_margin_ratio(player, wnp=True)
    marg_target_rate_pct = scf.get_margin_target_ratio(player, wnp=True)
    margin_premium_pct = scf.get_margin_premium(player, wnp=True)

    ret['interest_rate_pct'] = scf.as_wnp(scf.get_interest_rate(player))
    ret['marg_ratio'] = margin_ratio
    ret['marg_ratio_pct'] = marg_ratio_pct
    ret['marg_target_rat_pct'] = marg_target_rate_pct
    ret['margin_premium_pct'] = margin_premium_pct
    ret['num_rounds'] = rounds.Constants.num_rounds
    ret['part_fee_whole_num'] = int(ret['participation_fee'])

    return ret


def vars_for_08_template(player: Player):
    ret = vars_for_temp_common(player)

    # Determine values used in the example
    cash = scf.get_item_as_int(ret, SK_08_example_cash)
    shares = scf.get_item_as_int(ret, SK_08_example_short)
    ratio = scf.get_margin_ratio(player)
    margin = cash * ratio
    target_value = margin + 2
    price = int(target_value // 2)
    pos_value = int(price * shares)

    ret['cash'] = cash
    ret['shares'] = shares
    ret['price'] = price
    ret['value'] = pos_value
    return ret


def vars_for_15_template(player: Player):
    ret = vars_for_temp_common(player)
    ret['fund_value'] = scf.get_fundamental_value(player)
    ret['conversion'] = int(ret['real_world_currency_per_point'])
    return ret


class IntroPage(Page):
    vars_for_template = vars_for_temp_common


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
    vars_for_template = vars_for_08_template


class _09_AutoSellOff(Page):
    vars_for_template = vars_for_temp_common


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
    vars_for_template = vars_for_15_template


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
