import rounds
from common.ParticipantFuctions import generate_participant_ids
from practice.models import *
from rounds import OrderType
from rounds.data_structs import DataForOrder, DataForPlayer

doc = """
Practice Rounds
"""


class C(BaseConstants):
    NAME_IN_URL = 'practice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3
    SHORT = 5
    FLOAT = 10


prices = [-1, 30.00, 25.00, 14.00]
volumes = [-1, 12, 18, 8]
dividends = [-1, 0.40, 1.00, 0.40]


def creating_session(subsession):
    round_number = subsession.round_number

    # Stuff for all rounds
    for g in subsession.get_groups():
        g.float = C.FLOAT
        g.short = C.SHORT
        g.price = prices[round_number]
        g.volume = volumes[round_number]
        g.dividend = dividends[round_number]

    # only set up endowments in the first round
    if round_number != 1:
        return

    generate_participant_ids(subsession)
    for p in subsession.get_players():
        p.cash = 100
        p.shares = 6


def practice_market_page_live_method(player, d):
    return rounds.market_page_live_method(player, d, o_cls=Order)


def practice_market_variables(player):
    ret = rounds.vars_for_market_template(player)
    ret['short'] = C.SHORT
    return ret


def practice_forecast_page_live_method(player, d):
    return rounds.forecast_page_live_method(player, d, o_cls=Order)


def practice_forecast_variables(player):
    ret = rounds.vars_for_forecast_template(player)
    ret['short'] = C.SHORT
    return ret


def practice_results_page_live_method(player, d):
    return rounds.result_page_live_method(player, d, o_cls=Order)


def practice_results_variables(player):
    ret = rounds.vars_for_round_results_template(player)
    ret['short'] = C.SHORT
    return ret


def is_last_round(player: Player):
    return player.round_number == C.NUM_ROUNDS


# noinspection PyUnusedLocal
def forecast_before_next_page(player: Player, timeout_happened):
    g = player.group  # price, volume, and dividend are already set on the group

    orders = [DataForOrder(o) for o in Order.filter(player=player)]
    # cap orders
    short_lim = C.FLOAT
    short = C.SHORT
    supply = sum([o.quantity for o in orders if o.order_type == 1])
    shorting_this_round = max(supply - max(player.shares, 0), 0)
    if short + shorting_this_round > short_lim:
        cap_amt = short + shorting_this_round - short_lim
        for o in sorted(orders, key=lambda x: x.price):
            if o.quantity <= cap_amt:
                cap_amt -= o.quantity
                o.original_quantity = o.quantity
                o.quantity = 0
            else:
                o.original_quantity = o.quantity
                o.quantity = o.quantity - cap_amt
                cap_amt = 0

    # "fill" orders
    sell_fill_amt = 2
    buy_fill_amt = False
    for o in filter(lambda x: x.quantity > 0, orders):
        if o.order_type == OrderType.BID.value and o.price >= g.price:
            o.quantity_final = min(buy_fill_amt, o.quantity)
            buy_fill_amt = 0
        elif o.order_type == OrderType.OFFER.value and o.price <= g.price:
            o.quantity_final = min(sell_fill_amt, o.quantity)
            sell_fill_amt = 0

    d4p = DataForPlayer(player)
    d4p.get_new_player_position(orders, g.dividend, 0.05, g.price)
    d4p.update_player()
    for o in orders:
        o.update_order()

    player.determine_forecast_reward(g.price)


# PAGES
class PracticeMarketPage(Page):
    template_name = 'rounds/Market.html'
    timer_text = 'Time Left:'
    form_model = Player
    form_fields = ['type', 'price', 'quantity']
    get_timeout_seconds = scf.get_market_time

    # method bindings
    js_vars = rounds.get_js_vars
    live_method = practice_market_page_live_method
    vars_for_template = practice_market_variables


class PracticeForecastPage(Page):
    template_name = 'rounds/Market.html'
    timer_text = 'Time Left:'
    form_fields = ['f0']
    form_model = 'player'
    get_timeout_seconds = scf.get_forecast_time
    js_vars = rounds.get_js_vars_forcast_page
    live_method = practice_forecast_page_live_method
    vars_for_template = practice_forecast_variables
    before_next_page = forecast_before_next_page


class PracticeRoundResultsPage(Page):
    template_name = 'rounds/Market.html'
    timer_text = 'Time Left:'
    form_model = 'player'
    js_vars = rounds.get_js_vars_round_results
    get_timeout_seconds = scf.get_summary_time
    vars_for_template = practice_results_variables
    live_method = practice_results_page_live_method

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        next_player = player.in_round_or_null(player.round_number + 1)
        if next_player:
            next_player.shares = player.shares_result
            next_player.cash = player.cash_result


class PracticeEndPage(Page):
    timeout_seconds = 120
    is_displayed = is_last_round


page_sequence = [PracticeMarketPage, PracticeForecastPage, PracticeRoundResultsPage, PracticeEndPage]
