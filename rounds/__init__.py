from otree.api import *
from .models import *
import rounds.call_market_price as cmp
from rounds.call_market_price import MarketPrice
from rounds.call_market_price import OrderFill
from scipy.stats import rv_discrete
import random
from statistics import mean
import math
from collections import defaultdict
import numpy as np


class Constants(BaseConstants):
    name_in_url = 'rounds'
    players_per_group = None
    num_rounds = 5
    MARKET_TIME = 50000

#assign treatments
def creating_session(subsession):
    #only set up endowments in the first round
    if subsession.round_number != 1:
        return

    session = subsession.session

    cash_control = session.config['cash_endowment_control']
    shares_control = session.config['shares_endowment_control']
    cash_treatment = session.config['cash_endowment_treatment']
    shares_treatment = session.config['shares_endowment_treatment']

    endowments = [{'cash': cash_control, 'shares': shares_control}
            , {'cash': cash_treatment, 'shares': shares_treatment}]

    if ('treated_ids' in session.config):
        treated_ids = [int(x) for x in session.config['treated_ids'].split()]
        modulus = len(treated_ids)
        for group in subsession.get_groups():
            for player in group.get_players():
                idx = player.id_in_group % modulus
                endowment_idx = treated_ids[idx]
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
            type_assignments = ([0]*num_controls) + ([1]*num_treatments)
            random.shuffle(type_assignments)

            for idx, player in enumerate(group.get_players()):
                endow = endowments[type_assignments[idx]]
                player.cash = endow['cash']
                player.shares = endow['shares']



def get_js_vars(player: Player):
    #Price History
    group = player.group
    groups =  group.in_previous_rounds()

    prices = [g.price for g in groups]
    volumes = [g.volume for g in groups]

    # Error Codes
    error_codes = {e.value: e.to_dict() for e in OrderErrorCode}

    return dict(
            labels = list(range(1, Constants.num_rounds+1))
            , price_data = prices
            , volume_data = volumes
            , num_periods=Constants.num_rounds
            , error_codes = error_codes
            )

#########################
#LIVE PAGES FUNCTIONS
def is_order_valid(data):
    o_type = data['type']
    o_price = data['price']
    o_quant = data['quantity']

    error_code = 0
   
    #price tests
    if not o_price.lstrip('-').isnumeric():
        error_code = OrderErrorCode.PRICE_NOT_NUM.combine(error_code)
    elif (int(o_price) <= 0):
        error_code = OrderErrorCode.PRICE_NEGATIVE.combine(error_code)
    
    #quant tests
    if not o_quant.lstrip('-').isnumeric():
        error_code = OrderErrorCode.QUANT_NOT_NUM.combine(error_code)
    elif (int(o_quant) <= 0):
        error_code = OrderErrorCode.QUANT_NEGATIVE.combine(error_code)

    #type tests
    if not o_type in ['-1', '1']:
        error_code = OrderErrorCode.BAD_TYPE.combine(error_code)

    return error_code == 0, error_code

def process_order_submit(player, data):
    p_id = player.id_in_group

    valid, error_code = is_order_valid(data)

    if (valid):
        o_type = int(data['type'])
        o_price = int(data['price'])
        o_quant = int(data['quantity'])

        o = Order.create(player=player
                    , group = player.group
                    , order_type = o_type
                    #, uuid = str(uuid.uuid4())
                    , price = o_price
                    , quantity = o_quant)

        #HACK!!!!  I don't know why this works, but I'm trying to send the id to of the Order object
        # back to browser and that doesn't work unless I make a db query.
        Order.filter(player = player) 

        return {p_id: {'func': 'order_confirmed',  'order_id': o.id}}
    else:
        return {p_id: {'func': 'order_rejected', 'error_code': error_code}}

def get_orders_for_player_live(player):
    p_id = player.id_in_group
    orders = [o.to_dict() for o in Order.filter(player = player)]
    return {p_id: dict(func ='order_list', orders = orders)}

def delete_order(player, oid):
    obs = Order.filter(player=player, id =  oid)
    [Order.delete(o) for o in obs]


def market_page_live_method(player, d):
    func = d['func']

    if (func == 'submit-order'):
        data = d['data']
        return process_order_submit(player, data)

    elif (func == 'get_orders_for_player') :
        return get_orders_for_player_live(player)

    elif (func == 'delete_order'):
        delete_order(player, d['oid'])

## END LIVE METHODS
#######################################

def standard_vars_for_template(player: Player):
    price = get_last_period_price(player.group)
    pos_value = player.shares * price
    if (player.cash == 0):
        margin_ratio = None
        margin_ratio_pct = None
    else:
        margin_ratio = abs(float(pos_value) / float(player.cash))
        margin_ratio_pct = "{:.0%}".format(margin_ratio)
    return dict( margin_ratio = margin_ratio
                , margin_ratio_pct = margin_ratio_pct
                , price = price
                , pos_value = pos_value
                )
    

def get_orders_for_group(group: Group):
    group_orders = Order.filter(group = group)
    bids = [o for o in group_orders if OrderType(o.order_type) == OrderType.BID]
    offers = [o for o in group_orders if OrderType(o.order_type) == OrderType.OFFER]
    return bids, offers


#Change this to feilds of the participant
def set_up_future_player(player, margin_violation=False):
    r_num = player.round_number
    if (r_num == Constants.num_rounds):
        pass
    else:
        future_player = player.in_round(r_num + 1)
        future_player.cash = player.cash_result
        future_player.shares = player.shares_result
        future_player.margin_violation = margin_violation

#######################################
## CALCULATE MARKET
def get_dividend(session):
    div_probabilities = [float(x) for x in session.config['div_dist'].split()]
    div_amts = [int(x) for x in session.config['div_amount'].split()]
    # The realized dividend will be a random draw from the distribution described by the amounts and probs
    dividend = int(random.choices(div_amts, weights=div_probabilities)[0])
    return dividend

def get_fundamental_value(obj):
    session = obj.session

    dist = np.array([float(x) for x in session.config['div_dist'].split()])
    amts = np.array([int(x) for x in session.config['div_amount'].split()])
    exp = dist.dot(amts)
    r = session.config['interest_rate']

    if (r == 0):
        return 0

    return exp / r

def get_orders_by_players(orders):
    d = defaultdict(list) 
    for o in orders:
        d[o.player].append(o)
    return d

def get_new_player_position(orders_for_player, p, dividend, r, market_price):
    d = p.to_dict()

    #calculate players positions
    net_shares_per_order = (-1 * o.order_type * o.quantity_final for o in orders_for_player)
    shares_transacted = sum(net_shares_per_order)
    new_position = p.shares + shares_transacted
    trans_cost = -1 * int(shares_transacted) * int(market_price)
    cash_after_trade = int(p.cash + trans_cost)

    #assign interest and dividends
    dividend_earned =  dividend * new_position #if new_position is negative then the player pays out dividends
    interest_earned = int(cash_after_trade * r)
    cash_result = int(p.cash + interest_earned + trans_cost + dividend_earned)

    d['p'] = p
    d['shares_result'] = new_position
    d['shares_transacted'] = shares_transacted
    d['trans_cost'] = trans_cost
    d['cash_after_trade'] = cash_after_trade
    d['dividend_earned'] = dividend_earned
    d['interest_earned'] = interest_earned
    d['cash_result'] = cash_result
    return d

def is_margin_violation(data, margin_ratio, market_price):
    b1 = data['shares_result'] < 0 
    b2 = margin_ratio * data['cash_result'] <= abs(market_price * data['shares_result'])
    return b1 and b2

def get_last_period_price(group: Group):
        ## Get the market Price of the last period
        round_number = group.round_number
        if round_number == 1:
            last_price = get_fundamental_value(group)
        else:
            ##Look up call price from last period
            last_round_group = group.in_round(round_number -1)
            last_price = last_round_group.price

        return round(last_price)  #Round to the nearest integer (up or down)

def get_buy_in_players(new_data, old_players):
    ret = []
    for p in old_players:
        new_d_for_p = new_data.get(p)
        if new_d_for_p is None:
            continue

        if (new_d_for_p.get('margin_violation_future') and p.margin_violation):
            ret.append(p)

    return ret


def generate_buy_in_order(player: Player, data, market_price, margin_premium, margin_target_ratio):
    buy_in_price = int(round(market_price * margin_premium))  # premium of current market price
    current_value_of_position = abs(data.get('shares_result') * market_price)
    cash_position = data.get('cash_result')
    target_value = math.floor(cash_position * margin_target_ratio) # value of shares to be in compliance
    difference = current_value_of_position - target_value
    number_of_shares = int(math.ceil(difference / buy_in_price))

    return Order.create(player=player
                    , group = player.group
                    , order_type = OrderType.BID.value
                    , price = cu(buy_in_price)
                    , quantity = number_of_shares
                    , is_buy_in = True)


def calculate_market(group: Group):
        last_price = get_last_period_price(group)

        #Determine dividends
        session = group.session
        dividend = get_dividend(session)

        #get session parameters
        r = session.config['interest_rate']
        margin_ratio = session.config['margin_ratio']
        margin_premium  = session.config['margin_premium']
        margin_target_ratio = session.config['margin_target_ratio']

        #get the current period orders
        base_bids, base_offers = get_orders_for_group(group)
        bids = list(base_bids)
        offers= list(base_offers)

        has_not_looped = True
        buy_in_required = False
        enough_supply = True
        # loop while at_least_once
        ## players that are MV are still MV
        ## still supply (offers) available
        while has_not_looped or (buy_in_required and enough_supply):
            has_not_looped = False
            ##Evaluate the new narket conditions
            ## Calculate the Market Price
            mp = MarketPrice(bids, offers)
            market_price, market_volume = mp.get_market_price(last_price = last_price)
            print("Principal:", mp.final_principle)
            print("DF:\n", mp.price_df)

            #Fill Orders
            of = OrderFill(bids + offers)
            filled_bids, filled_offers = of.fill_orders(market_price)

            #Apply new market conditions to the players
            o_by_p = get_orders_by_players(Order.filter(group=group))
            new_player_data = {}
            for p in group.get_players():
                orders_for_player = o_by_p[p]
                data_for_player = get_new_player_position(orders_for_player, p, dividend, r, market_price)

                #determine if the player is violating the margin requirement
                mv = is_margin_violation(data_for_player, margin_ratio, market_price)
                data_for_player['margin_violation_future'] =  mv

                new_player_data[p] = data_for_player


            # If there are MV's that require buy-in
            buy_ins = []
            buy_in_required = False
            for p in get_buy_in_players(new_player_data, group.get_players()):
                buy_in_required = True
                # determine buy-in orders
                # add them to the proper lists
                buy_in_order = generate_buy_in_order(p, new_player_data[p], market_price, margin_premium, margin_target_ratio)
                buy_ins.append( buy_in_order )

            bids = base_bids + buy_ins

            #determine if there is remaining supply, if market volume is exactly equal 
            # the out standing supply that is less than or equal to the new market price
            buy_in_demand = sum([o.quantity for o in buy_ins])
            total_supply = sum([o.quantity for o in offers])
            enough_supply = buy_in_demand <= total_supply
        

        #Finally update all the players
        for p in group.get_players():
            data = new_player_data[p]
            p.update_from_dict(data)
            mv = data.get('margin_violation_future')
            set_up_future_player(p, margin_violation = mv)

        # Update the group
        group.price = int(market_price)
        group.volume = int(market_volume)
        group.dividend = dividend



############
## PAGES
##########

class Market(Page):
    timeout_seconds = Constants.MARKET_TIME
    form_model = 'player'
    form_fields = [ 'type', 'price', 'quantity' ]

    #method bindings
    js_vars = get_js_vars
    live_method = market_page_live_method
    vars_for_template = standard_vars_for_template



class MarketWaitPage(WaitPage):
    #template_name = 'rounds/MarketWaitPage.html'
    after_all_players_arrive = calculate_market


class PreMarketWait(WaitPage):
    body_text = "Waiting for the experiment to begin"
    pass


class MarketResults(Page):
    js_vars = get_js_vars


class Survey(Page):
    form_model = 'player'
    form_fields = ['emotion']


page_sequence = [PreMarketWait, Market, MarketWaitPage, Survey]
