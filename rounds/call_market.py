import random

from rounds.market_iteration import MarketIteration
from rounds.models import *


class CallMarket:

    def __init__(self, group: Group):
        self.group = group
        self.bids, self.offers = self.get_orders_for_group()
        self.auto_trans_premium = scf.get_margin_premium(group)

    def get_orders_for_group(self):
        group_orders = Order.filter(group=self.group)
        bids = [o for o in group_orders if OrderType(o.order_type) == OrderType.BID]
        offers = [o for o in group_orders if OrderType(o.order_type) == OrderType.OFFER]
        return bids, offers

    def get_dividend(self):
        div_probabilities = scf.get_dividend_probabilities(self.group)
        div_amounts = scf.get_dividend_amounts(self.group)
        # The realized dividend will be a random draw from the distribution described by the amounts and probs
        dividend = random.choices(div_amounts, weights=div_probabilities)[0]
        return dividend

    def calculate_market(self):
        dividend = self.get_dividend()

        cnt = 0
        iteration = None
        while (iteration is None or iteration.recommend_iteration()) and cnt < 100:
            if iteration is None:
                iteration = MarketIteration(self.bids, self.offers, self.group, dividend)
            else:
                iteration = iteration.next_iteration(self.bids, self.offers)

            iteration.run_iteration()
            cnt += 1
            print("ITR:", cnt)

        # Perform final updates
        # with the last completed iteration.
        self.final_updates(iteration)

    def get_buy_in_price(self, current_price):
        return current_price * (1 + self.auto_trans_premium)

    def get_sell_off_price(self, current_price):
        return current_price * (1 - self.auto_trans_premium)

    def final_updates(self, iteration):
        # Final Updates
        for p_data in iteration.players:
            p_data.update_player()

        # update orders
        for o in iteration.get_all_orders():
            o.update_order()

        # Update the group
        self.group.price = iteration.market_price
        self.group.volume = iteration.market_volume
        self.group.dividend = iteration.dividend

    @staticmethod
    def get_total_quantity(offers):
        if offers is None:
            return 0

        return sum((o.quantity for o in offers))
