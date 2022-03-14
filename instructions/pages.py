import common.SessionConfigFunctions as scf
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

    ret['interest_rate_pct'] = scf.as_wnp(scf.get_interest_rate(player))
    ret['marg_ratio'] = margin_ratio
    ret['marg_ratio_pct'] = marg_ratio_pct
    ret['marg_target_rat_pct'] = marg_target_rate_pct
    ret['margin_premium_pct'] = margin_premium_pct
    ret['num_rounds'] = rounds.Constants.num_rounds
    ret['part_fee_whole_num'] = int(ret['participation_fee'])
    ret['bonus_cap_whole_num'] = int(ret['bonus_cap'] / 10000)
    ret['float_ratio_cap'] = scf.as_wnp(scf.get_float_ratio_cap(player))
    ret['market_time'] = scf.get_market_time(player)
    ret['forecast_thold'] = forecast_thold
    ret['forecast_reward'] = forecast_reward

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
    pass


class _04_ShortingStock(Page):
    pass


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


class _13_ForecastingPage(Page):
    vars_for_template = vars_for_temp_common


class _14_PeriodSummary(Page):
    pass


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

        # if the page has already been submitted, we now have a form object,
        # and it has been 'graded'.  determine the check/ex class of each question.
        if getattr(self.player, self.attempted_field):
            correct = {f.name: not bool(f.errors) for f in self.form}
            question_class = {n: 'correct' if b else 'wrong' for n, b in correct.items()}

            # This variable will signal the js to turn the error message green.
            success = all(correct.values())

        return {'q_class': question_class,
                'success': success}

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
            self.form.non_field_error = "Well Done! &nbsp;&nbsp Please click Next to continue."
        return ret


class Quiz01(QuizPage):
    form_fields = ['qz1q1', 'qz1q2', 'qz1q3', 'qz1q4']
    attempted_field = 'qz1_attempted'

    def grade_quiz(self, values):
        ret = {}

        if values['qz1q1'] != 6:
            ret['qz1q1'] = "You are allowed up to 6 orders per market period."

        if values['qz1q2'] is None or values['qz1q2']:
            ret['qz1q2'] = "Your BUY prices must all be less than you SELL prices."

        if not values['qz1q3']:
            ret['qz1q3'] = "When you short the STOCK, dividends  will be deducted from your CASH holdings."

        ir = scf.as_wnp(scf.get_interest_rate(self.player))
        if values['qz1q4'] != ir:
            ret['qz1q4'] = f"Interest on CASH is earned at {ir}."

        return ret


class Quiz02(QuizPage):
    form_fields = ['qz2q1', 'qz2q2', 'qz2q3']
    attempted_field = 'qz2_attempted'

    def grade_quiz(self, values):
        player = self.player
        ret = {}

        fundamental = scf.get_fundamental_value(player)
        if values['qz2q1'] != fundamental:
            ret['qz2q1'] = f'The system will buy back shares of STOCK at a price of {fundamental} points'

        mr = scf.get_margin_ratio(player, wnp=True)
        if values['qz2q2'] != 1:
            ret['qz2q2'] = f'The system will attempt an automatic buy-in when you are currently shorting the STOCK ' \
                           f'and your margin ratio drops below {mr} '

        num = rounds.Constants.num_rounds
        if values['qz2q3'] != num:
            ret['qz2q3'] = f'The market will last for {num} periods'

        return ret


class OutroPage(Page):
    pass


page_sequence = [IntroPage,
                 _01_Assets,
                 _02_Trading,
                 _03_BorrowingCash,
                 _04_ShortingStock,
                 _05_MarketRestrictions_1,
                 _06_MarketRestrictions_2,
                 _06_MarketRestrictions_3,
                 _07_MarketPeriod,
                 Quiz01,
                 _08_Equity,
                 _09_AutoTransactions,
                 _10_Bankruptcy,
                 _11_MarketPeriod_2,
                 _12_MarketPage,
                 _13_ForecastingPage,
                 _14_PeriodSummary,
                 _15_EndOfMarket,
                 Quiz02,
                 OutroPage]
