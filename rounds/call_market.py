import numpy as np
import pandas as pd
import random
from rounds.models import *
from rounds.call_market_price import MarketPrice
from rounds.call_market_price import OrderFill
from collections import defaultdict
import math


class CallMarket:

    def __init__(self, group:Group, num_rounds):
        self.num_rounds = num_rounds
        self.group = group
        self.session = group.session
        self.bids, self.offers = self.get_orders_for_group()
        self.last_price = self.get_last_period_price()

        #get session parameters
        self.interest_rate = self.session.config['interest_rate']
        self.margin_ratio = self.session.config['margin_ratio']
        self.margin_premium  = self.session.config['margin_premium']
        self.margin_target_ratio = self.session.config['margin_target_ratio']


    def get_orders_for_group(self):
        group_orders = Order.filter(group = self.group)
        bids = [o for o in group_orders if OrderType(o.order_type) == OrderType.BID]
        offers = [o for o in group_orders if OrderType(o.order_type) == OrderType.OFFER]
        return bids, offers

    def get_last_period_price(self):
        ## Get the market Price of the last period
        round_number = self.group.round_number
        if round_number == 1:
            last_price = self.get_fundamental_value()
        else:
            ##Look up call price from last period
            last_round_group = self.group.in_round(round_number -1)
            last_price = last_round_group.price

        return round(last_price)  #Round to the nearest integer (up or down)



    #Change this to feilds of the participant
    def set_up_future_player(self, player, margin_violation=False):
        r_num = player.round_number
        if (r_num == self.num_rounds):
            pass
        else:
            future_player = player.in_round(r_num + 1)
            future_player.cash = player.cash_result
            future_player.shares = player.shares_result
            future_player.margin_violation = margin_violation

    def get_dividend(self):
        div_probabilities = [float(x) for x in self.session.config['div_dist'].split()]
        div_amts = [int(x) for x in self.session.config['div_amount'].split()]
        # The realized dividend will be a random draw from the distribution described by the amounts and probs
        dividend = int(random.choices(div_amts, weights=div_probabilities)[0])
        return dividend

    def get_fundamental_value(self):
        session = self.session

        dist = np.array([float(x) for x in session.config['div_dist'].split()])
        amts = np.array([int(x) for x in session.config['div_amount'].split()])
        exp = dist.dot(amts)
        r = session.config['interest_rate']

        if (r == 0):
            return 0

        return int(exp / r)

    def get_orders_by_player(self):
        d = defaultdict(list) 
        for o in self.bids:
            d[o.player].append(o)
        for o in self.offers:
            d[o.player].append(o)
        return d

    def get_new_player_position(self, orders_for_player, p, dividend,  market_price):
        d = p.to_dict()

        #calculate players positions
        net_shares_per_order = (-1 * o.order_type * o.quantity_final for o in orders_for_player)
        shares_transacted = sum(net_shares_per_order)
        new_position = p.shares + shares_transacted
        trans_cost = -1 * int(shares_transacted) * int(market_price)
        cash_after_trade = int(p.cash + trans_cost)

        #assign interest and dividends
        dividend_earned =  dividend * new_position #if new_position is negative then the player pays out dividends
        interest_earned = int(cash_after_trade * self.interest_rate)
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

    def is_margin_violation(self, data, market_price):
        b1 = data['shares_result'] < 0 
        b2 = self.margin_ratio * data['cash_result'] <= abs(market_price * data['shares_result'])
        return b1 and b2

    def get_buy_in_players(self, new_data, players):
        ret = []
        for p in players:
            new_d_for_p = new_data.get(p)
            if new_d_for_p is None:
                continue

            if (new_d_for_p.get('margin_violation_future') and p.margin_violation):
                ret.append(p)

        return ret


    def generate_buy_in_order(self, data, market_price):
        buy_in_price = int(round(market_price * self.margin_premium))  # premium of current market price
        current_value_of_position = abs(data.get('shares_result') * market_price)
        cash_position = data.get('cash_result')
        target_value = math.floor(cash_position * self.margin_target_ratio) # value of shares to be in compliance
        difference = current_value_of_position - target_value
        number_of_shares = int(math.ceil(difference / buy_in_price))
        
        player = data['p']
        return Order.create(player=player
                        , group = player.group
                        , order_type = OrderType.BID.value
                        , price = cu(buy_in_price)
                        , quantity = number_of_shares
                        , is_buy_in = True)


    def calculate_market(group: Group):

            dividend = get_dividend()

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
                o_by_p = get_orders_by_player(Order.filter(group=group))
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
                    buy_in_order = generate_buy_in_order(new_player_data[p], market_price, margin_premium, margin_target_ratio)
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

