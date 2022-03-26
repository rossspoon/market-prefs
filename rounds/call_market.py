import random

from rounds.market_iteration import MarketIteration
from rounds.models import *


class CallMarket:

    def __init__(self, group: Group):
        self.group = group
        self.bids, self.offers = self.get_orders_for_group()

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

        # Run the market without buy in.  It might be the case that everything clears up.
        iteration = MarketIteration(self.bids, self.offers, self.group, dividend)
        buy_ins, sell_offs = iteration.run_iteration()

        # Quick out if everything clears up
        if not len(buy_ins) and not len(sell_offs):
            self.final_updates(iteration)
            return

        # If we made it this far then there is buy_in demand or sell_off supply

        cnt = 0
        while iteration.recommend_iteration() and cnt < 100:
            iteration = MarketIteration(self.bids, self.offers, self.group, dividend,
                                        buy_ins=buy_ins, sell_offs=sell_offs)
            buy_ins, sell_offs = iteration.run_iteration()

            cnt += 1

        # If the loop exited because of a lack of supply
        # Run the market one last time with the last set of buy ins
        if not iteration.enough_demand() or not iteration.enough_supply():
            iteration = MarketIteration(self.bids, self.offers, self.group, dividend,
                                        buy_ins=buy_ins, sell_offs=sell_offs)
            iteration.run_iteration()

        # Preform final updates
        # with the last completed iteration.
        self.final_updates(iteration)

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
