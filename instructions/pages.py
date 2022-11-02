import datetime
import random

from otree.api import cu, WaitPage

import common.SessionConfigFunctions as scf
import practice
import rounds
from common.CommonPges import UpdatedWaitPage
from ._builtin import Page
from .models import Player

SK_08_example_cash = '_08_example_cash'
SK_08_example_short = '_08_example_short'


def vars_for_temp_common(player: Player):
    ret = scf.ensure_config(player)

    margin_ratio = scf.get_margin_ratio(player)
    marg_ratio_pct = scf.get_margin_ratio(player, wnp=True)
    marg_target_rate_pct = scf.get_margin_target_ratio(player, wnp=True)
    margin_premium_pct = scf.get_margin_premium(player, wnp=True)
    forecast_thold = scf.get_forecast_thold(player)
    forecast_reward = scf.get_forecast_reward(player)

    bonus_cap = ret['bonus_cap']
    ret['has_bonus_cap'] = False
    if bonus_cap:
        ret['has_bonus_cap'] = True
        ret['bonus_cap_whole_num'] = int(bonus_cap * ret['real_world_currency_per_point'])

    ret['interest_rate_pct'] = scf.as_wnp(scf.get_interest_rate(player))
    ret['marg_ratio'] = margin_ratio
    ret['marg_ratio_pct'] = marg_ratio_pct
    ret['marg_target_rat_pct'] = marg_target_rate_pct
    ret['margin_premium_pct'] = margin_premium_pct
    ret['num_rounds'] = rounds.Constants.num_rounds
    ret['num_practice_rounds'] = practice.C.NUM_ROUNDS
    ret['part_fee_whole_num'] = int(ret['participation_fee'])
    ret['float_ratio_cap'] = scf.as_wnp(scf.get_float_ratio_cap(player))
    ret['market_time'] = scf.get_market_time(player)
    ret['forecast_thold'] = forecast_thold
    ret['forecast_reward'] = forecast_reward
    ret['is_online'] = scf.is_online(player)
    return ret


def vars_for_market_ins_template(player):
    ret = scf.ensure_config(player)
    ret['interest_pct'] = f"{scf.get_interest_rate(player):.0%}"
    ret['dividends'] = " or ".join(str(d) for d in scf.get_dividend_amounts(player))
    ret['buy_back'] = scf.get_fundamental_value(player)
    ret['round_num'] = 2 * rounds.Constants.num_rounds // 3

    m_time = datetime.timedelta(seconds=scf.get_market_time(player))
    ret['market_time_fmt'] = f"{m_time}"
    ret['market_time'] = scf.get_market_time(player)

    f_time = datetime.timedelta(seconds=scf.get_forecast_time(player))
    ret['forecast_time_fmt'] = f"{f_time}"
    ret['forecast_time'] = scf.get_forecast_time(player)

    r_time = datetime.timedelta(seconds=scf.get_summary_time(player))
    ret['results_time_fmt'] = f"{r_time}"
    ret['results_time'] = scf.get_summary_time(player)

    ret['num_rounds'] = rounds.Constants.num_rounds
    short_cap_exist = scf.get_float_ratio_cap(player) is not None
    ret['short_cap_exist'] = short_cap_exist
    ret['short_cap'] = f"{scf.get_float_ratio_cap(player):.0%}" if short_cap_exist else ''

    return ret


def js_vars_for_market_ins(player):
    show_rounds = 2 * rounds.Constants.num_rounds // 3
    prices = [14] + random.choices(range(15, 20), k=show_rounds)
    volumes = [0] + random.choices(range(0, 11), k=show_rounds)

    return dict(labels=list(range(0, rounds.Constants.num_rounds + 1)),
                price_data=prices,
                volume_data=volumes,
                num_periods=rounds.Constants.num_rounds,
                )


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

    conversion_rate = ret['real_world_currency_per_point']
    conversion = 0
    if conversion_rate:
        conversion = int(1 / ret['real_world_currency_per_point'])

    ret['fund_value'] = scf.get_fundamental_value(player)
    ret['conversion'] = f"{conversion:,}"
    return ret


class IntroPage(Page):
    vars_for_template = vars_for_temp_common
    # timeout_seconds = 120
    pass


class _01_Assets(Page):
    # timeout_seconds = 120
    pass

class _02_Trading(Page):
    # timeout_seconds = 120
    pass


class _03_BorrowingCash(Page):
    vars_for_template = vars_for_temp_common
    # timeout_seconds = 180
    pass


class _04_ShortingStock(Page):
    vars_for_template = vars_for_temp_common
    # timeout_seconds = 180
    pass


class _05_MarketRestrictions_1(Page):
    # timeout_seconds = 180
    pass


class _06_MarketRestrictions_2(Page):
    # timeout_seconds = 180
    pass


class _06_MarketRestrictions_3(Page):
    def is_displayed(self):
        return scf.get_float_ratio_cap(self.player) is not None

    vars_for_template = vars_for_temp_common
    # timeout_seconds = 180


class _07_MarketPeriod(Page):
    vars_for_template = vars_for_temp_common
    # timeout_seconds = 180
    pass

class _08_Equity(Page):
    vars_for_template = vars_for_temp_common
    # timeout_seconds = 180
    pass

class _09_AutoTransactions(Page):
    vars_for_template = vars_for_temp_common
    # timeout_seconds = 180


class _10_Bankruptcy(Page):
    # timeout_seconds = 180
    pass


class _11_MarketPeriod_2(Page):
    # timeout_seconds = 180
    pass

class _12_MarketPage2(Page):
    template_name = "instructions/Market_ins.html"
    vars_for_template = vars_for_market_ins_template
    js_vars = js_vars_for_market_ins
    # timeout_seconds = 420


class _13_ForecastPage2(Page):
    template_name = "instructions/Forecast_ins.html"
    vars_for_template = vars_for_market_ins_template
    js_vars = js_vars_for_market_ins
    # timeout_seconds = 300


class _14_PeriodSummary2(Page):
    template_name = "instructions/Summary_ins.html"
    vars_for_template = vars_for_market_ins_template
    js_vars = js_vars_for_market_ins
    # timeout_seconds = 300


class _15_EndOfMarket(Page):
    vars_for_template = vars_for_15_template
    # timeout_seconds = 180


class Quiz02(Page):
    template_name = 'instructions/Quiz_template.html'
    form_fields = ['quiz_1', 'quiz_2', 'quiz_3', 'quiz_4']
    form_model = Player
    # timeout_seconds = 300


    def before_next_page(self):
        # Grade the quiz
        player = self.player
        fundamental = cu(scf.get_fundamental_value(player))

        ans1 = player.field_maybe_none('quiz_1')
        ans2 = player.field_maybe_none('quiz_2')
        ans3 = player.field_maybe_none('quiz_3')
        ans4 = player.field_maybe_none('quiz_4')

        player.quiz_1_score = ans1 is not None and not ans1
        player.quiz_2_score = ans2 == fundamental
        player.quiz_3_score = ans3 == 56
        player.quiz_4_score = ans4 == 110


class Quiz02Results(Page):
    template_name = 'instructions/QuizResults_template.html'
    form_fields = ['quiz_1', 'quiz_2', 'quiz_3', 'quiz_4']
    form_model = Player
    # timeout_seconds = 120

    def get_messages(self):
        player = self.player
        ret = {}
        fundamental = cu(scf.get_fundamental_value(player))

        ret['quiz_1'] = "" if player.quiz_1_score else "All BUY prices must all be less than your SELL prices."

        ret['quiz_2'] = "" if player.quiz_2_score else f'The system will buy back shares of STOCK at a price of {fundamental}.'

        ret['quiz_3'] = "" if player.quiz_3_score else f'At the end of the experiment, all STOCK is bought back at a price of {fundamental}.' \
                            f'You will receive 4 x {fundamental} = {cu(4 * fundamental)}.'

        ret['quiz_4'] = "" if player.quiz_4_score else f'You will receive 5% on you CASH or 5.00 points, and 1.00 point for each of your' \
                            f'shares.  Your final CASH position will be: 100.00 + 5.00 + (1.00 x 5) = 110.00 points.'

        return ret

    def js_vars(self):
        player = self.player
        success = False

        fields_to_check = {f: f"{f}_score" for f in self.form_fields}
        scored = {f: bool(player.field_maybe_none(s)) for f, s in fields_to_check.items()}
        question_class = {n: 'correct' if b else 'wrong' for n, b in scored.items()}

        # This variable will signal the js to turn the error message green.
        success = all(scored.values())

        attempted = True

        return {'q_class': question_class,
                'success': success,
                'attempted': attempted,
                'errors': self.get_messages()}


class OutroPage(Page):
    vars_for_template = vars_for_temp_common
    # timeout_seconds = 120
    pass

class InstWaitPage(UpdatedWaitPage):
    body_text = "Please wait for the other participants to progress through the instructions."


page_sequence = [IntroPage,
                 _02_Trading,
                 InstWaitPage,
                 _03_BorrowingCash,
                 _04_ShortingStock,
                 _15_EndOfMarket,
                 InstWaitPage,
                 _12_MarketPage2,
                 InstWaitPage,
                 _13_ForecastPage2,
                 InstWaitPage,
                 _14_PeriodSummary2,
                 InstWaitPage,
                 _06_MarketRestrictions_2,
                 _06_MarketRestrictions_3,
                 InstWaitPage,
                 _09_AutoTransactions,
                 _10_Bankruptcy,
                 Quiz02,
                 Quiz02Results,
                 OutroPage,
                 InstWaitPage,
                 ]
