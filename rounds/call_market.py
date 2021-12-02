import random

import numpy as np

from rounds.market_iteration import MarketIteration
from rounds.models import *


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
        if r_num == self.num_rounds:
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
        div_amounts = np.array([int(x) for x in session.config['div_amount'].split()])
        exp = dist.dot(div_amounts)
        r = session.config['interest_rate']

        if r == 0:
            return 0

        return int(exp / r)

    def calculate_market(self):
        dividend = self.get_dividend()
        total_supply = get_total_quantity(self.offers)

        buy_in_required = False
        enough_supply = True
        players = self.group.get_players()
        config = self.group.session.config
        iteration = None
        buy_ins = None

        # loop while at_least_once
        # players that are MV are still MV
        # still supply (offers) available
        while iteration is None or (buy_in_required and enough_supply):
            iteration = MarketIteration(self.bids, self.offers, players,
                                        config, dividend, self.last_price,
                                        buy_ins=buy_ins)

            buy_ins = iteration.run_iteration()

            # determine the conditions that determine if we need another iteration.
            buy_in_demand = get_total_quantity(buy_ins)
            buy_in_required = buy_in_demand > 0
            enough_supply = buy_in_demand <= total_supply

            # all_orders = [DataForOrder(o=o) for o in bids_for_loop + offers_for_loop]
            #
            # # Evaluate the new market conditions
            # # Calculate the Market Price
            # mp = MarketPrice(bids_for_loop, offers_for_loop)
            # market_price, market_volume = mp.get_market_price(last_price=self.last_price)
            # print(mp.price_df)
            #
            # # Fill Orders
            # of = OrderFill(all_orders)
            # of.fill_orders(market_price)
            #
            # # Apply new market conditions to the players
            # o_by_p = get_orders_by_player(all_orders)
            # buy_ins = []
            # for p in self.group.get_players():
            #     orders_for_player = o_by_p[p]
            #     data_for_player = DataForPlayer(p, orders_for_player)
            #     data_for_player.get_new_player_position(dividend, self.interest_rate, market_price)
            #     data_for_player.set_mv_future(self.margin_ratio, market_price)
            #     new_player_data[p] = data_for_player
            #
            #     # determine buy-in orders
            #     # add them to the proper lists
            #     if data_for_player.is_buy_in_required():
            #         buy_in_order = data_for_player.generate_buy_in_order(market_price, self.margin_premium,
            #                                                              self.margin_target_ratio)
            #         buy_ins.append(buy_in_order)
            #
            # buy_in_required = len(buy_ins) > 0
            # bids_for_loop = base_bid_data + buy_ins

        # The Market Iteration created by the last time through the loop contains all the
        # information needed to update the players, orders, and groups.

        for p_data in iteration.players:
            p_data.update_player()
            # Propagate certain data to the next round.
            self.set_up_future_player(p_data.player, margin_violation=p_data.margin_violation_future)

        # update orders
        for o in iteration.get_all_orders():
            o.update_order()

        # Update the group
        self.group.price = int(iteration.market_price)
        self.group.volume = int(iteration.market_volume)
        self.group.dividend = dividend


def get_total_quantity(offers):
    if offers is None:
        return 0

    return sum((o.quantity for o in offers))
