from collections import defaultdict

from rounds.call_market_price import MarketPrice, OrderFill
from rounds.models import Player, Order
from rounds.data_structs import DataForOrder, DataForPlayer
import common.SessionConfigFunctions as scf


class MarketIteration:

    def __init__(self, bids, offers, players, session_config, dividend, last_price, buy_ins=None, sell_offs=None):
        self.bids = ensure_order_data(bids)
        self.offers = ensure_order_data(offers)
        self.buy_ins = ensure_order_data(buy_ins)
        self.sell_offs = ensure_order_data(sell_offs)
        self.orders_by_player = get_orders_by_player(self.get_all_orders())
        self.players = ensure_player_data(players)
        self.dividend = dividend
        self.last_price = last_price
        self.market_price = None
        self.market_volume = None

        # get session parameters
        # These dict references will cause ValueErrors if they are missing
        # This enforces that the session config has these values
        self.interest_rate = scf.get_interest_rate(session_config)
        self.margin_ratio = scf.get_margin_ratio(session_config)
        self.margin_premium = scf.get_margin_premium(session_config)
        self.margin_target_ratio = scf.get_margin_target_ratio(session_config)

    def run_iteration(self):
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

        return auto_buys, auto_sells

    def fill_orders(self, market_price):
        of = OrderFill(concat_or_null([self.bids, self.offers, self.buy_ins, self.sell_offs]))
        of.fill_orders(market_price)

    def get_market_price(self):
        # Assemble all bids including buy-ins
        all_buys = concat_or_null([self.bids, self.buy_ins])
        all_sells = concat_or_null([self.offers, self.sell_offs])
        # Calculate the Market Price
        mp = MarketPrice(all_buys, all_sells)
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
        if type(p) == Player:
            ret.append(DataForPlayer(p))
        else:
            ret.append(p)

    return ret


def ensure_order_data(orders):
    if orders is None:
        return None

    ret = []
    for o in orders:
        if type(o) == Order:
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
