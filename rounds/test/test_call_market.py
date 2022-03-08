import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import PropertyMock
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
    o = MagicMock()
    o.player = kwargs.get('player')
    o.group = kwargs.get('group')
    o.order_type = kwargs.get('order_type')
    o.price = kwargs.get('price')
    o.quantity = kwargs.get('quantity')
    o.is_buy_in = kwargs.get('is_buy_in')
    o.original_quantity = kwargs.get('original_quantity')
    return o


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

    @staticmethod
    def basic_player(shares=0):
        player = MagicMock()
        player.shares = shares
        player.__iter__ = MagicMock(side_effect=TypeError('foo'))
        return player

    @staticmethod
    def basic_group():
        group = Group()
        config_settings = {'interest_rate': R, 'margin_ratio': MARGIN_RATIO, 'margin_premium': MARGIN_PREM,
                           'margin_target_ratio': MARGIN_TARGET}
        session = MagicMock()
        session.config = config_settings
        group.session = session

        return group

    def basic_setup(self, orders=None):
        if not orders:
            orders = all_orders

        with patch.object(Order, 'filter', return_value=orders):
            Order.filter = MagicMock(return_value=orders)
            group = self.basic_group()
            group.get_last_period_price = MagicMock(return_value=47)
            cm = CallMarket(group)
        return cm

    def test_init(self):
        # Set up and
        with patch.object(Order, 'filter', return_value=all_orders):
            group = self.basic_group()
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
            cm = self.basic_setup()

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
            cm = self.basic_setup(orders=orders)

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
            cm = self.basic_setup(orders=orders)

            # Execute
            bids, offers = cm.get_orders_for_group()

            # Assert
            self.assertEqual(bids, [])
            self.assertEqual(offers, [o_05_05, o_05_06, o_06_05, o_06_07])
            Order.filter.assert_called_with(group=cm.group)

    def test_get_dividend(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist='0.5 0.5', div_amount='40 100'))

        # Execute
        reps = 100000
        s = sum((cm.get_dividend() for _ in range(reps)))
        avg = s / reps

        # Assert
        self.assertAlmostEqual(avg, 70, delta=.3,
                               msg=f"Expecting the average dividend to be around 70, instead it was: {avg}")

    def test_supply_for_player(self):
        # Set-up
        p1 = self.basic_player(shares=0)
        p2 = self.basic_player(shares=2)

        o1 = get_order(player=p1, quantity=1, order_type=OFFER)
        o21 = get_order(player=p2, quantity=2, order_type=OFFER)
        o22 = get_order(player=p2, quantity=1, order_type=OFFER)
        o23 = get_order(player=p2, quantity=4, order_type=BID)

        cm = self.basic_setup(orders=[o1, o21, o22, o23])

        # Test
        s1 = cm.get_supply_for_player(p1)
        s2 = cm.get_supply_for_player(p2)

        # Assert
        self.assertEqual(s1, 1)
        self.assertEqual(s2, 3)

    def test_get_orders_for_players_single(self):
        p1 = self.basic_player(shares=0)
        p2 = self.basic_player(shares=2)
        p3 = self.basic_player(shares=2)

        o1 = get_order(player=p1, quantity=1, order_type=OFFER)
        o21 = get_order(player=p2, quantity=2, order_type=OFFER)
        o22 = get_order(player=p2, quantity=1, order_type=OFFER)
        o23 = get_order(player=p2, quantity=4, order_type=BID)
        o3 = get_order(player=p3, quantity=4, order_type=OFFER)

        cm = self.basic_setup(orders=[o1, o21, o22, o23, o3])

        # Test
        o_for_p1 = cm.get_orders_for_players(p1)
        o_for_p2 = cm.get_orders_for_players(p2)
        b_for_p2 = cm.get_orders_for_players(p2, order_type=OrderType.BID)
        o_for_p1p2 = cm.get_orders_for_players([p1, p2])

        # Assert
        self.assertEqual(set(o_for_p1), {o1})
        self.assertEqual(set(o_for_p2), {o21, o22})
        self.assertEqual(set(b_for_p2), {o23})
        self.assertEqual(set(o_for_p1p2), {o1, o21, o22})

    def test_get_shorting_players(self):
        # Set-up
        p1 = self.basic_player(shares=10)  # not selling
        p2 = self.basic_player(shares=10)  # selling all shares, not shorting
        p3 = self.basic_player(shares=10)  # Shorting
        p4 = self.basic_player(shares=-10)  # already short, and selling
        p5 = self.basic_player(shares=-10)  # already short, but not selling

        o2 = get_order(player=p2, quantity=10, order_type=OFFER)
        o3 = get_order(player=p3, quantity=11, order_type=OFFER)
        o4 = get_order(player=p4, quantity=1, order_type=OFFER)

        cm = self.basic_setup(orders=[o2, o3, o4])
        cm.group.get_players = MagicMock(return_value=[p1, p2, p3, p4, p5])

        # Test
        shorting = cm.get_shorting_players()

        # Assert
        self.assertEqual(set(shorting), {p3, p4})

    def test_screen_orders_for_over_shorting_no_limit(self):
        # Set-up
        cm = self.basic_setup()
        cm.group.get_short_limit = MagicMock(return_value=Group.NO_SHORT_LIMIT)
        cm.get_shorting_players = MagicMock()

        # Test
        cm.screen_orders_for_over_shorting()

        # Assert
        self.assertEqual(cm.get_shorting_players.call_count, 0)

    def tests_screen_orders_for_over_shorting_at_limit(self):
        # Set-up
        p1 = self.basic_player(shares=0)
        p2 = self.basic_player(shares=0)

        o1 = get_order(player=p1, quantity=2, order_type=OFFER)
        o2 = get_order(player=p2, quantity=2, order_type=OFFER)

        p = PropertyMock()
        type(o1).original_quantity = p
        type(o2).original_quantity = p

        cm = self.basic_setup(orders=[o1, o2])
        cm.group.get_players = MagicMock(return_value=[p1, p2])
        cm.group.get_short_limit = MagicMock(return_value=4)

        # Test
        cm.screen_orders_for_over_shorting()

        # Assert
        o1.original_quantity.assert_not_called()
        o2.original_quantity.assert_not_called()

    def tests_screen_orders_for_over_shorting_cancel_partial(self):
        # Set-up
        p1 = self.basic_player(shares=0)
        p2 = self.basic_player(shares=0)

        o1 = get_order(player=p1, quantity=2, price=5, order_type=OFFER, original_quantity=None)
        o2 = get_order(player=p2, quantity=2, price=4, order_type=OFFER, original_quantity=None)

        cm = self.basic_setup(orders=[o1, o2])
        cm.group.get_players = MagicMock(return_value=[p1, p2])
        cm.group.get_short_limit = MagicMock(return_value=3)

        # Test
        cm.screen_orders_for_over_shorting()

        # Assert
        self.assertEqual(o1.original_quantity, 2)
        self.assertEqual(o1.quantity, 1)
        self.assertIsNone(o2.original_quantity)
        self.assertEqual(o2.quantity, 2)

    def tests_screen_orders_for_over_shorting_cancel_full(self):
        # Set-up
        p1 = self.basic_player(shares=0)
        p2 = self.basic_player(shares=0)

        o1 = get_order(player=p1, quantity=2, price=5, order_type=OFFER, original_quantity=None)
        o2 = get_order(player=p2, quantity=2, price=4, order_type=OFFER, original_quantity=None)

        cm = self.basic_setup(orders=[o1, o2])
        cm.group.get_players = MagicMock(return_value=[p1, p2])
        cm.group.get_short_limit = MagicMock(return_value=1)

        # Test
        cm.screen_orders_for_over_shorting()

        # Assert
        self.assertEqual(o1.original_quantity, 2)
        self.assertEqual(o1.quantity, 0)
        self.assertEqual(o2.original_quantity, 2)
        self.assertEqual(o2.quantity, 1)

    def tests_screen_orders_for_over_shorting_overage_just_zeroed(self):
        # Set-up
        p1 = self.basic_player(shares=0)
        p2 = self.basic_player(shares=0)

        o1 = get_order(player=p1, quantity=2, price=5, order_type=OFFER, original_quantity=None)
        o2 = get_order(player=p2, quantity=2, price=4, order_type=OFFER, original_quantity=None)

        cm = self.basic_setup(orders=[o1, o2])
        cm.group.get_players = MagicMock(return_value=[p1, p2])
        cm.group.get_short_limit = MagicMock(return_value=0)

        # Test
        cm.screen_orders_for_over_shorting()

        # Assert
        self.assertEqual(o1.original_quantity, 2)
        self.assertEqual(o1.quantity, 0)
        self.assertEqual(o2.original_quantity, 2)
        self.assertEqual(o2.quantity, 0)

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
