import math
import random
from collections import defaultdict

from rounds.call_market import CallMarket
from .models import *
import common.SessionConfigFunctions as scf
from common.ParticipantFuctions import generate_participant_ids


class Constants(BaseConstants):
    name_in_url = 'rounds'
    players_per_group = None
    num_rounds = 3


# assign treatments
def creating_session(subsession):
    # only set up endowments in the first round
    if subsession.round_number != 1:
        return

    generate_participant_ids(subsession)
    session = subsession.session

    # Assemble config params regarding endowments
    cash_control = session.config['cash_endowment_control']
    shares_control = session.config['shares_endowment_control']
    cash_treatment = session.config['cash_endowment_treatment']
    shares_treatment = session.config['shares_endowment_treatment']

    endowments = [{'cash': cash_control, 'shares': shares_control},
                  {'cash': cash_treatment, 'shares': shares_treatment}]

    if 'treated_ids' in session.config:
        treated_ids = [int(x) for x in session.config['treated_ids'].split()]
        modulus = len(treated_ids)
        for group in subsession.get_groups():

            # Make initial endowments to all players in the group
            for _idx, player in enumerate(group.get_players()):
                idx = _idx % modulus
                endowment_idx = treated_ids[idx]
                print("assigning endowments: ", player.id_in_group, " IS Treatment:", endowment_idx)
                endow = endowments[endowment_idx]
                player.cash = endow['cash']
                player.shares = endow['shares']

    else:
        # randomize to treatments
        fraction = session.config['fraction_of_short_starts']
        for group in subsession.get_groups():
            cnt = len(group.get_players())
            num_treatments = math.floor(cnt * fraction)
            num_controls = cnt - num_treatments
            type_assignments = ([0] * num_controls) + ([1] * num_treatments)
            random.shuffle(type_assignments)

            for idx, player in enumerate(group.get_players()):
                endow = endowments[type_assignments[idx]]
                player.cash = endow['cash']
                player.shares = endow['shares']


def get_js_vars_not_current(player: Player):
    return get_js_vars(player, include_current=False)


def get_js_vars(player: Player, include_current=True):
    # Price History
    group = player.group
    if include_current:
        # TODO: Try doing this with player.round_number
        groups = list(filter(lambda g: g.field_maybe_none('price') is not None, group.in_all_rounds()))
    else:
        groups = group.in_previous_rounds()

    init_price = scf.get_init_price(player)

    if scf.is_random_hist(player):
        show_rounds = 2 * Constants.num_rounds // 3
        prices = random.choices(range(2500, 3200), k=show_rounds) + [init_price]
        volumes = random.choices(range(0, 11), k=show_rounds) + [4]
    else:
        prices = [init_price] + [g.price for g in groups]
        volumes = [0] + [g.volume for g in groups]

    # Error Codes
    error_codes = {e.value: e.to_dict() for e in OrderErrorCode}

    return dict(
        labels=list(range(0, Constants.num_rounds + 1)),
        price_data=prices,
        volume_data=volumes,
        num_periods=Constants.num_rounds,
        error_codes=error_codes
    )


#########################
# LIVE PAGES FUNCTIONS
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


def market_page_live_method(player, d):
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


def standard_vars_for_template(player: Player):
    return scf.ensure_config(player)


def get_messages(player: Player):
    ret = []
    is_short = player.is_short()
    is_debt = player.is_debt()
    is_bankrupt = player.is_bankrupt()
    margin_target_ratio = scf.get_margin_target_ratio(player)
    margin_ratio = scf.get_margin_ratio(player)

    price = player.group.get_last_period_price()
    personal_stock_margin = player.get_personal_stock_margin(price)
    personal_cash_margin = player.get_personal_cash_margin(price)
    round_number = player.round_number

    # Current Market Price:
    if scf.get_float_ratio_cap(player):
        short_float_ratio = player.group.short / player.group.float
        ret.append(dict(class_attr="",
                        msg=f"""
                            <span class="left-side">Current Market Price: <span class="bold-text"> 
                            {price}</span></span>
                            <span class="right-side">Percent of Float Shorted: 
                            <span class="bold-text">{short_float_ratio:.0%}</span></span> 
                        """))
    else:
        ret.append(dict(class_attr="",
                        msg=f"""Current Market Price: <span class="bold-text"> {price}"""))

    # Messages / Warning for short position
    if is_short and not is_bankrupt:
        delay = player.periods_until_auto_buy
        class_attr, msg = get_short_message(margin_ratio, margin_target_ratio,
                                            personal_stock_margin, delay, round_number)
        if msg:
            ret.append(dict(class_attr=class_attr, msg=msg))

    # Messages / Warning for negative cash holding
    if is_debt and not is_bankrupt:
        delay = player.periods_until_auto_sell
        class_attr, msg = get_debt_message(margin_ratio, margin_target_ratio,
                                           personal_cash_margin, delay, round_number)
        if msg:
            ret.append(dict(class_attr=class_attr, msg=msg))

    # Bankrupt
    if is_bankrupt:
        ret.append(dict(class_attr="alert-danger",
                        msg="""You are now bankrupt.  Please wait until the end of the market experiment
                         to take the final survey."""))
    return ret


def get_msg_which(delay, round_number):
    if delay == 0:
        which = 'this period'
    elif delay == 1:
        which = f'next period (Period {round_number + 1})'
    else:
        which = "a future period"
    return which


# noinspection DuplicatedCode
def get_debt_message(margin_ratio, margin_target_ratio, personal_cash_margin, delay, round_number):
    # Determine margin sell messages
    msg = None
    class_attr = None

    if personal_cash_margin > margin_target_ratio:
        class_attr = ""
        msg = f"""CASH Margin: <span class="bold-text">{personal_cash_margin:.0%}</span>"""

    elif margin_ratio < personal_cash_margin <= margin_target_ratio:
        class_attr = "alert-warning"
        msg = f"""<p>Warning:  CASH Margin: <span class="bold-text"> {personal_cash_margin:.0%} </span></p>
                        <p> Your CASH margin is getting close to the minimum requirement of {margin_ratio:.0%}.
                        This most likely happened because the value of your STOCK has decreased.  If your
                        CASH margin becomes {margin_ratio:.0%} or lower, the system will sell off your STOCK to
                        satisfy the margin requirement.</p>
                        """

    elif personal_cash_margin <= margin_ratio:
        # Skip if last period and sell is next period
        if round_number == Constants.num_rounds and delay > 0:
            return None, None

        which = get_msg_which(delay, round_number)
        class_attr = "alert-danger"
        msg = f"""<p>Warning:  CASH Margin: <span class="bold-text"> {personal_cash_margin:.0%} </span></p>
                        <p>You are advised to sell some of your STOCK to raise this margin in order to avoid an
                         automatic sell off.</p>                     
                        <p>An automatic sell-off will be generated at the end of {which} if your CASH margin
                         is still less than or equal to <span class="bold-text">{margin_ratio:.0%}</span></p>"""

    return class_attr, msg


# noinspection DuplicatedCode
def get_short_message(margin_ratio, margin_target_ratio, personal_stock_margin, delay, round_number):
    msg = None
    class_attr = None

    # Determine short position messages
    # Normal condition
    if personal_stock_margin > margin_target_ratio:
        class_attr = ""
        msg = f"""STOCK Margin: <span class="bold-text">{personal_stock_margin:.0%}</span>"""

    elif margin_ratio < personal_stock_margin <= margin_target_ratio:
        class_attr = "alert-warning"
        msg = f"""<p>Warning:  STOCK Margin: <span class="bold-text"> {personal_stock_margin:.0%} </span></p>
                            <p> Your STOCK margin is getting close to the minimum requirement of {margin_ratio:.0%}.
                            This most likely happened because the value of your shorted STOCK has increased.  If your
                            STOCK margin becomes {margin_ratio:.0%} or lower, the system will purchase STOCK on your
                            behalf to satisfy the margin requirement.</p>
                            """

    elif personal_stock_margin <= margin_ratio:
        # Skip if last period and buy is next period
        if round_number == Constants.num_rounds and delay > 0:
            return None, None

        which = get_msg_which(delay, round_number)
        class_attr = "alert-danger"
        msg = f"""<p>Warning: STOCK Margin: <span class="bold-text"> {personal_stock_margin:.0%} </span></p>
                        <p>You are advised to purchase STOCK to raise this margin in order to avoid an
                         automatic buy-in.</p>                     
                        <p>An automatic purchase will be made on your behalf at the end of {which} if your 
                        STOCK margin is still less than or equal to 
                        <span class="bold-text">{margin_ratio:.0%}</span></p>"""

    return class_attr, msg


def vars_for_market_template(player: Player):
    ret = standard_vars_for_template(player)
    ret['messages'] = get_messages(player)
    ret['is_practice'] = False
    return ret


def vars_for_forecast_template(player: Player):
    ret = standard_vars_for_template(player)
    round_number = player.round_number
    include_f1 = round_number < Constants.num_rounds
    include_f2 = round_number < Constants.num_rounds - 1

    ret['period_f1_prompt'] = "What do you think the market price will be in period {}?".format(round_number + 1)
    ret['period_f2_prompt'] = "What do you think the market price will be in period {}?".format(round_number + 2)
    ret['include_f1'] = include_f1
    ret['include_f2'] = include_f2
    return ret


def vars_for_round_results_template(player: Player):
    ret = standard_vars_for_template(player)

    filled_amount = abs(player.shares_transacted)
    orders = get_orders_for_player(player)

    # All transaction types should be the same for a given player
    trans_type = 0
    if filled_amount > 0:
        # get the order type
        o_types = list(set(o.order_type for o in orders if o.quantity_final > 0))
        print(orders)
        print(o_types)

        if len(o_types) != 1:
            trans_type = 0
        else:
            trans_type = o_types[0]

    ret['filled_amount'] = filled_amount
    ret['trans_type'] = trans_type
    ret['trans_cost'] = filled_amount * player.group.price

    return ret


def pre_round_tasks(group: Group):
    # Determine auto transaction statuses
    # And copy previous round results to the current player object
    for p in group.get_players():
        # Copy results from the previous player
        p.copy_results_from_previous_round()

        # update margin violations
        p.determine_auto_trans_status()

    # Calculate float the total shorts
    group.float = sum(p.shares for p in group.get_players())
    group.short = abs(sum(p.shares for p in group.get_players() if p.shares < 0))


#######################################
# CALCULATE MARKET
def calculate_market(group: Group):
    cm = CallMarket(group)
    cm.calculate_market()

    for p in group.get_players():
        # Process current round forecasts
        p.determine_forecast_reward(group.price)


#######################################
# CHOICES FOR the drop-downs on the forecasting page
def get_forecasters_choices(player: Player, attr):
    current_mp = player.group.get_last_period_price()
    setattr(player, attr, current_mp)
    step = Currency(500)
    current_mp_nearest_step = (current_mp // step) * step
    num_choices = 20

    # choices below
    below_start = current_mp_nearest_step - num_choices * step
    working_price = max(Currency(0), below_start)
    choices_below = []
    while working_price < current_mp:
        choices_below.append(working_price)
        working_price += step

    # choices_above
    above_stop = current_mp_nearest_step + num_choices * step
    working_price = current_mp_nearest_step + step
    choices_above = []
    while working_price <= above_stop:
        choices_above.append(working_price)
        working_price += step

    return choices_below + [current_mp] + choices_above


def f0_choices(player: Player):
    return get_forecasters_choices(player, 'f0')


def f1_choices(player: Player):
    return get_forecasters_choices(player, 'f1')


def f2_choices(player: Player):
    return get_forecasters_choices(player, 'f2')


def only_show_for_rounds_app(player: Player):
    return scf.get_session_name(player) in ['rounds', 'rounds_sell_off']


############
# PAGES
##########

class PreMarketWait(WaitPage):
    body_text = "Waiting for the experiment to begin"
    pass

    after_all_players_arrive = pre_round_tasks


class Market(Page):
    get_timeout_seconds = scf.get_market_time
    form_model = 'player'
    form_fields = ['type', 'price', 'quantity']

    # method bindings
    js_vars = get_js_vars
    vars_for_template = vars_for_market_template
    live_method = market_page_live_method


class ForecastPage(Page):
    form_model = 'player'

    js_vars = get_js_vars_not_current
    vars_for_template = vars_for_forecast_template
    is_displayed = only_show_for_rounds_app

    @staticmethod
    def get_form_fields(player):
        round_number = player.round_number
        if round_number == Constants.num_rounds:
            return ['f0']
        elif round_number == Constants.num_rounds - 1:
            return ['f0', 'f1']
        else:
            return ['f0', 'f1', 'f2']


class MarketWaitPage(WaitPage):
    after_all_players_arrive = calculate_market


# TODO: Make this page say something about bankruptcy.
class RoundResultsPage(Page):
    form_model = 'player'
    is_displayed = only_show_for_rounds_app
    js_vars = get_js_vars
    vars_for_template = vars_for_round_results_template

    @staticmethod
    def app_after_this_page(player: Player, upcoming_apps):
        if not upcoming_apps or len(upcoming_apps) == 0:
            return None

        if player.is_bankrupt():
            return upcoming_apps[0]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.is_bankrupt():
            return

        if player.round_number != Constants.num_rounds:
            return

        participant = player.participant
        stock_value = player.shares_result * scf.get_fundamental_value(player)
        total_equity = stock_value + player.cash_result
        participant.payoff = max(total_equity, 0)


class FinalResultsPage(Page):
    js_vars = get_js_vars
    form_model = 'player'

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player: Player):
        participant = player.participant
        session = player.session
        return {'bonus_rwc': participant.payoff.to_real_world_currency(session),
                'total_pay': participant.payoff_plus_participation_fee()}


page_sequence = [PreMarketWait, Market, ForecastPage, MarketWaitPage, RoundResultsPage, FinalResultsPage]
