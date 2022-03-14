from collections import defaultdict

import rounds
from common.ParticipantFuctions import generate_participant_ids
from practice.models import *
from rounds import OrderType, OrderErrorCode
from rounds.data_structs import DataForOrder, DataForPlayer

doc = """
Practice Rounds
"""


class C(BaseConstants):
    NAME_IN_URL = 'practice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3


#########################
# LIVE PAGES FUNCTIONS
# noinspection DuplicatedCode
def is_order_valid(player: Player, data):
    o_type = data['type']
    o_price = data['price']
    o_quant = data['quantity']

    error_code = 0

    # We'll need to check this order against all other outstanding orders
    # And categorize them by type
    orders = get_orders_for_player(player)
    orders_cat = defaultdict(list)
    for o in orders:
        orders_cat[o.order_type].append(o)

    # price tests
    if not o_price.lstrip('-').isnumeric():
        error_code = OrderErrorCode.PRICE_NOT_NUM.combine(error_code)
    elif int(o_price) <= 0:
        error_code = OrderErrorCode.PRICE_NEGATIVE.combine(error_code)

    # quant tests
    if not o_quant.lstrip('-').isnumeric():
        error_code = OrderErrorCode.QUANT_NOT_NUM.combine(error_code)
    elif int(o_quant) <= 0:
        error_code = OrderErrorCode.QUANT_NEGATIVE.combine(error_code)

    # type tests
    if o_type not in ['-1', '1']:
        error_code = OrderErrorCode.BAD_TYPE.combine(error_code)

    # If this is a bid, then its price must be less than the lowest ask
    min_ask = min([o.price for o in orders_cat[OrderType.OFFER.value]], default=999999999)
    max_bid = max([o.price for o in orders_cat[OrderType.BID.value]], default=-999)

    if o_type == '-1' and float(o_price) >= min_ask:
        error_code = OrderErrorCode.BID_GREATER_THAN_ASK.combine(error_code)

    if o_type == '1' and float(o_price) <= max_bid:
        error_code = OrderErrorCode.ASK_LESS_THAN_BID.combine(error_code)

    return error_code


def process_order_submit(player, data):
    p_id = player.id_in_group

    error_code = is_order_valid(player, data)
    valid = error_code == 0

    if valid:
        o_type = int(data['type'])
        o_price = int(data['price'])
        o_quant = int(data['quantity'])

        o = Order.create(player=player,
                         group=player.group,
                         order_type=o_type,
                         price=o_price,
                         quantity=o_quant,
                         )

        # HACK!!!!  I don't know why this works, but I'm trying to send the id to of the Order object
        # back to browser and that doesn't work unless I make a db query.
        # TODO: May a db.commit()?
        Order.filter(player=player)

        return {p_id: {'func': 'order_confirmed', 'order_id': o.id}}
    else:
        return {p_id: {'func': 'order_rejected', 'error_code': error_code}}


def get_orders_for_player_live(player):
    p_id = player.id_in_group
    orders = [o.to_dict() for o in Order.filter(player=player)]
    return {p_id: dict(func='order_list', orders=orders)}


def get_orders_for_player(player):
    return Order.filter(player=player)


# noinspection PyUnresolvedReferences
def delete_order(player, oid):
    obs = Order.filter(player=player, id=oid)
    for o in obs:
        Order.delete(o)


def practice_market_page_live_method(player, d):
    func = d['func']

    if func == 'submit-order':
        data = d['data']
        return process_order_submit(player, data)

    elif func == 'get_orders_for_player':
        return get_orders_for_player_live(player)

    elif func == 'delete_order':
        delete_order(player, d['oid'])


# END LIVE METHODS
#######################################

prices = [-1, 3000, 2500, 1400]
volumes = [-1, 12, 18, 8]
dividends = [-1, 40, 100, 40]


def creating_session(subsession):
    round_number = subsession.round_number

    # Stuff for all rounds
    for g in subsession.get_groups():
        g.float = 10
        g.short = 5
        g.price = prices[round_number]
        g.volume = volumes[round_number]
        g.dividend = dividends[round_number]

    # only set up endowments in the first round
    if round_number != 1:
        return

    generate_participant_ids(subsession)
    for p in subsession.get_players():
        p.cash = 10000
        p.shares = 2


def f0_choices(player: Player):
    return rounds.get_forecasters_choices(player, 'f0')


def f1_choices(player: Player):
    return rounds.get_forecasters_choices(player, 'f1')


def f2_choices(player: Player):
    return rounds.get_forecasters_choices(player, 'f2')


# PAGES
class PracticeMarketPage(Page):
    template_name = 'rounds/Market.html'
    form_model = Player
    form_fields = ['type', 'price', 'quantity']
    get_timeout_seconds = scf.get_market_time

    # method bindings
    js_vars = rounds.get_js_vars_not_current
    live_method = practice_market_page_live_method

    @staticmethod
    def vars_for_template(player: Player):
        ret = rounds.vars_for_market_template(player)
        ret['is_practice'] = True
        return ret


class PracticeForecastPage(Page):
    template_name = 'rounds/ForecastPage.html'
    form_model = 'player'

    js_vars = rounds.get_js_vars_not_current

    @staticmethod
    def vars_for_template(player: Player):
        return rounds.vars_for_forecast_template(player, num_rounds=C.NUM_ROUNDS)

    @staticmethod
    def get_form_fields(player):
        round_number = player.round_number
        if round_number == C.NUM_ROUNDS:
            return ['f0']
        elif round_number == C.NUM_ROUNDS - 1:
            return ['f0', 'f1']
        else:
            return ['f0', 'f1', 'f2']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        g = player.group  # price, volume, and dividend are already set on the group

        orders = [DataForOrder(o) for o in Order.filter(player=player)]
        # "fill" orders
        for o in orders:
            if o.order_type == OrderType.BID.value and o.price >= g.price:
                o.quantity_final = min(4, o.quantity)
            elif o.order_type == OrderType.OFFER.value and o.price <= g.price:
                o.quantity_final = min(2, o.quantity)

        d4p = DataForPlayer(player)
        d4p.get_new_player_position(orders, g.dividend, 0.05, g.price)
        d4p.update_player()
        for o in orders:
            o.update_order()

        player.determine_forecast_reward(g.price)


class PracticeRoundResultsPage(Page):
    template_name = 'rounds/RoundResultsPage.html'
    form_model = 'player'
    js_vars = rounds.get_js_vars
    vars_for_template = rounds.vars_for_round_results_template

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        next_player = player.in_round_or_null(player.round_number + 1)
        if next_player:
            next_player.shares = player.shares_result
            next_player.cash = player.cash_result


class PracticeEndPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [PracticeMarketPage, PracticeForecastPage, PracticeRoundResultsPage, PracticeEndPage]
