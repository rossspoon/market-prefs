from collections import defaultdict

from otree.api import cu

from rounds.call_market_price import MarketPrice, OrderFill
from rounds.models import Player, Order, Group, OrderType, NO_SHORT_LIMIT
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
        self.is_first_time = True

        # artifacts to communicate back to the CallMarket
        self.market_price = None
        self.market_volume = None
        self.pending_buy_ins = None
        self.pending_sell_offs = None
        self.buy_in_price = None
        self.sell_off_price = None
        self.buy_recommended = False
        self.sell_recommended = False
        self.old_buy_in_price = None
        self.old_sell_off_price = None

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

        # Update buy-in and sell off price
        if self.buy_in_price is None:
            self.buy_in_price = market_price
        self.old_buy_in_price = self.buy_in_price
        self.buy_in_price = self.buy_in_price * (1 + self.margin_premium)

        if self.sell_off_price is None:
            self.sell_off_price = market_price
        self.old_sell_off_price = self.sell_off_price
        self.sell_off_price = self.sell_off_price * (1 - self.margin_premium)

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
        self.buy_recommended = self.recommend_buy_iteration()
        self.sell_recommended = self.recommend_sell_iteration()

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
        return cu(market_price), market_volume

    def compute_player_position(self, data_for_player, market_price):
        orders = self.orders_by_player[data_for_player.player]
        data_for_player.get_new_player_position(orders, self.dividend, self.interest_rate, market_price)
        data_for_player.set_mv_short_future(self.margin_ratio, market_price)
        data_for_player.set_mv_debt_future(self.margin_ratio, market_price)

        # determine buy-in orders
        # add them to the proper lists
        buy_in_order = None
        if data_for_player.is_buy_in_required():
            buy_in_order = data_for_player.generate_buy_in_order(self.buy_in_price)

        sell_off_order = None
        if data_for_player.is_sell_off_required():
            sell_off_order = data_for_player.generate_sell_off_order(self.sell_off_price)

        return buy_in_order, sell_off_order

    def get_all_orders(self):
        base_orders = concat_or_null([self.bids, self.offers, self.buy_ins, self.sell_offs])
        return base_orders

    def recommend_buy_iteration(self):
        # If this iteration didn't generate any buy_ins then there is no need to iterate
        if not self.pending_buy_ins:
            return False
        elif self.is_first_time:
            return True

        demand = self.get_total_quantity(self.bids) + \
                 self.get_total_quantity(self.buy_ins)
        supply = self.get_total_quantity(self.offers) + \
                 self.get_total_quantity(self.sell_offs)

        max_sell_price = max_price([self.offers, self.sell_offs])

        # The old buy in price was used during this iteration.
        # So if we get to here the market was run once with a buy in price greater than
        # the max sell price.  Further increases in price will not have an effect.
        if self.old_buy_in_price > max_sell_price:
            return False

        any_unfilled_buy_ins = any(o.quantity != o.quantity_final for o in self.buy_ins)
        any_filled_bids = any(o.quantity_final != 0 for o in self.bids)
        any_unfilled_sells = any(o.quantity != o.quantity_final for o
                                 in concat_or_null([self.offers, self.sell_offs]))

        if demand <= supply and any_unfilled_buy_ins:
            return True

        elif demand > supply and (any_filled_bids or any_unfilled_sells):
            return True

        return False

    def recommend_sell_iteration(self):
        # If this iteration didn't generate any sell_offs then there is no need to iterate
        if not self.pending_sell_offs:
            return False
        elif self.is_first_time:
            return True

        demand = self.get_total_quantity(self.bids) + \
                 self.get_total_quantity(self.buy_ins)
        supply = self.get_total_quantity(self.offers) + \
                 self.get_total_quantity(self.sell_offs)

        # The old sell off price was used during this iteration.
        # So if we get to here the market was run once with a sell off price less than
        # the min buy price.  Further decreases in price will not have an effect.
        min_buy_price = min_price([self.bids, self.buy_ins])
        if self.old_sell_off_price < min_buy_price:
            return False

        any_unfilled_sell_offs = any(o.quantity != o.quantity_final for o in self.sell_offs)
        any_filled_offers = any(o.quantity_final != 0 for o in self.offers)
        any_unfilled_buys = any(o.quantity != o.quantity_final for o
                                in concat_or_null([self.bids, self.buy_ins]))

        if supply <= demand and any_unfilled_sell_offs:
            return True

        elif supply > demand and (any_filled_offers or any_unfilled_buys):
            return True

        return False

    def recommend_iteration(self):
        return self.sell_recommended or self.buy_recommended

    def next_iteration(self, bids, offers):
        """
        Create the next market iteration.  Copy the pending buy_ins and sells_offs created this iteration to
        the actual buys_in and sell_offs of the next iteration.  Also, be sure to pass in fresh bids and offers.
        These will get transformed to DataForOrder objects and mutated.  These should be reset each iteration.
        @param bids: The bids - best to be actual Order model objects, so they won't get mutated.
        @param offers: The offers - best to be actual Order model objects, so they won't get mutated.
        @return: The next iteration.
        """
        next_itr = MarketIteration(bids, offers, self.group, self.dividend,
                                   self.pending_buy_ins, self.pending_sell_offs)
        next_itr.sell_off_price = self.sell_off_price
        next_itr.buy_in_price = self.buy_in_price
        next_itr.is_first_time = False
        return next_itr

    @staticmethod
    def get_total_quantity(orders):
        if orders is None:
            return 0

        return sum((o.quantity for o in orders))

    def screen_orders_for_over_shorting(self):
        """
        Pre-screen offers to ensure that the market does not exceed the short limit
        This method will mutate the orders if any quantity of them is canceled.
        """
        # Get the short limit for this round.
        # If there is no limit, simply return.
        round_limit = self.group.get_short_limit()
        if round_limit == NO_SHORT_LIMIT:
            return

        # Get a list of players going short this rounds
        # Then get the offers of the shorting players
        shorting_players = self.get_shorting_players()

        #Determine how much each player is attempting to short and keep the results for later use
        total_short_supply = 0
        short_amount_by_player = {}
        sell_orders_by_player = {}
        for p in shorting_players:
            orders = self.get_orders_for_players(p)
            sell_total_for_player = sum(o.quantity for o in orders)

            amount_player_shorting = 0
            if p.is_short():
                #If the player is already short, then all sell orders are an attempted short sale.
                amount_player_shorting = sell_total_for_player
            else:
                #Otherwise, the amount shorted is the overage
                amount_player_shorting = max(sell_total_for_player - p.shares, 0)

            #remember the results
            total_short_supply += amount_player_shorting
            short_amount_by_player[p] = amount_player_shorting
            sell_orders_by_player[p] = orders

        # skip out if nothing to do
        if total_short_supply <= round_limit:
            return

        # Start canceling orders - Start with the least likely to trade (the orders with the highest price)
        overage = total_short_supply - round_limit
        for o in sorted(self.get_orders_for_players(shorting_players), key=lambda x: x.price, reverse=True):
            if overage <= 0:
                break

            # determine how many shares this player is trying to short
            player_shorting = short_amount_by_player.get(o.player, 0)
            if player_shorting <= 0:
                continue

            # determine the amount that we need to reduce for this player
            overage_for_player = min(overage, player_shorting)
            if o.quantity > overage_for_player:
                allowed_amount = o.quantity - overage_for_player
                amount_reduced = overage_for_player
            else:
                allowed_amount = 0
                amount_reduced = o.quantity

            # update the stored values
            short_amount_by_player[o.player] = player_shorting - amount_reduced
            overage -= amount_reduced

            # update the order
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


def max_price(order_itr):
    orders = concat_or_null(order_itr)
    if orders is None or len(orders) == 0:
        return 0

    prices = [o.price for o in orders]
    return max(prices)


def min_price(order_itr):
    orders = concat_or_null(order_itr)
    if orders is None or len(orders) == 0:
        return 999999

    prices = [o.price for o in orders]
    return min(prices)
