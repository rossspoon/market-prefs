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
            raw_value = self.group.session.config.get('initial_price')
            if raw_value:
                return int(raw_value)
            else:
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
        total_supply = self.get_total_quantity(self.offers)   # get this once since it does not change

        players = self.group.get_players()
        config = self.group.session.config

        # Run the market without buy in.  It might be the case that everything clears up.
        iteration = MarketIteration(self.bids, self.offers, players,
                                    config, dividend, self.last_price,)
        buy_ins = iteration.run_iteration()

        # Quick out if everything clears up
        if not buy_ins:
            self.final_updates(iteration)
            return

        # If we made it this far then there is buy_in demand
        buy_in_required = True
        buy_in_demand = self.get_total_quantity(buy_ins)
        enough_supply = buy_in_demand <= total_supply

        # loop while at_least_once
        # players that are MV are still MV
        # still supply (offers) available
        # Note that as the bid price increases, the buy-in demand might change
        # This means that we have to test for total supply each iteration of the market.
        cnt = 0
        while buy_in_required and enough_supply and cnt < 10:
            iteration = MarketIteration(self.bids, self.offers, players,
                                        config, dividend, self.last_price,
                                        buy_ins=buy_ins)
            buy_ins = iteration.run_iteration()

            # determine the conditions that determine if we need another iteration.
            buy_in_demand = self.get_total_quantity(buy_ins)
            buy_in_required = buy_in_demand > 0
            enough_supply = buy_in_demand <= total_supply
            cnt += 1

        # If the loop exited because of a lack of supply
        # Run the market one last time with the last set of buy ins
        if not enough_supply:
            iteration = MarketIteration(self.bids, self.offers, players,
                                        config, dividend, self.last_price, buy_ins=buy_ins)
            iteration.run_iteration()

        # Preform final updates
        # with the last completed iteration.
        self.final_updates(iteration)

    def final_updates(self, iteration):
        # Final Updates
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
        self.group.dividend = iteration.dividend

    @staticmethod
    def get_total_quantity(offers):
        if offers is None:
            return 0

        return sum((o.quantity for o in offers))
