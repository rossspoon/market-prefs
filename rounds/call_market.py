import random
from rounds.market_iteration import MarketIteration
from rounds.models import *
import common.SessionConfigFunctions as scf


class CallMarket:

    def __init__(self, group: Group, num_rounds):
        self.num_rounds = num_rounds
        self.group = group
        self.bids, self.offers = self.get_orders_for_group()
        self.last_price = group.get_last_period_price()

    def get_orders_for_group(self):
        group_orders = Order.filter(group=self.group)
        bids = [o for o in group_orders if OrderType(o.order_type) == OrderType.BID]
        offers = [o for o in group_orders if OrderType(o.order_type) == OrderType.OFFER]
        return bids, offers

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
        div_probabilities = scf.get_dividend_probabilities(self)
        div_amts = scf.get_dividend_amounts(self)
        # The realized dividend will be a random draw from the distribution described by the amounts and probs
        dividend = int(random.choices(div_amts, weights=div_probabilities)[0])
        return dividend

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
