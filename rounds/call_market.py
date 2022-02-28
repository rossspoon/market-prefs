import random
from rounds.market_iteration import MarketIteration
from rounds.models import *
import common.SessionConfigFunctions as scf


class CallMarket:

    def __init__(self, group: Group):
        self.group = group
        self.bids, self.offers = self.get_orders_for_group()
        self.last_price = group.get_last_period_price()

    def get_orders_for_group(self):
        group_orders = Order.filter(group=self.group)
        bids = [o for o in group_orders if OrderType(o.order_type) == OrderType.BID]
        offers = [o for o in group_orders if OrderType(o.order_type) == OrderType.OFFER]
        return bids, offers

    def get_dividend(self):
        div_probabilities = scf.get_dividend_probabilities(self.group)
        div_amts = scf.get_dividend_amounts(self.group)
        # The realized dividend will be a random draw from the distribution described by the amounts and probs
        dividend = int(random.choices(div_amts, weights=div_probabilities)[0])
        return dividend

    def calculate_market(self):
        dividend = self.get_dividend()
        total_supply = self.get_total_quantity(self.offers)   # get this once since it does not change
        total_demand = self.get_total_quantity(self.bids)

        players = self.group.get_players()
        config = self.group.session.config

        # Run the market without buy in.  It might be the case that everything clears up.
        iteration = MarketIteration(self.bids, self.offers, players,
                                    config, dividend, self.last_price,)
        buy_ins, sell_offs = iteration.run_iteration()

        # Quick out if everything clears up
        if not len(buy_ins) and not len(sell_offs):
            self.final_updates(iteration)
            return

        # If we made it this far then there is buy_in demand or sell_off supply
        auto_trans_required = True
        buy_in_demand = self.get_total_quantity(buy_ins)
        sell_off_supply = self.get_total_quantity(sell_offs)
        supply_with_sell_off = total_supply + sell_off_supply
        demand_with_buy_in = total_demand + buy_in_demand
        enough_supply = buy_in_demand <= supply_with_sell_off
        enough_demand = sell_off_supply <= demand_with_buy_in
        sufficient_orders = enough_demand or enough_supply

        # loop while at_least_once
        # players that are MV are still MV
        # still supply (offers) available
        # Note that as the bid price increases, the buy-in demand might change
        # This means that we have to test for total supply each iteration of the market.
        cnt = 0
        while auto_trans_required and sufficient_orders and cnt < 100:
            iteration = MarketIteration(self.bids, self.offers, players,
                                        config, dividend, self.last_price,
                                        buy_ins=buy_ins, sell_offs=sell_offs)
            buy_ins, sell_offs = iteration.run_iteration()

            # determine the conditions that determine if we need another iteration.
            auto_trans_required = len(buy_ins) or len(sell_offs)

            buy_in_demand = self.get_total_quantity(buy_ins)
            sell_off_supply = self.get_total_quantity(sell_offs)
            supply_with_sell_off = total_supply + sell_off_supply
            demand_with_buy_in = total_demand + buy_in_demand
            enough_supply = buy_in_demand <= supply_with_sell_off
            enough_demand = sell_off_supply <= demand_with_buy_in
            sufficient_orders = enough_demand or enough_supply
            cnt += 1

        # If the loop exited because of a lack of supply
        # Run the market one last time with the last set of buy ins
        if not sufficient_orders:
            iteration = MarketIteration(self.bids, self.offers, players,
                                        config, dividend, self.last_price,
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
        self.group.price = int(iteration.market_price)
        self.group.volume = int(iteration.market_volume)
        self.group.dividend = iteration.dividend

    @staticmethod
    def get_total_quantity(offers):
        if offers is None:
            return 0

        return sum((o.quantity for o in offers))
