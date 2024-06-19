import decimal
from collections import defaultdict
from math import floor
from rounds.call_market import CallMarket
from . import tool_tip
from .models import Player, Group, Order, OrderErrorCode, OrderType, cu, Page, WaitPage, BaseSubsession, BaseConstants, Subsession
from .sample_hist import SAMPLE_HIST
import common.SessionConfigFunctions as scf
from common.ParticipantFuctions import generate_participant_ids, is_button_click
from otree import database
import os
import json
import numpy as np
import random
import math
from datetime import date


#read in and pickle the decision tree for the risk elicitation task
with open("common/decision_trees_and_gambles.json", "r") as dec_tree:
    js = dec_tree.read()
DECISION_TREES = json.loads(js)


NUM_ROUNDS = os.getenv('SSE_NUM_ROUNDS')
NUM_PRACTICE_ROUNDS = os.getenv('SSE_NUM_PRACTICE_ROUNDS')


class Constants(BaseConstants):
    name_in_url = 'rounds'
    players_per_group = None
    num_market_rounds = 30
    
    if NUM_PRACTICE_ROUNDS:
        num_practice = int(NUM_PRACTICE_ROUNDS)
    else:
        num_practice = 3
    
    if NUM_ROUNDS:
        num_market_rounds = int(NUM_ROUNDS)
        num_rounds = int(NUM_ROUNDS) + num_practice
    else:
        num_rounds = 30 + num_practice

print(f"Number of Rounds: {Constants.num_rounds}")
print(f"Number of Practice Rounds: {Constants.num_practice}")
print(f"Number of Market Rounds: {Constants.num_rounds - Constants.num_practice}")

# determine which rounds are practice by the setting is_practice on the group objects
def creating_session(subsession: Subsession):
    
    #Set the date as the label
    session = subsession.session
    today = date.today().strftime("%Y-%m-%d")
    session.label=today
    session.comment = "Market Experiment"
    
    if subsession.round_number <= Constants.num_practice:
        for g in subsession.get_groups():
            g.is_practice = True


# assign treatments
def assign_endowments(subsession):
    # only set up endowments in the first round
    if subsession.round_number != 1 and subsession.round_number != Constants.num_practice + 1:
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
    return get_js_vars(player, show_cancel=False)

def get_js_vars_round_results(player: Player):
    return get_js_vars(player, include_current=True, show_notes=True, show_cancel=False)

def get_js_vars_final_results(player: Player):
    return get_js_vars(player, include_current=True, show_notes=True, show_cancel=False, event_type='stop_exp')


def get_js_vars_for_risk(player: Player, choice_num: int):
    ret =  get_js_vars(player)
    idx = player.round_number-1
    
    risk_task = DECISION_TREES[idx]
    
    sh = f"${risk_task['sh'] : .2f}"
    sl = f"${risk_task['sl'] : .2f}"
    rh = f"${risk_task['rh'] : .2f}"
    rl = f"${risk_task['rl'] : .2f}"
    

    ret['safe_pay'] = [sh, sl]
    ret['risk_pay'] = [rh, rl]

    node = traverse_dec_tree(player, risk_task['dec_tree'])
    hi = floor(float(node['q']) * 100)
    lo = 100 - hi
    ret['pct'] = [hi, lo]
    
    # risk parameters from the node, are stored in the html and sent back to the 
    # Risk Page depending on the palyer's choice
    ret['r0'] = node['r0']
    ret['mu0'] = node['mu0']
    ret['r1'] = node['r1']
    ret['mu1'] = node['mu1']
    
    
    #update player object (best place to do it)
    if player.field_maybe_none('risk_rh') is None:
        player.risk_rh = risk_task['rh']
        player.risk_rl = risk_task['rl']
        player.risk_sh = risk_task['sh']
        player.risk_sl = risk_task['sl']
    setattr(player, f'risk_phi_{choice_num}', hi)

    ws_vars = get_websockets_vars(player)
    ret.update(ws_vars)
    return ret


def traverse_dec_tree(player: Player, dec_tree: dict):
    """
    Traverses the given binary tree based on the risk decisions of the player.
    Returns the question (based on the DOSE task) stored in the resting node.
    This is meant for the Risk Elicitation Pages.  The question will become the
    probabilities underlying the pie charts on that page.

    Parameters
    ----------
    player : Player
        The player.
    dec_tree : dict
        The decision tree.  Expecting it to be of the form:
            node = {q:<question>,  right: <node>,  left: <node>}.

    Returns
    -------
    int : the question.  The percentage chance of a hi payout expressed as a
            2-digit integer.
    """
    moves = []

    # Three moves gets you to the leaf nodes of these trees
    # 1=risky, 0=safe
    for i in [1,2,3]:
        rc = player.field_maybe_none(f"risk_{i}")
        if rc is not None:
            moves.append(rc)

    #Traverse the tree
    node = dec_tree
    for move in moves:
        if move == 1:
            node = node['right']
        else:
            node = node['left']
            
    
    return node



def get_websockets_vars(player: Player, event_type='page_name'):
    # determine if these are practice sessions
    is_practice = player.group.is_practice
    page_name = player.participant._current_page_name
    
    return dict(
    page_name = page_name,
    event_type = event_type,
    rnd = player.round_number,
    label = player.participant.label,
    part_code = player.participant.code,
    is_practice = is_practice,
    )


def get_js_vars_fixate(player: Player):
    return get_websockets_vars(player, 'fixate')


def get_grid_setting(extreme: int):
    """
    

    Parameters
    ----------
    extreme : int
        Possible price extreme.  This is the amount above and below the 
        market price

    Returns
    -------
    nlines : TYPE
        Number of lines on the grid.  Will None is there is no even division
    nticks : TYPE
        Number of ticks per line. Will None is there is no even division

    """
    # number of grid lines is the 
    nlines = None
    for d in [5,4,3]:
        if extreme % d == 0:
            nlines = d
            break
        
    if nlines is None:
        return None, None
        
    nticks = extreme / nlines
    
    return nticks, nlines - 1



def get_js_vars_grid(player: Player, factor=.2):
    ret = get_js_vars(player)
    
    # get grid spacing variables
    # Price Extreme is the range of price above and below the market price
    
    # initial guess of price extreme
    init_extreme = math.ceil(ret['market_price'] * factor)

    n_ticks, n_lines =  None, None
    for extreme in range(init_extreme, init_extreme+5):
        n_ticks, n_lines = get_grid_setting(extreme)
        if n_ticks and n_lines:
            break
        
    if not(n_ticks) or not(n_lines):
        extreme = 10
        n_ticks = 2
        n_lines = 5
        
    ret['price_extreme'] = extreme
    ret['num_grid_lines'] = n_lines
    ret['minor_tick'] = n_ticks
    return ret



def get_js_vars(player: Player, include_current=False, show_notes=False, show_cancel=True, event_type='page_name'):

    # determine if these are practice sessions
    is_practice = player.group.is_practice
    
    
    # Price History
    group: Group = player.group
    if include_current:
        # TODO: Try doing this with player.round_number
        groups = list(filter(lambda g: g.field_maybe_none('price') is not None, group.in_all_rounds()))
    else:
        groups = group.in_previous_rounds()

    init_price = scf.get_init_price(player)
    

    if scf.is_random_hist(player):
        end_idx = player.round_number + (0 if include_current else -1)
        prices = [init_price] + SAMPLE_HIST["price"][0:end_idx]
        volumes = SAMPLE_HIST["volume"][0:end_idx]
        
    else:
        prices = [init_price] + [g.price for g in groups]
        volumes = [0] + [g.volume for g in groups]
       
    # show practice rounds?
    npract = Constants.num_practice
    if is_practice:
        labels = list(range(0, npract + 1))
        prices = prices[:npract+1]
        volumes = volumes[:npract+1]
    else:
        labels = list(range(0, Constants.num_rounds - npract + 1))
        prices = [init_price] + prices[npract+1:]
        volumes = [0] + volumes[npract+1:]

    # Error Codes
    error_codes = {e.value: e.to_dict() for e in OrderErrorCode}

    if scf.is_random_hist(player):
        market_price = prices[-1]
    else:
        market_price = group.price if include_current else group.get_last_period_price()
    mp_str = f"{market_price:.2f}"

    show_next = scf.show_next_button(player)


    # get websocket variables
    ws_vars = get_websockets_vars(player, event_type)
    # Special case.  The first time we get the market page, trigger a record start.
    if player.round_number == 1 and ws_vars['page_name']=="MarketGridChoice":
        ws_vars['event_type'] = 'rec_start'


    ret = dict(
        labels=labels,
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
        is_practice = is_practice,
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
    #more_price_quant_checks = True

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


def create_order_from_live_submit(player, o_type: OrderType, price, quant, ts, o_cls=Order):
    # TODO:  Does this need to go in a transaction?
    o = o_cls.create(player=player,
                     group=player.group,
                     order_type=o_type.value,
                     price=price,
                     quantity=quant,
                     timestamp=ts
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
        ts = data['ts']

        if error_code == 0:
            ret.update(create_order_from_live_submit(player, t, p, q, ts, o_cls=o_cls))
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


def get_mp_to_show(player: Player, d: dict, include_current=False):
    rn = player.round_number
    is_first_round = rn == 1 or rn == Constants.num_practice + 1
    if scf.is_random_hist(player):
        if is_first_round and not include_current:
            price =  scf.get_init_price(player)
            volume = 0
        
        idx = rn-1 if include_current else rn-2
        price = SAMPLE_HIST['price'][idx]
        volume = SAMPLE_HIST['volume'][idx]
    else:    
        price = player.group.price if include_current else player.group.get_last_period_price()
        volume = player.group.field_maybe_none('volume') # going on the assumption of that volume is only sound on the round results page.
    return price, volume
    


def standard_vars_for_template(player: Player):
    ret = scf.ensure_config(player)
    
    # determine if these are practice sessions
    is_practice = player.group.is_practice
    ret['real_rn'] = player.round_number if is_practice else player.round_number - Constants.num_practice

    ret['is_practice'] = is_practice
    ret['num_practice'] = Constants.num_practice

    
    marg_req = ret.get(scf.SK_MARGIN_RATIO)
    ret['marg_req_pct'] = f"{marg_req :.0%}"
    ret['margin_buffer_pct'] = f"{1 + marg_req:.0%}"
    ret['for_results'] = False
    ret['cash'] = player.cash
    ret['shares'] = player.shares


    price, _ = get_mp_to_show(player, ret)
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
        msg = """<p>Warning:  The the amount of CASH that you have is getting close to your borrowing limit.
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
        msg = """<p>Warning:  The the value of you shorted STOCK is getting close to your limit.
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


def to_mult(x, mult, up=True):
    mod = x % mult
    if mod == 0:
        return x
    
    if up:
        d = mult - mod
        return x+ d
    else:
        return x - mod
    


def get_slider_info(gap: int, mp: int, tgt_period: int, fnum:int):

        mult = 2
        if gap >= 5 and gap < 10:
            mult = 2.5
        elif gap >= 10:
            mult = 3
        
        upper_lim = int(mp * mult)
        
        #determine tick spacing
        tick_step = 5
        if upper_lim > 95 and upper_lim <= 190:
            tick_step = 10
        elif upper_lim > 190:
            tick_step = 20
            
        # Round up to the tick step.
        tick_upper = to_mult(upper_lim, tick_step, up=True)
        tick_lower = 0        
        
        slider_info = {}
        # Generate ticks and save other information on the return object
        slider_info['ticks'] = list(np.arange(tick_lower, tick_upper +1, tick_step))
        slider_info['lo'] = tick_lower
        slider_info['hi'] = tick_upper
        slider_info['mp'] = mp
        slider_info['tgt'] = tgt_period
        
        label = f'This period ({tgt_period})' if gap == 0 else f'Period  {tgt_period}'
        slider_info['label'] = label
        slider_info['f'] = f'f{fnum}'
        
        
        return slider_info
        


def vars_for_forecast_template(player: Player):
    ret = standard_vars_for_template(player)
    ret['action_include'] = 'insert_forecast.html'
    
    fcast_periods = scf.get_forecast_periods(player)
    real_rnd = player.round_number if ret['is_practice'] else player.round_number - Constants.num_practice
    mp = int(ret['market_price'])


    sliders = []
    for i, gap in enumerate(fcast_periods):
        target_period = real_rnd + gap
        if target_period > Constants.num_market_rounds:
            continue
        
        slider_info = get_slider_info(gap, mp, target_period, i)
        sliders.append(slider_info)

        #store target round number on the player object
        if i == 0:
            player.fcast_rnd_0 = target_period
        elif i == 1:
            player.fcast_rnd_1 = target_period
        elif i == 2:
            player.fcast_rnd_2 = target_period
        elif i == 3:
            player.fcast_rnd_3 = target_period
    
    ret['inputs'] = sliders
    return ret



def vars_for_round_results_template(player: Player):
    ret = standard_vars_for_template(player)
    ret['for_results'] = True
    ret['cash'] = player.cash_result
    ret['shares'] = player.shares_result

    price, _ = get_mp_to_show(player, ret, include_current=True)
    
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
    return ret


def vars_for_practice(player: Player):
    return scf.ensure_config(player)


def get_round_result_messages(player: Player, d: dict):
    messages = []

    price, volume = get_mp_to_show(player, d, include_current=True)

    # Price message
    msg = f"Market price this period: {price}"
    messages.append(dict(class_attr='result-msg', msg=msg))

    # Volume message
    msg = f"Market volume this period: {volume} shares"
    messages.append(dict(class_attr='result-msg', msg=msg))

    # Determine the "you bought/sold" message
    which = "bought" if player.trans_cost < 0 else "sold"
    quant = player.shares_transacted
    s = "s" if quant > 1 else ""

    if quant == 0:
        msg = "You did not trade any shares this period."
    else:
        msg = f"You {which} {abs(quant)} share{s} at {d.get('market_price')}"
    messages.append(dict(class_attr='result-msg', msg=msg))


    # Bankrupt
    if d.get('bankrupt'):
        msg = "You are now bankrupt and will be unable to participate the in market.  You will be directed to the" \
              " survey portion of the experiment.  Afterward you will be able to collect your $10.00 participation" \
              " fee plus any forecast bonus that you earned during the experiment."
        messages.append(dict(class_attr='alert-danger', msg=msg))

    return messages




def pre_round_tasks(group: Group):

    assign_endowments(group)

    # Determine auto transaction statuses
    # And copy previous round results to the current player object
    for p in group.get_players():
        # Copy results from the previous player
        # Don't copy previous results for the first real market round.
        if p.round_number != Constants.num_practice + 1:
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

    # TODO: Remove f0 forecast reward
    for p in group.get_players():
        # Process current round forecasts
        p.determine_forecast_reward(group.price)


def not_displayed_for_simulation(player: Player):
    return not scf.get_session_name(player) == 'sim_1'


def not_displayed_for_simulation_except_last_round(player: Player):
    return not scf.get_session_name(player) == 'sim_1' or player.round_number == Constants.num_rounds


def custom_export(players):
    yield ['session', 'participant', 'part_label', 'round_number', 'type', 'quantity', 'price',
           'quantity_final', 'original_quantity', 'automatic', 'timestamp', 'market_price', 'volume']

    for p in players:
        session = p.session
        part = p.participant
        group = p.group
        orders = Order.filter(player=p)

        for o in orders:
            o_type = 'SELL' if o.order_type == 1 else 'BUY'
            ts = o.timestamp
            yield [session.code, part.code, part.label, p.round_number, o_type, o.quantity, o.price,
                   o.quantity_final, o.original_quantity, o.is_buy_in, ts,
                   group.field_maybe_none('price'), group.field_maybe_none('volume')]


def vars_for_admin_report(subsession: BaseSubsession):
    group = subsession.get_groups()[0]
    players = group.get_players()
    return {"orders": Order.filter(group=group),
            "sess_vars": subsession.session.label,
            "plys": players}


def determine_bonus(player: Player):
    rn = player.round_number
    if rn != Constants.num_rounds and rn != Constants.num_practice:
        return

    bankrupt = player.is_bankrupt()
    participant = player.participant
    conversion = scf.get_conversion_rate(player)

    ##
    ##
    ##
    # Market Bonus - Final equity with STOCK at Fundamental Value
    market_bonus = 0
    if not bankrupt:
        stock_value = player.shares_result * scf.get_fundamental_value(player)
        total_equity = stock_value + player.cash_result
        bonus_cap = scf.get_bonus_cap(player)
        market_bonus = min(total_equity, bonus_cap)

    participant.MARKET_PAYMENT = cu(market_bonus)

    ##
    ##
    ## Loop through history and gather data
    risk_choices = []
    current_group = player.group
    include_practice = current_group.is_practice
    groups = {}
    players = {}
    for p in player.in_all_rounds():
        # Ignore practice rounds
        if not(p.group.is_practice) or include_practice:
            risk_choices.extend(p.get_risk_task_data())
            groups[p.round_number] = p.group
            players[p.round_number] = p
    

    ##
    ##
    ## Forcast Bonus
    forecast_bonus = 0
    forecast_data = []
    r_start = 0 if current_group.is_practice else Constants.num_practice
    r_end = Constants.num_practice -1 if current_group.is_practice else Constants.num_rounds
    
    for i in range(r_start, r_end):
        # sort out forecast data
        source_rnd = i + 1
        for look_ahead in range(4):
            p = players[source_rnd]

            #Determine target round, and convert to overall round number
            target_rnd = p.field_maybe_none(f'fcast_rnd_{look_ahead}')
            if not target_rnd:
                continue
            
            target_rnd = target_rnd + Constants.num_practice
            if target_rnd > Constants.num_rounds:
                continue
            
            #Get the price data and the forecast for the target round
            g = groups.get(target_rnd)
            if not g:
                continue
            
            price = g.price
            forecast = p.field_maybe_none(f'f{look_ahead}')

            if not forecast:
                continue  # skip out if no forecast was made
                
            # Determine error and apply threshold rule
            error = abs(price - forecast)
            freward = scf.get_forecast_reward(player) if error <= scf.get_forecast_thold(player) else 0
            # aggergate
            forecast_bonus += freward
            
            # Assemble debugging data
            round_look_data = dict(
                    source_rnd = source_rnd - Constants.num_practice,
                    target_rnd = target_rnd - Constants.num_practice,
                    look_ahead = look_ahead,
                    forecast = int(forecast),
                    price = int(price),
                    error = int(error),
                    reward = int(freward)
                )
            forecast_data.append(round_look_data)
            
    #player.forecast_bonus_data = json.dumps(forecast_data)  #Keep for debugging purposes
    participant.FORECAST_PAYMENT = cu(forecast_bonus)
    
    ##
    ##
    ## Risk Bonus, 
    # first pick a random choice
    risk_bonus = 0
    if len(risk_choices) > 0:
        choice_data = random.choice(risk_choices)        
        # next, run the chosen gamble
        draw = random.random()  # uniformly random between 0 and 1
        success = (draw <= choice_data['p_hi']/100)  # should have a p_hi percent chance of being lower than p_hi.
        
        # Which payout did they win?
        if choice_data['choice'] == 1:  #participant made risky choice
            if success:
                risk_bonus = choice_data['rh']
            else:
                risk_bonus = choice_data['rl']
        else: # participant made the safe choice
            if success:
                risk_bonus = choice_data['sh']
            else:
                risk_bonus = choice_data['sl']
                
        #Modify the choice data with the artifacts of picking and running the gamble
        choice_data['draw'] = draw
        choice_data['success'] = success
        choice_data['bonus'] = risk_bonus
        #fix round number
        choice_data['rnd'] = choice_data['rnd'] - Constants.num_practice
        
        #save choice artifacts on the player object
        player.risk_reward =  json.dumps(choice_data)[:180]# keep for debugging
        
    risk_payment = (risk_bonus/conversion)/10
    participant.RISK_PAYMENT = cu(risk_payment) 
    
    ##
    ##
    ##
    # Determine total bonus and round up to whole dollar amount.
    bonus = market_bonus + forecast_bonus + risk_payment
    # is_online = scf.is_online(player)
    # if not is_online:  # only round up for in-person sessions
    #     bonus = ceil(bonus * conversion) / conversion
    participant.payoff = cu(max(bonus, 0))


    
def group_by_arrival_time_method(subsession: Subsession, waiting_players:list):
    print('######   group_by_arrival_time_method')

    print(f'    waiting: {len(waiting_players)} / {len(subsession.get_players())}')
    print([p.participant.label for p in waiting_players])
    if len(waiting_players) != len(subsession.get_players()):
        return
    
    print(f'   round_number: {subsession.round_number}')
    if subsession.round_number != 1:
        # should never get here.  The wait page GroupingWaitPage only runs once
        # during round 1
        return
    
    #group labels and non responders
    responders = [p for p in subsession.get_players() if p.participant.label]
    
    print(f'    responders:  {len(responders)}')
    return responders
    

############
# PAGES
##########
class GroupingWaitPage(WaitPage):
    body_text = "Waiting for the experiment to begin"
    group_by_arrival_time=True
    
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number==1
    
    
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
    js_vars = get_js_vars_grid
    vars_for_template = vars_for_market_template
    live_method = market_page_live_method


class ForecastPage(Page):
    template_name = 'rounds/MarketPageModular.html'
    form_model = 'player'
    form_fields = ['f0', 'f1', 'f2', 'f3']
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

        
        

class RiskWaitPage(WaitPage):
    pass

class RiskPage(Page):
    template_name = 'rounds/RiskPage.html'
    form_model = 'player'
    form_fields = ['risk', 'dr', 'dmu']
    timer_text = 'Time Left:'

    vars_for_template = vars_for_risk_template
    get_timeout_seconds = scf.get_risk_elic_time
    is_displayed = not_displayed_for_simulation


class RiskPage1(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_1 = player.field_maybe_none('risk')
        player.risk = None
        
        # r param
        r = player.field_maybe_none('dr')
        if r:
            player.dose_r = r
        player.dr = None
            
        # mu param
        m = player.field_maybe_none('dmu')
        if m:
            player.dose_mu = m
        player.dmu = None
        
        
    @staticmethod
    def js_vars(player:Player):
        return get_js_vars_for_risk(player, 1)
        
        
class RiskPage2(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_2 = player.field_maybe_none('risk')
        player.risk = None
       
        # r param
        r = player.field_maybe_none('dr')
        if r:
            player.dose_r = r
        player.dr = None
            
        # mu param
        m = player.field_maybe_none('dmu')
        if m:
            player.dose_mu = m
        player.dmu = None
        
        
    @staticmethod
    def js_vars(player:Player):
        return get_js_vars_for_risk(player, 2)


class RiskPage3(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_3 = player.field_maybe_none('risk')
        player.risk = None
       
        # r param
        r = player.field_maybe_none('dr')
        if r:
            player.dose_r = r
        player.dr = None
            
        # mu param
        m = player.field_maybe_none('dmu')
        if m:
            player.dose_mu = m
        player.dmu = None
        
        
    @staticmethod
    def js_vars(player:Player):
        return get_js_vars_for_risk(player, 3)




class RiskPage4(RiskPage):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_4 = player.field_maybe_none('risk')
        player.risk = None
        
       
        # r param
        r = player.field_maybe_none('dr')
        if r:
            player.dose_r = r
        player.dr = None
            
        # mu param
        m = player.field_maybe_none('dmu')
        if m:
            player.dose_mu = m
        player.dmu = None
        
        
    @staticmethod
    def js_vars(player:Player):
        return get_js_vars_for_risk(player, 4)




class FinalResultsPage(Page):
    js_vars = get_js_vars_final_results
    form_model = 'player'
    get_timeout_seconds = scf.get_final_results_time
    timer_text = "Next Page in:"

    @staticmethod
    def is_displayed(player: Player):
        rn = player.round_number
        return rn == Constants.num_rounds or rn == Constants.num_practice

    @staticmethod
    def vars_for_template(player: Player):
        player.participant.finished = not(player.group.is_practice)  # Set true only on the very last round
        
        ret = standard_vars_for_template(player)
        
        determine_bonus(player)
        participant = player.participant
        session = player.session
        market_bonus = participant.vars.get('MARKET_PAYMENT').to_real_world_currency(session)
        forecast_bonus = participant.vars.get('FORECAST_PAYMENT').to_real_world_currency(session)
        risk_bonus = participant.vars.get('RISK_PAYMENT').to_real_world_currency(session)
        
        conv = scf.get_conversion_rate(player)
        buy_back_amt = player.shares_result * ret['buy_back']
        return ret | {'market_bonus': market_bonus,
                'forecast_bonus': forecast_bonus,
                'risk_bonus': risk_bonus,
                'total_pay': participant.payoff_plus_participation_fee(),
                'is_online': scf.is_online(player),
                'conv':   int(1/conv),
                'buy_back_amt': buy_back_amt,
                'market_price': player.group.price,
                }


class PracticeMarkerPage(Page):
    vars_for_template = vars_for_practice
    js_vars = get_websockets_vars
    timer_text = 'Next page in:'
    
    @staticmethod
    def get_timeout_seconds(player: Player):
        if player.round_number == 1:
            return scf.get_practice_time(player)
        else:
            return scf.get_practice_end_time(player)
        
    
    @staticmethod 
    def js_vars(player: Player):
        ret = {}
        if player.round_number == 1:
            ret['timer_text'] = 'Practice Begins in: '
        else:
            ret['timer_text'] = 'Experiment Begins in: '
            
        return ret

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1  or player.round_number == Constants.num_practice + 1




page_sequence = [#GroupingWaitPage,
                 PreMarketWait,
                 PracticeMarkerPage,
                 #Fixate,
                 MarketGridChoice,
                 #Fixate,
                 ForecastPage,
                 #Fixate,
                 MarketWaitPage,
                 RoundResultsPage,
                 #Fixate,
                 #RiskWaitPage,
                 RiskPage1,
                 RiskPage2,
                 RiskPage3,
                 RiskPage4,
                 FinalResultsPage,
]
