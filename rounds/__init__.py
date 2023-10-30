import decimal
import random
from collections import defaultdict
from math import ceil
from rounds.call_market import CallMarket
from . import tool_tip
from .models import *
import common.SessionConfigFunctions as scf
from common.ParticipantFuctions import generate_participant_ids, is_button_click
from otree import database
import os

NUM_ROUNDS = os.getenv('SSE_NUM_ROUNDS')


class Constants(BaseConstants):
    name_in_url = 'rounds'
    players_per_group = None
    if NUM_ROUNDS:
        num_rounds = int(NUM_ROUNDS)
    else:
        num_rounds = 50


# assign treatments
def assign_endowments(subsession):
    # only set up endowments in the first round
    if subsession.round_number != 1:
        return

    generate_participant_ids(subsession)

    # Set up endowments.  All endowments are of equivalent value at the
    # fundamental value of the stock
    stock_endowments = scf.get_endow_stocks(subsession)
    worth = scf.get_endow_worth(subsession)
    fund_val = scf.get_fundamental_value(subsession)
    clickers = list(filter(lambda x: is_button_click(x), subsession.get_players()))
    num_click = len(clickers)

    # Remainder - This part is particular to the experiment and based on three possible opening share positions
    remainder = num_click % 3
    whole_quotient = num_click // 3
    stock_for_players = stock_endowments * whole_quotient
    if remainder == 1:
        stock_for_players = stock_for_players + stock_endowments[1:2]
    elif remainder == 2:
        stock_for_players = stock_for_players + [stock_endowments[0], stock_endowments[2]]

    idx = 0
    for p in subsession.get_players():
        shares =  0
        worth_for_player = 0

        if is_button_click(p):
            shares = stock_for_players[idx]
            worth_for_player = worth
            idx += 1

        p.shares = shares
        p.cash = worth_for_player - shares * fund_val


def get_js_vars_forcast_page(player: Player):
    return get_js_vars(player, show_cancel=False, event_type='page_name')


def get_js_vars_round_results(player: Player):
    return get_js_vars(player, include_current=True, show_notes=True, show_cancel=False, event_type='rec_stop')

def get_websockets_vars(player: Player, event_type):
    page_name = player.participant._current_page_name
    return dict(
    page_name = page_name,
    event_type = event_type,
    rnd = player.round_number,
    label = player.participant.label,
    part_code = player.participant.code,
    )

def get_js_vars_fixate(player: Player):
    return get_websockets_vars(player, 'fixate')

def get_js_vars(player: Player, include_current=False, show_notes=False, show_cancel=True, event_type='rec_start'):
    # Price History
    group: Group = player.group
    if include_current:
        # TODO: Try doing this with player.round_number
        groups = list(filter(lambda g: g.field_maybe_none('price') is not None, group.in_all_rounds()))
    else:
        groups = group.in_previous_rounds()

    init_price = scf.get_init_price(player)

    if scf.is_random_hist(player):
        show_rounds = 2 * Constants.num_rounds // 3
        prices = random.choices(range(25, 32), k=show_rounds) + [init_price]
        volumes = random.choices(range(0, 11), k=show_rounds) + [4]
    else:
        prices = [init_price] + [g.price for g in groups]
        volumes = [0] + [g.volume for g in groups]

    # Error Codes
    error_codes = {e.value: e.to_dict() for e in OrderErrorCode}

    market_price = group.price if include_current else group.get_last_period_price()
    mp_str = f"{market_price:.2f}"

    show_next = scf.show_next_button(player)

    ws_vars = get_websockets_vars(player, event_type)
    ret = dict(
        labels=list(range(0, Constants.num_rounds + 1)),
        price_data=prices,
        volume_data=volumes,
        num_periods=Constants.num_rounds,
        error_codes=error_codes,
        show_notes=show_notes,
        show_cancel=show_cancel,
        market_price=market_price,
        market_price_str=mp_str,
        tt=tool_tip.get_tool_tip_data(player),
        show_next=show_next,
    )
    ret.update(ws_vars)
    return ret


#########################
# LIVE PAGES FUNCTIONS
# noinspection DuplicatedCode



def is_order_valid(player, data, orders_by_type):
    """
    Check order form information.  This is both a syntactic and semantic check.
    @param data: Data from the otree live page's packet
    @return: Error Code - 0 if valid
    @return: An OrderType object if valid, None otherwise
    @return: The price as an integer if valid, None otherwise
    @return: The quantity as an integer if valid, None otherwise
    """
    error_code, o_type, price, quant = is_order_form_valid(data)

    # All remaining tests depend on the numeric form data
    if error_code > 0:
        return error_code, o_type, price, quant

    # price tests
    if price <= 0:
        error_code = OrderErrorCode.PRICE_NEGATIVE.combine(error_code)

    # quant tests
    if quant <= 0:
        error_code = OrderErrorCode.QUANT_NEGATIVE.combine(error_code)

    # All remaining tests depend on valid price and quant
    if error_code > 0:
        return error_code, o_type, price, quant

    offers = orders_by_type[OrderType.OFFER]
    bids = orders_by_type[OrderType.BID]

    # If this is a bid, then its price must be less than the lowest ask
    min_ask = min([o.price for o in offers], default=999999999)
    max_bid = max([o.price for o in bids], default=-999)

    if o_type == OrderType.BID and price >= min_ask:
        return OrderErrorCode.BID_GREATER_THAN_ASK.combine(error_code), o_type, price, quant

    if o_type == OrderType.OFFER and price <= max_bid:
        return OrderErrorCode.ASK_LESS_THAN_BID.combine(error_code), o_type, price, quant

    # disallow margin trading and shorting
    if o_type == OrderType.OFFER and is_shorting(player, offers, quant):
        return OrderErrorCode.SHORTING.combine(error_code), o_type, price, quant

    if o_type == OrderType.BID and is_margin(player, bids, quant, price):
        return OrderErrorCode.MARGIN.combine(error_code), o_type, price, quant

    return error_code, o_type, price, quant


def is_order_form_valid(data):
    """
    Syntactic checks of the order form.  Basically test that the price and quant are all
    integer numbers, and that the type is either -1 or 1 (BUY or SELL).
    @param data: Data from the otree live page's packet
    @return: Error Code - 0 if valid
    @return: An OrderType object if valid, None otherwise
    @return: The price as an integer if valid, None otherwise
    @return: The quantity as an integer if valid, None otherwise
    """
    raw_type = data['type']
    raw_price = data['price']
    raw_quant = data['quantity']

    error_code = 0
    more_price_quant_checks = True

    # # Checks for raw length
    # if len(raw_price) > 10:
    #     error_code = OrderErrorCode.PRICE_LEN_RAW.combine(error_code)
    #     more_price_quant_checks = False
    #
    # if len(raw_quant) > 5:
    #     error_code = OrderErrorCode.QUANT_LEN_RAW.combine(error_code)
    #     more_price_quant_checks = False

    price = None
    quant = None
    # Numeric Tests  - Price and Quantity must be numeric
    try:
        price = cu(raw_price)
    except (ValueError, decimal.InvalidOperation):
        error_code = OrderErrorCode.PRICE_NOT_NUM.combine(error_code)

    # if not raw_quant.lstrip('-').isnumeric():
    #     error_code = OrderErrorCode.QUANT_NOT_NUM.combine(error_code)
    # else:
    quant = int(raw_quant)

    # PRICE CEILING
    if price and price >= 10000:
        error_code = OrderErrorCode.PRICE_CEIL.combine(error_code)

    # QUANT CEILING
    if quant and quant >= 100:
         error_code = OrderErrorCode.QUANT_CEIL.combine(error_code)


    # Order type checks
    o_type = None
    if raw_type not in ['SELL', 'BUY']:
        error_code = OrderErrorCode.BAD_TYPE.combine(error_code)
    else:
        t = -1 if raw_type == 'BUY' else 1
        o_type = OrderType(int(t))
    return error_code, o_type, price, quant


def is_shorting(player, offers,  quant):
    outstanding_quant = sum([o.quantity for o in offers])
    return outstanding_quant + quant > player.shares


def is_margin(player, bids, quant, price):
    outstanding_cost = sum([o.quantity * o.price for o in bids])
    return outstanding_cost + quant*price > player.cash


def get_order_warnings(player, o_type, price, quant, orders_by_type):
    warnings = []

    # show a warning if the combined orders can cause a short
    existing_supply = sum((o.quantity for o in orders_by_type[OrderType.OFFER]))
    test_supply = existing_supply + quant if o_type == OrderType.OFFER else existing_supply
    if test_supply > 0 and player.shares < test_supply:
        warnings.append("Note:  Depending on market conditions, your combined SELL orders might result in a short "
                        "STOCK position.")

    existing_cost = sum((o.price * o.quantity for o in orders_by_type[OrderType.BID]))
    order_cost = price * quant
    test_cost = existing_cost + order_cost if o_type == OrderType.BID else existing_cost
    if test_cost > 0 and player.cash < test_cost:
        warnings.append("Note:  Depending on market conditions, your combined BUY orders might require you to borrow "
                        "CASH.")

    return warnings


def get_orders_by_type(existing_orders):
    orders_cat = defaultdict(list)
    for o in existing_orders:
        orders_cat[OrderType(o.order_type)].append(o)
    return orders_cat


def create_order_from_live_submit(player, o_type: OrderType, price, quant, o_cls=Order):
    # TODO:  Does this need to go in a transaction?
    o = o_cls.create(player=player,
                     group=player.group,
                     order_type=o_type.value,
                     price=price,
                     quantity=quant,
                     )

    # Commit the order so that we can get an id.
    database.db.commit()

    return {'func': 'order_confirmed', 'order_id': o.id}


def get_orders_for_player_live(orders, show_notes):
    orders_dicts = [o.to_dict() for o in orders]

    for o in orders_dicts:
        # Format price to two decimals
        o['price'] = f"{o['price']:.2f}"

        o['note'] = '&nbsp;'
        if show_notes:
            quant_orig = o.get('original_quantity')
            quant = o.get('quantity')

            if o.get('is_buy_in'):
                o['note'] = "<span class='auto-order'>Automatic</span>"
            elif quant_orig != 0 and quant == 0:
                o['note'] = "<span class='canceled-order'>Canceled</span>"
            elif quant_orig is not None and quant_orig != quant:
                o['note'] = f"Capped to {quant}"

    return dict(func='order_list', orders=orders_dicts)


# noinspection PyUnresolvedReferences
def delete_order(player, oid, o_cls=Order):
    obs = o_cls.filter(player=player, id=oid)
    for o in obs:
        o_cls.delete(o)


def result_page_live_method(player, d, o_cls=Order):
    return market_page_live_method(player, d, o_cls=o_cls, show_warnings=False, show_notes=True)


def forecast_page_live_method(player, d, o_cls=Order):
    return market_page_live_method(player, d, o_cls=o_cls, show_warnings=False)


def market_page_live_method(player, d, o_cls=Order, show_warnings=True, show_notes=False):
    func = d['func']

    # Do delete first.  it might change the outcome of get_orders_for_player
    if func == 'delete_order':
        delete_order(player, d['oid'], o_cls=o_cls)

    orders_for_player = get_orders_for_player(player, o_cls=o_cls)
    orders_by_type = get_orders_by_type(orders_for_player)
    ret = {}
    this_order_q = 0
    this_order_p = 0
    this_order_t = 'no_order'

    if func == 'submit-order':
        data = d['data']
        error_code, t, p, q = is_order_valid(player, data, orders_by_type)

        if error_code == 0:
            ret.update(create_order_from_live_submit(player, t, p, q, o_cls=o_cls))
            this_order_q = q
            this_order_p = p
            this_order_t = t
        else:
            ret.update({'func': 'order_rejected', 'error_code': error_code})

    elif func == 'get_orders_for_player':
        ret.update(get_orders_for_player_live(orders_for_player, show_notes))

    # generate warnings
    if show_warnings:
        warnings = get_order_warnings(player, this_order_t, this_order_p, this_order_q, orders_by_type)
        ret['warnings'] = warnings

    return {player.id_in_group: ret}


# END LIVE METHODS
#######################################


def get_orders_for_player(player, o_cls=Order):
    return o_cls.filter(player=player)


def standard_vars_for_template(player: Player):
    ret = scf.ensure_config(player)
    marg_req = ret.get(scf.SK_MARGIN_RATIO)
    ret['marg_req_pct'] = f"{marg_req :.0%}"
    ret['margin_buffer_pct'] = f"{1 + marg_req:.0%}"
    ret['for_results'] = False
    ret['cash'] = player.cash
    ret['shares'] = player.shares

    price = player.group.get_last_period_price()
    value_of_stock, equity, debt, limit, close = player.get_holding_details(price)
    ret['stock_val'] = value_of_stock
    ret['vos_neg_cls'] = 'neg-val' if value_of_stock < 0 else ''
    ret['equity'] = equity
    ret['debt'] = debt
    ret['dbt_neg_cls'] = 'neg-val' if debt < 0 else ''
    ret['limit'] = limit
    ret['lim_neg_cls'] = 'neg-val' if limit and limit < 0 else ''
    ret['close_limit'] = close
    ret['is_short'] = player.is_short()
    ret['is_debt'] = player.is_debt()
    ret['market_price'] = price
    ret['interest_pct'] = f"{scf.get_interest_rate(player):.0%}"
    ret['dividends'] = " or ".join(str(d) for d in scf.get_dividend_amounts(player))
    ret['buy_back'] = scf.get_fundamental_value(player)
    ret['short'] = player.group.short

    ret['messages'] = []  # The market page will populate this
    ret['attn_cls'] = ''
    ret['show_pop_up'] = False
    ret['num_rounds_left'] = 99

    return ret


def get_messages(player: Player, template_vars):
    ret = []
    is_short = player.is_short()
    is_debt = player.is_debt()
    is_bankrupt = is_short and is_debt
    limit = template_vars['limit']
    close = template_vars['close_limit']
    debt = template_vars['debt']

    round_number = player.round_number

    # Messages / Warning for short position
    if is_short and not is_bankrupt:
        delay = player.periods_until_auto_buy
        class_attr, msg = get_short_message(limit, close, debt, delay, round_number)
        if msg:
            ret.append(dict(class_attr=class_attr, msg=msg))

    # Messages / Warning for negative cash holding
    if is_debt and not is_bankrupt:
        delay = player.periods_until_auto_sell
        class_attr, msg = get_debt_message(limit, close, debt, delay, round_number)
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
def get_debt_message(limit, close, debt, delay, round_number):
    # Determine margin sell messages
    msg = None
    class_attr = None

    if limit < debt <= close:
        class_attr = "alert-warning"
        msg = f"""<p>Warning:  The the amount of CASH that you have is getting close to your borrowing limit.
                This might have happened because the value of you STOCK holdings has decreased.  You are advised
                to sell STOCK to decrease your debt, to avoid an automatic sell.</p>
                """

    elif debt <= limit:
        # Skip if last period and sell is next period
        if round_number == Constants.num_rounds and delay > 0:
            return None, None

        which = get_msg_which(delay, round_number)
        class_attr = "alert-danger"
        msg = f"""<p>Warning:  You are over your borrowing limit.  You are advised to sell STOCK to raise CASH.</p>                   
                        <p>An automatic sell-off will be generated at the end of {which} if your borrowed CASH 
                        is still over the limit.</p>"""

    return class_attr, msg


# noinspection DuplicatedCode
def get_short_message(limit, close, debt, delay, round_number):
    msg = None
    class_attr = None

    # Determine short position messages
    # Normal condition
    if limit < debt <= close:
        class_attr = "alert-warning"
        msg = f"""<p>Warning:  The the value of you shorted STOCK is getting close to your limit.
                This might have happened because the value of you STOCK price has increased.  You are advised
                to buy STOCK to decrease your debt, to avoid an automatic buy.</p>
                """

    elif debt <= limit:
        # Skip if last period and buy is next period
        if round_number == Constants.num_rounds and delay > 0:
            return None, None

        which = get_msg_which(delay, round_number)
        class_attr = "alert-danger"
        msg = f"""<p>Warning:  You are over your shorting limit.  You are advised to buy STOCK to decrease the value of
                        your short position.</p>                   
                    <p>An automatic buy-in will be generated at the end of {which} if your shorted STOCK value 
                        is still over the limit.</p>"""

    return class_attr, msg


def vars_for_market_template(player: Player):
    ret = standard_vars_for_template(player)
    ret['messages'] = get_messages(player, ret)
    ret['show_pop_up'] = player.round_number > (Constants.num_rounds - 5)
    ret['num_rounds_left'] = Constants.num_rounds - player.round_number + 1
    ret['action_include'] = 'insert_order_grid.html'

    return ret


def vars_for_forecast_template(player: Player):
    ret = standard_vars_for_template(player)
    ret['action_include'] = 'insert_forecast.html'
    return ret


def vars_for_round_results_template(player: Player):
    ret = standard_vars_for_template(player)
    ret['for_results'] = True
    ret['cash'] = player.cash_result
    ret['shares'] = player.shares_result

    price = player.group.price
    value_of_stock, equity, debt, limit, close = player.get_holding_details(price, results=True)
    ret['stock_val'] = value_of_stock
    ret['vos_neg_cls'] = 'neg-val' if value_of_stock < 0 else ''
    ret['equity'] = equity
    ret['debt'] = debt
    ret['dbt_neg_cls'] = 'neg-val' if debt < 0 else ''
    ret['limit'] = limit
    ret['lim_neg_cls'] = 'neg-val' if limit and limit < 0 else ''
    ret['close_limit'] = close
    ret['is_short'] = player.is_short()
    ret['is_debt'] = player.is_debt()
    ret['market_price'] = price

    short = abs(sum([p.shares_result for p in player.group.get_players() if p.shares_result < 0]))
    ret['short'] = short

    filled_amount = abs(player.shares_transacted)
    orders = get_orders_for_player(player)

    # All transaction types should be the same for a given player
    trans_type = 0
    if filled_amount > 0:
        # get the order type
        o_types = list(set(o.order_type for o in orders if o.quantity_final > 0))

        if len(o_types) != 1:
            trans_type = 0
        else:
            trans_type = o_types[0]

    ret['filled_amount'] = filled_amount
    ret['trans_type'] = trans_type
    ret['trans_cost'] = filled_amount * player.group.price
    ret['bankrupt'] = player.is_bankrupt(results=True)
    ret['attn_cls'] = 'attention_slow'
    ret['messages'] = get_round_result_messages(player, ret)
    ret['action_include'] = 'insert_round_results.html'
    return ret


def vars_for_risk_template(player: Player):
    ret = standard_vars_for_template(player)

    ret['s_hi'] = 10.00
    ret['s_lo'] = 8.00
    ret['r_hi'] = 19.25
    ret['r_lo'] = 0.50

    hi_p = random.randint(1,100)
    lo_p = 100 - hi_p

    ret['hi_prob'] = hi_p
    ret['lo_prob'] = lo_p

    return ret


def get_round_result_messages(player: Player, d: dict):
    messages = []


    # Price message
    msg = f"Market price this period: {player.group.price}"
    messages.append(dict(class_attr='result-msg', msg=msg))

    # Volume message
    msg = f"Market volume this period: {player.group.volume} shares"
    messages.append(dict(class_attr='result-msg', msg=msg))

    # Determine the "you bought/sold" message
    which = "bought" if player.trans_cost < 0 else "sold"
    quant = player.shares_transacted
    s = "s" if quant > 1 else ""

    if quant == 0:
        msg = f"You did not trade any shares this period."
    else:
        msg = f"You {which} {abs(quant)} share{s} at {d.get('market_price')}"
    messages.append(dict(class_attr='result-msg', msg=msg))


    # Bankrupt
    if d.get('bankrupt'):
        msg = f"You are now bankrupt and will be unable to participate the in market.  You will be directed to the" \
              f" survey portion of the experiment.  Afterward you will be able to collect your $10.00 participation" \
              f" fee plus any forecast bonus that you earned during the experiment."
        messages.append(dict(class_attr='alert-danger', msg=msg))

    return messages




def pre_round_tasks(group: Group):
    assign_endowments(group)

    # Determine auto transaction statuses
    # And copy previous round results to the current player object
    for p in group.get_players():
        # Copy results from the previous player
        p.copy_results_from_previous_round()

        # update margin violations
        p.determine_auto_trans_status()

    # Determine the float and set it on all group objects
    if group.round_number == 1:
        group.determine_float()
    else:
        # copy float from previous round
        prev_g = group.in_round_or_none(group.round_number - 1)
        if prev_g:  # should be guaranteed a group object here, but just in case.
            group.float = prev_g.float

    # Calculate total shorts
    group.short = abs(sum(p.shares for p in group.get_players() if p.shares < 0))

#######################################
# CALCULATE MARKET
def calculate_market(group: Group):
    cm = CallMarket(group)
    cm.calculate_market()

    for p in group.get_players():
        # Process current round forecasts
        p.determine_forecast_reward(group.price)


def not_displayed_for_simulation(player: Player):
    return not scf.get_session_name(player) == 'sim_1'


def not_displayed_for_simulation_except_last_round(player: Player):
    return not scf.get_session_name(player) == 'sim_1' or player.round_number == Constants.num_rounds


def custom_export(players):
    yield ['session', 'participant', 'part_label', 'round_number', 'type', 'quantity', 'price',
           'quantity_final', 'original_quantity', 'automatic', 'market_price', 'volume']

    for p in players:
        session = p.session
        part = p.participant
        group = p.group
        orders = Order.filter(player=p)

        for o in orders:
            o_type = 'SELL' if o.order_type == 1 else 'BUY'
            yield [session.code, part.code, part.label, p.round_number, o_type, o.quantity, o.price,
                   o.quantity_final, o.original_quantity, o.is_buy_in,
                   group.field_maybe_none('price'), group.field_maybe_none('volume')]


def vars_for_admin_report(subsession: BaseSubsession):
    group = subsession.get_groups()[0]
    return {"orders": Order.filter(group=group)}


############
# PAGES
##########
class PreMarketWait(WaitPage):
    body_text = "Waiting for the experiment to begin"
    after_all_players_arrive = pre_round_tasks


class Fixate(Page):
    get_timeout_seconds = scf.get_fixate_time
    form_model = 'player'

    # method bindings
    js_vars = get_js_vars_fixate


class MarketGridChoice(Page):
    template_name = 'rounds/MarketPageModular.html'
    get_timeout_seconds = scf.get_market_time
    form_model = 'player'
    timer_text = 'Time Left:'

    # method bindings
    js_vars = get_js_vars
    vars_for_template = vars_for_market_template
    live_method = market_page_live_method


class ForecastPage(Page):
    template_name = 'rounds/MarketPageModular.html'
    form_model = 'player'
    form_fields = ['f0']
    timer_text = 'Time Left:'

    js_vars = get_js_vars_forcast_page
    vars_for_template = vars_for_forecast_template
    get_timeout_seconds = scf.get_forecast_time
    is_displayed = not_displayed_for_simulation
    live_method = forecast_page_live_method


class MarketWaitPage(WaitPage):
    after_all_players_arrive = calculate_market


class RoundResultsPage(Page):
    template_name = 'rounds/MarketPageModular.html'
    form_model = 'player'
    timer_text = 'Time Left:'

    js_vars = get_js_vars_round_results
    vars_for_template = vars_for_round_results_template
    get_timeout_seconds = scf.get_summary_time
    is_displayed = not_displayed_for_simulation_except_last_round
    live_method = result_page_live_method

    @staticmethod
    def app_after_this_page(player: Player, upcoming_apps):
        if not upcoming_apps or len(upcoming_apps) == 0:
            return None

        if player.is_bankrupt(results=True):
            participant = player.participant
            participant.MARKET_PAYMENT = cu(0)

            forecast_bonus = 0
            for p in player.in_all_rounds():
                forecast_bonus += p.forecast_reward
            participant.FORECAST_PAYMENT = cu(forecast_bonus)

            return upcoming_apps[0]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.round_number != Constants.num_rounds:
            return

        bankrupt = player.is_bankrupt()
        participant = player.participant

        # Market Bonus - Final equity with STOCK at Fundamental Value
        market_bonus = 0
        if not bankrupt:
            stock_value = player.shares_result * scf.get_fundamental_value(player)
            total_equity = stock_value + player.cash_result
            bonus_cap = scf.get_bonus_cap(player)
            market_bonus = min(total_equity, bonus_cap)

        participant.MARKET_PAYMENT = cu(market_bonus)

        # Forecast Bonus
        forecast_bonus = 0
        for p in player.in_all_rounds():
            forecast_bonus += p.forecast_reward
        participant.FORECAST_PAYMENT = cu(forecast_bonus)

        # Determine total bonus and round up to whole dollar amount.
        bonus = market_bonus + forecast_bonus
        is_online = scf.is_online(player)
        if not is_online:  # only round up for in-person sessions
            conversion = 1 / scf.get_conversion_rate(player)
            bonus = ceil(bonus / conversion) * conversion
        participant.payoff = max(bonus, 0)

class RiskWaitPage(WaitPage):
    pass

class RiskPage(Page):
    template_name = 'rounds/RiskPage.html'
    form_model = 'player'
    form_fields = ['risk']
    timer_text = 'Time Left:'

    vars_for_template = vars_for_risk_template
    get_timeout_seconds = scf.get_risk_elic_time
    is_displayed = not_displayed_for_simulation


class RiskPage1(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_1 = player.field_maybe_none('risk')

class RiskPage2(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_2 = player.field_maybe_none('risk')

class RiskPage3(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_3 = player.field_maybe_none('risk')

class RiskPage4(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_4 = player.field_maybe_none('risk')


class FinalResultsPage(Page):
    js_vars = get_js_vars_round_results
    form_model = 'player'
    timeout_seconds = 120
    timer_text = "Survey starts in:"

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player: Player):
        participant = player.participant
        session = player.session
        market_bonus = participant.vars.get('MARKET_PAYMENT').to_real_world_currency(session)
        forecast_bonus = participant.vars.get('FORECAST_PAYMENT').to_real_world_currency(session)
        return {'market_bonus': market_bonus,
                'forecast_bonus': forecast_bonus,
                'total_pay': participant.payoff_plus_participation_fee(),
                'is_online': scf.is_online(player)}


page_sequence = [PreMarketWait,
                 Fixate,
                 MarketGridChoice,
                 ForecastPage,
                 MarketWaitPage,
                 RoundResultsPage,
                 RiskWaitPage,
                 RiskPage1,
                 RiskPage2,
                 RiskPage3,
                 RiskPage4,
                 FinalResultsPage]
