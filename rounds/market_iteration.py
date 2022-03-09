from collections import defaultdict

from rounds.call_market_price import MarketPrice, OrderFill
from rounds.models import Player, Order, Group, OrderType
from rounds.data_structs import DataForOrder, DataForPlayer
import common.SessionConfigFunctions as scf


class MarketIteration:

    def __init__(self, bids, offers, group: Group, dividend, buy_ins=None, sell_offs=None):
        self.bids = ensure_order_data(bids)
        self.offers = ensure_order_data(offers)
        self.buy_ins = ensure_order_data(buy_ins)
        self.sell_offs = ensure_order_data(sell_offs)
        self.orders_by_player = get_orders_by_player(self.get_all_orders())
        self.players = ensure_player_data(group.get_players())
        self.dividend = dividend
        self.last_price = group.get_last_period_price()
        self.group = group

        # artifacts to communicate back to the CallMarket
        self.market_price = None
        self.market_volume = None
        self.pending_buy_ins = None
        self.pending_sell_offs = None

        # get session parameters
        # These dict references will cause ValueErrors if they are missing
        # This enforces that the session config has these values
        self.interest_rate = scf.get_interest_rate(group)
        self.margin_ratio = scf.get_margin_ratio(group)
        self.margin_premium = scf.get_margin_premium(group)
        self.margin_target_ratio = scf.get_margin_target_ratio(group)

    def run_iteration(self):
        # Pre-screen offers to limit shorting
        # This will mutate the data stored in self.offers
        self.screen_orders_for_over_shorting()

        # Cancel the offers of players with forced buy-ins
        # The buy-in price could get quite high.  Higher than this player's sell orders
        # So avoid the situation where the buy price is higher than the sell.
        # Plus this player has no business selling anyway.
        if self.buy_ins:
            buy_in_players = [o.player for o in self.buy_ins]
            self.cancel_orders_for_players(buy_in_players, OrderType.OFFER)

        # Cancel the bids of players with forced sell-offs
        # Similar to buy-ins, but it is the sell price that can get quite low.
        if self.sell_offs:
            sell_off_players = [o.player for o in self.sell_offs]
            self.cancel_orders_for_players(sell_off_players, OrderType.BID)

        # Evaluate the new market conditions
        market_price, market_volume = self.get_market_price()
        self.market_price = market_price
        self.market_volume = market_volume
        self.fill_orders(market_price)

        # Compute new player positions
        auto_buys = []
        auto_sells = []
        for data_for_player in self.players:
            buy, sell = self.compute_player_position(data_for_player, market_price)
            if buy:
                auto_buys.append(buy)
            elif sell:
                auto_sells.append(sell)

        self.pending_sell_offs = auto_sells
        self.pending_buy_ins = auto_buys
        return auto_buys, auto_sells

    def cancel_orders_for_players(self, players, order_type):
        orders = self.get_orders_for_players(players, order_type)
        for o in orders:
            o.cancel()

    def fill_orders(self, market_price):
        of = OrderFill(self.get_all_orders())
        of.fill_orders(market_price)

    def get_market_price(self):
        # Calculate the Market Price
        b = concat_or_null([self.bids, self.buy_ins])
        o = concat_or_null([self.offers, self.sell_offs])
        mp = MarketPrice(b, o)
        market_price, market_volume = mp.get_market_price(last_price=self.last_price)
        return market_price, market_volume

    def compute_player_position(self, data_for_player, market_price):
        orders = self.orders_by_player[data_for_player.player]
        data_for_player.get_new_player_position(orders, self.dividend, self.interest_rate, market_price)
        data_for_player.set_mv_short_future(self.margin_ratio, market_price)
        data_for_player.set_mv_debt_future(self.margin_ratio, market_price)

        # determine buy-in orders
        # add them to the proper lists
        buy_in_order = None
        if data_for_player.is_buy_in_required():
            buy_in_order = data_for_player.generate_buy_in_order(market_price)

        sell_off_order = None
        if data_for_player.is_sell_off_required():
            sell_off_order = data_for_player.generate_sell_off_order(market_price)

        return buy_in_order, sell_off_order

    def get_all_orders(self):
        return concat_or_null([self.bids, self.offers, self.buy_ins, self.sell_offs])

    def recommend_iteration(self):
        auto_buy_still_required = len(self.pending_buy_ins) > 0
        auto_sell_still_required = len(self.pending_sell_offs) > 0

        enough_supply = self.enough_supply()
        enough_demand = self.enough_demand()
        auto_trans_required = auto_buy_still_required and enough_supply or auto_sell_still_required and enough_demand
        return auto_trans_required

    def enough_supply(self):
        buy_in_demand = self.get_total_quantity(self.pending_buy_ins)
        sell_off_supply = self.get_total_quantity(self.pending_sell_offs)

        total_base_supply = self.get_total_quantity(self.offers)
        supply_with_sell_off = total_base_supply + sell_off_supply
        enough_supply = buy_in_demand <= supply_with_sell_off
        return enough_supply

    def enough_demand(self):
        buy_in_demand = self.get_total_quantity(self.pending_buy_ins)
        sell_off_supply = self.get_total_quantity(self.pending_sell_offs)

        total_base_demand = self.get_total_quantity(self.bids)
        demand_with_buy_in = total_base_demand + buy_in_demand
        enough_demand = sell_off_supply <= demand_with_buy_in
        return enough_demand

    @staticmethod
    def get_total_quantity(offers):
        if offers is None:
            return 0

        return sum((o.quantity for o in offers))

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
                allowed_amount = o.quantity - overage
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


def ensure_order_data(orders):
    if orders is None:
        return None

    ret = []
    for o in orders:
        if isinstance(o, Order):
            ret.append(DataForOrder(o))
        else:
            ret.append(o)
    return ret


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
