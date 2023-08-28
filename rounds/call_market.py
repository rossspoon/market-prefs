import random
from collections import defaultdict

from rounds.models import *
from call_market_price import MarketPrice, OrderFill
from rounds.data_structs import DataForPlayer


class CallMarket:

    def __init__(self, group: Group):
        self.group = group
        self.bids, self.offers = self.get_orders_for_group()
        self.dividend = self.get_dividend()
        self.interest_rate = scf.get_interest_rate(group)
        self.orders_by_player = get_orders_by_player(concat_or_null([self.bids, self.offers]))
        self.players = ensure_player_data(group.get_players())


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
        market_price, market_volume = self.get_market_price()
        market_price = market_price
        market_volume = market_volume
        self.fill_orders(market_price)

        # Compute new player positions
        for player in self.players:
            #this call will mutate the player data
            self.compute_player_position(player, market_price)


        # Perform final updates
        # with the last completed iteration.
        self.final_updates(market_price, market_volume)


    def get_market_price(self):
        # Calculate the Market Price
        b = concat_or_null([self.bids])
        o = concat_or_null([self.offers])
        last_price = self.group.get_last_period_price()

        mp = MarketPrice(b, o)
        market_price, market_volume = mp.get_market_price(last_price=last_price)
        return cu(market_price), market_volume


    def fill_orders(self, market_price):
        of = OrderFill(concat_or_null([self.bids, self.offers]))
        of.fill_orders(market_price)


    def compute_player_position(self, data_for_player, market_price):
        orders = self.orders_by_player[data_for_player.player]
        data_for_player.get_new_player_position(orders, self.dividend, self.interest_rate, market_price)


    def final_updates(self, market_price, market_volume):
        # Final Updates
        for p_data in self.players:
            p_data.update_player()

        # Update the group
        self.group.price = market_price
        self.group.volume = market_volume
        self.group.dividend = self.dividend

    @staticmethod
    def get_total_quantity(offers):
        if offers is None:
            return 0

        return sum((o.quantity for o in offers))



def concat_or_null(list_of_list_of_orders):
    all_none = True
    for o_list in list_of_list_of_orders:
        all_none = all_none and (o_list is None)
    if all_none:
        return None

    ret = []
    for o_list in list_of_list_of_orders:
        if o_list is not None:
            ret.extend(o_list)
    return ret


def get_orders_by_player(orders):
    d = defaultdict(list)
    if orders is None:
        return d

    for o in orders:
        d[o.player].append(o)
    return d


def ensure_player_data(players):
    if players is None:
        return players

    ret = []
    for p in players:
        if isinstance(p, Player):
            ret.append(DataForPlayer(p))
        else:
            ret.append(p)

    return ret
