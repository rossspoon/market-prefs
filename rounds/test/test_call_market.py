import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from rounds.call_market import CallMarket
from rounds.models import *

NUM_ROUNDS = 5
BID = OrderType.BID.value
OFFER = OrderType.OFFER.value
R = .1
MARGIN_RATIO: float = .6
MARGIN_PREM: float = .25
MARGIN_TARGET: float = .3


def get_order(**kwargs):
    o = MagicMock(spec=Order)
    o.player = kwargs.get('player')
    o.group = kwargs.get('group')
    o.order_type = kwargs.get('order_type')
    o.price = kwargs.get('price')
    o.quantity = kwargs.get('quantity')
    o.quantity_final = kwargs.get('quantity_final')
    o.is_buy_in = kwargs.get('is_buy_in')
    o.original_quantity = kwargs.get('original_quantity')
    return o


def basic_group():
    group = Group()
    config_settings = {'interest_rate': R, 'margin_ratio': MARGIN_RATIO, 'margin_premium': MARGIN_PREM,
                       'margin_target_ratio': MARGIN_TARGET}
    session = MagicMock()
    session.config = config_settings
    group.session = session

    return group


def basic_setup(orders=None):
    if not orders:
        orders = all_orders

    with patch.object(Order, 'filter', return_value=orders):
        Order.filter = MagicMock(return_value=orders)
        group = basic_group()
        group.get_last_period_price = MagicMock(return_value=47)
        cm = CallMarket(group)
    return cm


b_10_05 = get_order(order_type=BID, price=10, quantity=5)
b_10_06 = get_order(order_type=BID, price=10, quantity=6)
b_11_05 = get_order(order_type=BID, price=11, quantity=5)
b_11_06 = get_order(order_type=BID, price=11, quantity=6)

o_05_05 = get_order(order_type=OFFER, price=5, quantity=5)
o_05_06 = get_order(order_type=OFFER, price=5, quantity=6)
o_06_05 = get_order(order_type=OFFER, price=6, quantity=5)
o_06_07 = get_order(order_type=OFFER, price=6, quantity=7)

all_orders = [b_10_05, b_10_06, b_11_05, b_11_06, o_05_05, o_05_06, o_06_05, o_06_07]


# noinspection PyUnresolvedReferences,DuplicatedCode
class TestCallMarket(unittest.TestCase):

    def test_init(self):
        # Set up and
        with patch.object(Order, 'filter', return_value=all_orders):
            group = basic_group()
            group.get_last_period_price = MagicMock(return_value=47)

            # Execute
            cm = CallMarket(group)

            # assert
            self.assertEqual(cm.group, group)
            self.assertEqual(cm.bids, [b_10_05, b_10_06, b_11_05, b_11_06])
            self.assertEqual(cm.offers, [o_05_05, o_05_06, o_06_05, o_06_07])
            Order.filter.assert_called_with(group=group)

    def test_get_orders_for_group(self):
        with patch.object(Order, 'filter', return_value=all_orders):
            # Set-up
            cm = basic_setup()

            # Execute
            bids, offers = cm.get_orders_for_group()

            # Assert
            self.assertEqual(bids, [b_10_05, b_10_06, b_11_05, b_11_06])
            self.assertEqual(offers, [o_05_05, o_05_06, o_06_05, o_06_07])
            Order.filter.assert_called_with(group=cm.group)

    def test_get_orders_for_group_bids(self):
        orders = [b_10_05, b_10_06, b_11_05, b_11_06]
        with patch.object(Order, 'filter', return_value=orders):
            # Set-up
            cm = basic_setup(orders=orders)

            # Execute
            bids, offers = cm.get_orders_for_group()

            # Assert
            self.assertEqual(bids, [b_10_05, b_10_06, b_11_05, b_11_06])
            self.assertEqual(offers, [])
            Order.filter.assert_called_with(group=cm.group)

    def test_get_orders_for_group_offers(self):
        orders = [o_05_05, o_05_06, o_06_05, o_06_07]
        with patch.object(Order, 'filter', return_value=orders):
            # Set-up
            cm = basic_setup(orders=orders)

            # Execute
            bids, offers = cm.get_orders_for_group()

            # Assert
            self.assertEqual(bids, [])
            self.assertEqual(offers, [o_05_05, o_05_06, o_06_05, o_06_07])
            Order.filter.assert_called_with(group=cm.group)

    def test_get_dividend(self):
        # Set-up
        cm = basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist='0.5 0.5', div_amount='40 100'))

        # Execute
        reps = 100000
        s = sum((cm.get_dividend() for _ in range(reps)))
        avg = s / reps

        # Assert
        self.assertAlmostEqual(avg, 70, delta=.3,
                               msg=f"Expecting the average dividend to be around 70, instead it was: {avg}")

# def test_market_case(self):
#     # Set up
#     session = Session()
#     sess_config = dict(interest_rate=0,
#                        margin_ratio=.5,
#                        margin_premium=.1,
#                        margin_target_ratio=.3)
#
#     session.config = sess_config
#     g = Group()
#     g.round_number = 1
#     g.session = session
#
#     p1 = get_player(group=g, cash=100, shares=5)
#     p2 = get_player(group=g, cash=100, shares=5)
#     pt = get_player(group=g, cash=1000, shares=-5)
#
#     o1 = get_order(player=p1, group=g, order_type=BID, price=20, quantity=5)
#     o2 = get_order(player=p2, group=g, order_type=OFFER, price=20, quantity=5)
#
#     with patch.object(Order, 'filter', return_value=[o1, o2]):
#         cm = CallMarket(g, NUM_ROUNDS)
#
#     # Execute
#     cm.calculate_market()
