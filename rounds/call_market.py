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
        dividend = int(random.choices(div_amounts, weights=div_probabilities)[0])
        return dividend

    def screen_orders_for_over_shorting(self):
        """
        Pre-screen offers to ensure that the market does not exceed the short limit
        This method will mutate the orders if any quantity of them is canceled.
        """
        # Get the short limit for this round.
        # If there is no limit, simply return.
        round_limit = self.group.get_short_limit()
        if round_limit == Group.NO_SHORT_LIMIT:
            return

        # Get a list of players going short this rounds
        # Then get the offers of the shorting players
        shorting_players = self.get_shorting_players()
        short_offers = self.get_orders_for_players(shorting_players)
        total_short_supply = sum(o.quantity for o in short_offers)

        # skip out if nothing to do
        if total_short_supply <= round_limit:
            return

        # Start canceling orders - Start with the least likely to trade (the orders with the highest price)
        overage = total_short_supply - round_limit
        for o in sorted(short_offers, key=lambda x: x.price, reverse=True):
            if overage <= 0:
                break

            order_supply = o.quantity
            allowed_amount = None
            if order_supply <= overage:
                overage -= order_supply
                allowed_amount = 0
            elif order_supply > overage:
                allowed_amount = overage
                overage = 0

            o.original_quantity = o.quantity
            o.quantity = allowed_amount

    def get_orders_for_players(self, players, order_type=OrderType.OFFER):
        """
        Get orders for the given iterable of players.  Players can be a single Player
        @param players: iterable or single player
        @param order_type: default OrderType.OFFER
        @return: an iterable of orders for the given players
        """
        if order_type == OrderType.OFFER:
            base_orders = self.offers
        else:
            base_orders = self.bids

        try:
            _ = iter(players)
        except TypeError:
            _players = {players}
        else:
            _players = set(players)

        return list(filter(lambda o: o.player in _players, base_orders))

    def get_supply_for_player(self, player):
        orders_for_player = self.get_orders_for_players(player)
        return sum(o.quantity for o in orders_for_player)

    def get_shorting_players(self):
        shorting_players = []
        for p in self.group.get_players():
            player_supply = self.get_supply_for_player(p)
            if player_supply > 0 and player_supply > p.shares:
                shorting_players.append(p)
        return shorting_players

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
        self.group.price = int(iteration.market_price)
        self.group.volume = int(iteration.market_volume)
        self.group.dividend = iteration.dividend

    @staticmethod
    def get_total_quantity(offers):
        if offers is None:
            return 0

        return sum((o.quantity for o in offers))
