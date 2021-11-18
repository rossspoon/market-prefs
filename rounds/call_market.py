import math
import random
from collections import defaultdict

import numpy as np

from rounds.call_market_price import MarketPrice
from rounds.call_market_price import OrderFill
from rounds.models import *


def get_orders_by_player(orders):
    d = defaultdict(list)
    for o in orders:
        d[o.player].append(o)
    return d


class CallMarket:

    def __init__(self, group: Group, num_rounds):
        self.num_rounds = num_rounds
        self.group = group
        self.session = group.session
        self.bids, self.offers = self.get_orders_for_group()
        self.last_price = self.get_last_period_price()

        # get session parameters
        self.interest_rate = self.session.config['interest_rate']
        self.margin_ratio = self.session.config['margin_ratio']
        self.margin_premium = self.session.config['margin_premium']
        self.margin_target_ratio = self.session.config['margin_target_ratio']

    def get_orders_for_group(self):
        group_orders = Order.filter(group=self.group)
        bids = [o for o in group_orders if OrderType(o.order_type) == OrderType.BID]
        offers = [o for o in group_orders if OrderType(o.order_type) == OrderType.OFFER]
        return bids, offers

    def get_last_period_price(self):
        # Get the market Price of the last period
        round_number = self.group.round_number
        if round_number == 1:
            last_price = self.get_fundamental_value()
        else:
            # Look up call price from last period
            last_round_group = self.group.in_round(round_number - 1)
            last_price = last_round_group.price

        return round(last_price)  # Round to the nearest integer (up or down)

    # Change this to fields of the participant
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

        if r == 0:
            return 0

        return int(exp / r)

    def calculate_market(self):

        dividend = self.get_dividend()

        has_looped = False
        buy_in_required = False
        enough_supply = True
        bids_for_loop = self.bids
        offers_for_loop = self.offers
        # loop while at_least_once
        # players that are MV are still MV
        # still supply (offers) available
        while not (has_looped) or (buy_in_required and enough_supply):
            has_looped = True
            buy_in_required = False

            # Evaluate the new narket conditions
            # Calculate the Market Price
            mp = MarketPrice(bids_for_loop, offers_for_loop)
            market_price, market_volume = mp.get_market_price(last_price=self.last_price)

            # Fill Orders
            all_orders = bids_for_loop + offers_for_loop
            of = OrderFill(all_orders)
            filled_bids, filled_offers = of.fill_orders(market_price)

            # Apply new market conditions to the players
            o_by_p = get_orders_by_player(all_orders)
            new_player_data = {}
            buy_ins = []
            for p in self.group.get_players():
                orders_for_player = o_by_p[p]
                data_for_player = DataForPlayer(p, orders_for_player)
                data_for_player.get_new_player_position(dividend, self.interest_rate, market_price)
                data_for_player.set_mv_future(self.margin_ratio, market_price)
                new_player_data[p] = data_for_player

                # determine buy-in orders
                # add them to the proper lists
                if data_for_player.is_buy_in_required():
                    buy_in_order = data_for_player.generate_buy_in_order(market_price, self.margin_premium,
                                                                         self.margin_target_ratio)
                    buy_ins.append(buy_in_order)

            buy_in_required = len(buy_ins) > 0
            bids_for_loop = self.bids + buy_ins

            # determine if there is remaining supply, if market volume is exactly equal
            # the outstanding supply that is less than or equal to the new market price
            buy_in_demand = sum([o.quantity for o in buy_ins])
            total_supply = sum([o.quantity for o in self.offers])
            enough_supply = buy_in_demand <= total_supply

        # Finally update all the players
        for p in self.group.get_players():
            data = new_player_data[p]
            data.update_player()
            self.set_up_future_player(data.player, margin_violation=data.margin_violation_future)

        # Update the group
        self.group.price = int(market_price)
        self.group.volume = int(market_volume)
        self.group.dividend = dividend


class DataForPlayer():
    def __init__(self, player: Player, orders):
        self.player = player
        self.orders = orders

        self.shares_result = None
        self.new_position = None
        self.shares_transacted = None
        self.trans_cost = None
        self.cash_after_trade = None
        self.dividend_earned = None
        self.interest_earned = None
        self.cash_result = None
        self.margin_violation_future = False

    def get_new_player_position(self, dividend, interest_rate, market_price):
        # calculate players positions
        net_shares_per_order = (-1 * o.order_type * o.quantity_final for o in self.orders)
        self.shares_transacted = sum(net_shares_per_order)
        self.shares_result = self.player.shares + self.shares_transacted
        self.new_position = self.player.shares + self.shares_transacted
        self.trans_cost = -1 * int(self.shares_transacted) * int(market_price)
        self.cash_after_trade = int(self.player.cash + self.trans_cost)

        # assign interest and dividends
        # if self.new_position is negative then the player pays out dividends
        self.dividend_earned = dividend * self.new_position
        self.interest_earned = int(self.cash_after_trade * interest_rate)
        self.cash_result = int(self.player.cash + self.interest_earned + self.trans_cost + self.dividend_earned)

    def set_mv_future(self, margin_ratio, market_price):
        b1 = self.shares_result < 0
        b2 = margin_ratio * self.cash_result <= abs(market_price * self.shares_result)
        self.margin_violation_future = b1 and b2

    def is_buy_in_required(self):
        return self.player.margin_violation and self.margin_violation_future

    def generate_buy_in_order(self, market_price, margin_premium, margin_target_ratio):
        buy_in_price = int(round(market_price * margin_premium))  # premium of current market price
        current_value_of_position = abs(self.shares_result * market_price)
        cash_position = self.cash_result
        target_value = math.floor(cash_position * margin_target_ratio)  # value of shares to be in compliance
        difference = current_value_of_position - target_value
        number_of_shares = int(math.ceil(difference / buy_in_price))

        player = self.player
        return Order.create(player=player
                            , group=player.group
                            , order_type=OrderType.BID.value
                            , price=cu(buy_in_price)
                            , quantity=number_of_shares
                            , is_buy_in=True)

    def update_player(self):
        p = self.player
        p.shares_result = self.shares_result
        p.shares_transacted = self.shares_transacted
        p.trans_cost = self.trans_cost
        p.cash_after_trade = self.cash_after_trade
        p.dividend_earned = self.dividend_earned
        p.interest_earned = self.interest_earned
        p.cash_result = self.cash_result
