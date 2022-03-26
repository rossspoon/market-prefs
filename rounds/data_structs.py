import math

import numpy as np

from common import SessionConfigFunctions as scf
from rounds.models import Order, Player, OrderType


class DataForOrder:
    def __init__(self, o=None,
                 player=None,
                 group=None,
                 order_type=None,
                 price=None,
                 quantity=None,
                 original_quantity=None,
                 is_buy_in=False
                 ):
        if o is None:
            self.order = o
            self.id = None
            self.player = player
            self.group = group
            self.order_type = order_type
            self.price = price
            self.quantity = quantity
            self.quantity_final = 0
            self.original_quantity = original_quantity
            self.is_buy_in = is_buy_in
            return

        self.order = o
        self.id = o.id
        self.player = o.player
        self.group = o.group
        self.order_type = o.order_type
        self.price = o.price
        self.quantity = o.quantity
        self.quantity_final = o.quantity_final
        self.original_quantity = o.original_quantity
        self.is_buy_in = o.is_buy_in

    def cancel(self):
        self.original_quantity = self.quantity
        self.quantity = 0

    def update_order(self):
        if self.order is None:
            self.order = Order.create(player=self.player,
                                      group=self.group,
                                      order_type=self.order_type,
                                      price=self.price,
                                      quantity=self.quantity,
                                      is_buy_in=self.is_buy_in,
                                      quantity_final=self.quantity_final,
                                      original_quantity=self.original_quantity)
        else:
            o = self.order
            o.quantity = self.quantity
            o.quantity_final = self.quantity_final
            o.original_quantity = self.original_quantity
            o.is_buy_in = self.is_buy_in

    def __eq__(self, other):
        return np.all((
            eq_with_none(self.id, other.id),
            eq_with_none(self.order, other.order),
            eq_with_none(self.player, other.player),
            eq_with_none(self.group, other.group),
            eq_with_none(self.order_type, other.order_type),
            eq_with_none(self.price, other.price),
            eq_with_none(self.quantity, other.quantity),
            eq_with_none(self.quantity_final, other.quantity_final),
            eq_with_none(self.is_buy_in, other.is_buy_in),
            eq_with_none(self.original_quantity, other.original_quantity)
        ))

    def is_sell(self):
        return self.order_type == OrderType.OFFER.value


class DataForPlayer:
    def __init__(self, player: Player):
        self.player = player

        self.shares_result = None
        self.new_position = None
        self.shares_transacted = None
        self.trans_cost = None
        self.cash_after_trade = None
        self.dividend_earned = None
        self.interest_earned = None
        self.cash_result = None
        self.mv_short_future = False
        self.mv_debt_future = False

    def get_new_player_position(self, orders, dividend, interest_rate, market_price):
        # calculate players positions
        net_shares_per_order = (-1 * o.order_type * o.quantity_final for o in orders)
        self.shares_transacted = sum(net_shares_per_order)
        self.shares_result = self.player.shares + self.shares_transacted
        self.new_position = self.player.shares + self.shares_transacted
        self.trans_cost = -1 * self.shares_transacted * market_price
        self.cash_after_trade = self.player.cash + self.trans_cost

        # assign interest and dividends
        # if self.new_position is negative then the player pays out dividends
        self.dividend_earned = dividend * self.new_position
        self.interest_earned = self.cash_after_trade * interest_rate
        self.cash_result = self.player.cash + self.interest_earned + self.trans_cost + self.dividend_earned

    def set_mv_short_future(self, margin_ratio, market_price):
        if self.shares_result >= 0 or market_price == 0:
            self.mv_short_future = False
            return

        share_value = abs(market_price * self.shares_result)

        b2 = (float(self.cash_result) - share_value) / share_value <= margin_ratio
        self.mv_short_future = b2

    def is_buy_in_required(self):
        return self.player.is_auto_buy() and self.mv_short_future

    def generate_buy_in_order(self, market_price):
        """
        Generate a buy-in order.
        @param market_price: The market price
        @return: DataForOrder
        """
        margin_premium = scf.get_margin_premium(self.player)
        p = market_price * (1 + margin_premium)  # premium of current market price
        tr = scf.get_margin_target_ratio(self.player)
        c = abs(self.player.cash)
        s = abs(self.player.shares)

        number_of_shares = int(math.ceil(((1 + tr)*s*p - c) / (tr * p)))

        player = self.player
        return DataForOrder(player=player,
                            group=player.group,
                            order_type=OrderType.BID.value,
                            price=p,
                            quantity=number_of_shares,
                            is_buy_in=True)

    def set_mv_debt_future(self, margin_ratio, market_price):
        if self.cash_result >= 0:
            self.mv_debt_future = False
            return

        cash = float(abs(self.cash_result))
        b2 = abs(float(self.shares_result) * market_price - cash) / cash <= margin_ratio
        self.mv_debt_future = b2

    def is_sell_off_required(self):
        return self.player.is_auto_sell() and self.mv_debt_future

    def generate_sell_off_order(self, market_price):
        """
        Generate a sell-off order.  The order is capped to the number of shares the plays owns.
        This should never be reached, but it's a backstop just in case.
        @param market_price: The market price
         @return: DataForOrder
        """
        margin_premium = scf.get_margin_premium(self.player)
        p = market_price * (1 - margin_premium)  # premium of current market price
        tr = scf.get_margin_target_ratio(self.player)
        s = abs(self.player.shares)
        c = abs(self.player.cash)

        sell_off_amount = int(math.ceil(abs(((1 - tr) * c - s * p) / (tr * p))))
        number_of_shares = min(sell_off_amount, s)  # prevent shorts

        player = self.player
        return DataForOrder(player=player,
                            group=player.group,
                            order_type=OrderType.OFFER.value,
                            price=p,
                            quantity=number_of_shares,
                            is_buy_in=True)

    def update_player(self):
        p = self.player
        p.shares_result = self.shares_result
        p.shares_transacted = self.shares_transacted
        p.trans_cost = self.trans_cost
        p.cash_after_trade = self.cash_after_trade
        p.dividend_earned = self.dividend_earned
        p.interest_earned = self.interest_earned
        p.cash_result = self.cash_result

    def __eq__(self, other):
        return np.all((
            eq_with_none(self.player, other.player),
            eq_with_none(self.shares_result, other.shares_result),
            eq_with_none(self.new_position, other.new_position),
            eq_with_none(self.shares_transacted, other.shares_transacted),
            eq_with_none(self.trans_cost, other.trans_cost),
            eq_with_none(self.cash_after_trade, other.cash_after_trade),
            eq_with_none(self.dividend_earned, other.dividend_earned),
            eq_with_none(self.interest_earned, other.interest_earned),
            eq_with_none(self.cash_result, other.cash_result),
            eq_with_none(self.mv_short_future, other.mv_short_future),
            eq_with_none(self.mv_debt_future, other.mv_debt_future)
        ))


def eq_with_none(o1, o2):
    eq = False
    if o1 is None and o2 is None:
        eq = True

    elif o1 is not None and o2 is not None:
        eq = o1 == o2
    return eq
