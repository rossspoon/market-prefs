import numpy as np

from rounds.models import Order, Player, OrderType
import math
from otree.api import *


class DataForOrder:
    def __init__(self, o=None,
                 player=None,
                 group=None,
                 order_type=None,
                 price=None,
                 quantity=None,
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
            self.quantity_final = None
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
        self.is_buy_in = o.is_buy_in

    def update_order(self):
        if self.order is None:
            self.order = Order.create(player=self.player,
                                      group=self.group,
                                      order_type=self.order_type,
                                      price=self.price,
                                      quantity=self.quantity,
                                      is_buy_in=self.is_buy_in,
                                      quantity_final=self.quantity_final)
        else:
            o = self.order
            o.quantity_final = self.quantity_final
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
            eq_with_none(self.is_buy_in, other.is_buy_in)
        ))


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
        self.margin_violation_future = False

    def get_new_player_position(self, orders, dividend, interest_rate, market_price):
        # calculate players positions
        net_shares_per_order = (-1 * o.order_type * o.quantity_final for o in orders)
        self.shares_transacted = sum(net_shares_per_order)
        self.shares_result = self.player.shares + self.shares_transacted
        self.new_position = self.player.shares + self.shares_transacted
        self.trans_cost = -1 * int(self.shares_transacted) * int(market_price)
        self.cash_after_trade = int(self.player.cash + self.trans_cost)

        # assign interest and dividends
        # if self.new_position is negative then the player pays out dividends
        self.dividend_earned = dividend * self.new_position
        self.interest_earned = int(self.cash_after_trade * interest_rate)
        self.cash_result = int(self.player.cash + self.interest_earned + self.trans_cost + self.dividend_earned)

    def set_mv_future(self, margin_ratio, market_price):
        b1 = self.shares_result < 0
        b2 = margin_ratio * self.cash_result <= abs(market_price * self.shares_result)
        self.margin_violation_future = b1 and b2

    def is_buy_in_required(self):
        return self.player.margin_violation and self.margin_violation_future

    def generate_buy_in_order(self, market_price, margin_premium, margin_target_ratio):
        """
        Generate a buy-in order.
        @param market_price: The market price
        @param margin_premium: The premium charged over the existing market price
        @param margin_target_ratio: After calculating the new order price, buy enough shares to meet this margin ratio
        @return: DataForOrder
        """
        price_multiplier = 1 + margin_premium
        buy_in_price = int(round(market_price * price_multiplier))  # premium of current market price
        current_value_of_position = abs(self.shares_result * market_price)
        cash_position = self.cash_result
        target_value = math.floor(cash_position * margin_target_ratio)  # value of shares to be in compliance
        difference = current_value_of_position - target_value
        number_of_shares = int(math.ceil(difference / buy_in_price))

        player = self.player
        return DataForOrder(player=player,
                            group=player.group,
                            order_type=OrderType.BID.value,
                            price=cu(buy_in_price),
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
            eq_with_none(self.margin_violation_future, other.margin_violation_future)
        ))


def eq_with_none(o1, o2):
    eq = False
    if o1 is None and o2 is None:
        eq = True

    elif o1 is not None and o2 is not None:
        eq = o1 == o2
    return eq
