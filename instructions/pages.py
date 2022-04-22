import datetime
import random

from otree.api import cu

import common.SessionConfigFunctions as scf
import practice
import rounds
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


class _01_Assets(Page):
    pass


class _02_Trading(Page):
    pass


class _03_BorrowingCash(Page):
    vars_for_template = vars_for_temp_common


class _04_ShortingStock(Page):
    vars_for_template = vars_for_temp_common


class _05_MarketRestrictions_1(Page):
    pass


class _06_MarketRestrictions_2(Page):
    pass


class _06_MarketRestrictions_3(Page):
    def is_displayed(self):
        return scf.get_float_ratio_cap(self.player) is not None

    vars_for_template = vars_for_temp_common


class _07_MarketPeriod(Page):
    vars_for_template = vars_for_temp_common


class _08_Equity(Page):
    vars_for_template = vars_for_temp_common


class _09_AutoTransactions(Page):
    vars_for_template = vars_for_temp_common


class _10_Bankruptcy(Page):
    pass


class _11_MarketPeriod_2(Page):
    pass


class _12_MarketPage(Page):
    vars_for_template = vars_for_temp_common


class _12_MarketPage2(Page):
    template_name = "instructions/Market_ins.html"
    vars_for_template = vars_for_market_ins_template
    js_vars = js_vars_for_market_ins


class _13_ForecastingPage(Page):
    vars_for_template = vars_for_temp_common


class _13_ForecastPage2(Page):
    template_name = "instructions/Forecast_ins.html"
    vars_for_template = vars_for_market_ins_template
    js_vars = js_vars_for_market_ins


class _14_PeriodSummary(Page):
    pass


class _14_PeriodSummary2(Page):
    template_name = "instructions/Summary_ins.html"
    vars_for_template = vars_for_market_ins_template
    js_vars = js_vars_for_market_ins


class _15_EndOfMarket(Page):
    vars_for_template = vars_for_15_template


class QuizPage(Page):
    template_name = 'instructions/Quiz_template.html'
    form_model = Player
    attempted_field = ''

    def grade_quiz(self, values):
        raise NotImplementedError("Please Implement this method")

    def js_vars(self):
        question_class = {name: 'normal' for name in self.form_fields}
        success = False
        attempted = False

        # if the page has already been submitted, we now have a form object,
        # and it has been 'graded'.  determine the check/ex class of each question.
        if getattr(self.player, self.attempted_field):
            correct = {f.name: not bool(f.errors) for f in self.form}
            question_class = {n: 'correct' if b else 'wrong' for n, b in correct.items()}

            # This variable will signal the js to turn the error message green.
            success = all(correct.values())

            attempted = True

        return {'q_class': question_class,
                'success': success,
                'attempted': attempted}

    def error_message(self, values):
        player = self.player

        if getattr(player, self.attempted_field):
            return

        ret = self.grade_quiz(values)
        setattr(player, self.attempted_field, True)

        # if errors are present the truthiness of ret will be True
        if ret:
            num_wrong = len(ret)
            s = '' if num_wrong == 1 else 's'
            self.form.non_field_error = f"You missed {num_wrong} question{s}. &nbsp;&nbsp Please take note of the " \
                                        f"correct answers and click ""Next"" to continue."
        else:
            self.form.non_field_error = "You answered all questions correctly. &nbsp;&nbsp Please click Next to " \
                                        "continue. "
        return ret


class Quiz01(QuizPage):
    form_fields = ['qz1q1', 'qz1q2', 'qz1q3', 'qz1q4']
    attempted_field = 'qz1_attempted'

    def grade_quiz(self, values):
        ret = {}

        if values['qz1q1'] != 6:
            ret['qz1q1'] = "You are allowed up to 6 orders per market period."

        if values['qz1q2'] is None or values['qz1q2']:
            ret['qz1q2'] = "All BUY prices must all be less than your SELL prices."

        if not values['qz1q3']:
            ret['qz1q3'] = "When you short the STOCK, dividends  will be deducted from your CASH holdings."

        ir = scf.as_wnp(scf.get_interest_rate(self.player))
        if values['qz1q4'] != ir:
            ret['qz1q4'] = f"Interest on CASH is earned at {ir}."

        return ret


class Quiz02(QuizPage):
    form_fields = ['quiz_1', 'quiz_2', 'quiz_3', 'quiz_4']
    attempted_field = 'qz_attempted'

    def grade_quiz(self, values):
        player = self.player
        ret = {}

        if values['quiz_1'] is None or values['quiz_1']:
            ret['quiz_1'] = "All BUY prices must all be less than your SELL prices."

        fundamental = cu(scf.get_fundamental_value(player))
        if values['quiz_2'] != fundamental:
            ret['quiz_2'] = f'The system will buy back shares of STOCK at a price of {fundamental}.'

        if values['quiz_3'] != 56:
            ret['quiz_3'] = f'At the end of the experiment, all STOCK is bought back at a price of {fundamental}.' \
                           f'You will receive 4 x {fundamental} = {cu(4 * fundamental)}.'

        if values['quiz_4'] != 110:
            ret['quiz_4'] = f'You will receive 5% on you CASH or 5.00 points, and 1.00 point for each of your' \
                           f'shares.  Your final CASH position will be: 100.00 + 5.00 + (1.00 x 5) = 110.00 points.'

        return ret


class OutroPage(Page):
    vars_for_template = vars_for_temp_common


# page_sequence = [IntroPage,
#                  _02_Trading,
#                  _03_BorrowingCash,
#                  _04_ShortingStock,
#                  _15_EndOfMarket,
#                  _12_MarketPage2,
#                  _13_ForecastPage2,
#                  _14_PeriodSummary2,
#                  _06_MarketRestrictions_2,
#                  _06_MarketRestrictions_3,
#                  _09_AutoTransactions,
#                  _10_Bankruptcy,
#                  Quiz02,
#                  OutroPage]
page_sequence = [
                 Quiz02,
                 OutroPage]