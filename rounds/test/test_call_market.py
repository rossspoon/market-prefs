import unittest
from rounds.models import *
from rounds.call_market import CallMarket, get_orders_by_player
from rounds.call_market import DataForPlayer
from unittest.mock import MagicMock
from unittest.mock import patch
import pandas as pd
import numpy as np

BID = OrderType.BID.value
OFFER = OrderType.OFFER.value
NUM_ROUNDS = 5
R = .1
MARGIN_RATIO = .6
MARGIN_PREM = 1.25
MARGIN_TARGET = .3

b_10_05 = Order(order_type=BID, price=10, quantity=5)
b_10_06 = Order(order_type=BID, price=10, quantity=6)
b_11_05 = Order(order_type=BID, price=11, quantity=5)
b_11_06 = Order(order_type=BID, price=11, quantity=6)

o_05_05 = Order(order_type=OFFER, price=5, quantity=5)
o_05_06 = Order(order_type=OFFER, price=5, quantity=6)
o_06_05 = Order(order_type=OFFER, price=6, quantity=5)
o_06_07 = Order(order_type=OFFER, price=6, quantity=7)

all_orders = [b_10_05, b_10_06, b_11_05, b_11_06, o_05_05, o_05_06, o_06_05, o_06_07]


class TestCallMarket(unittest.TestCase):

    def basic_group(self):
        group = Group()
        config_settings = dict(
            interest_rate=R
            , margin_ratio=MARGIN_RATIO
            , margin_premium=MARGIN_PREM
            , margin_target_ratio=MARGIN_TARGET)
        session = MagicMock()
        session.config = config_settings
        group.session = session

        return group

    def basic_setup(self, orders=all_orders):
        with patch.object(CallMarket, 'get_last_period_price', return_value=47) as mock_method:
            with patch.object(Order, 'filter', return_value=orders) as filter_mock:
                Order.filter = MagicMock(return_value=orders)
                group = self.basic_group()
                cm = CallMarket(group, NUM_ROUNDS)
        return cm

    def test_init(self):
        # Set up and
        with patch.object(CallMarket, 'get_last_period_price', return_value=47) as mock_method:
            with patch.object(Order, 'filter', return_value=all_orders) as filter_mock:
                group = self.basic_group()

                # Execute
                cm = CallMarket(group, NUM_ROUNDS)

                # assert
                self.assertEqual(cm.num_rounds, NUM_ROUNDS)
                self.assertEqual(cm.group, group)
                self.assertEqual(cm.session, group.session)
                self.assertEqual(cm.bids, [b_10_05, b_10_06, b_11_05, b_11_06])
                self.assertEqual(cm.offers, [o_05_05, o_05_06, o_06_05, o_06_07])
                Order.filter.assert_called_with(group=group)
                self.assertEqual(cm.last_price, 47)
                CallMarket.get_last_period_price.assert_called_with()
                self.assertEqual(cm.interest_rate, R)
                self.assertEqual(cm.margin_ratio, MARGIN_RATIO)
                self.assertEqual(cm.margin_premium, MARGIN_PREM)
                self.assertEqual(cm.margin_target_ratio, MARGIN_TARGET)

    def test_get_orders_for_group(self):
        with patch.object(Order, 'filter', return_value=all_orders) as filter_mock:
            # Set-up
            cm = self.basic_setup()
            group = cm.group

            # Execute
            bids, offers = cm.get_orders_for_group()

            # Assert
            self.assertEqual(bids, [b_10_05, b_10_06, b_11_05, b_11_06])
            self.assertEqual(offers, [o_05_05, o_05_06, o_06_05, o_06_07])
            Order.filter.assert_called_with(group=cm.group)

    def test_get_orders_for_group_bids(self):
        orders = [b_10_05, b_10_06, b_11_05, b_11_06]
        with patch.object(Order, 'filter', return_value=orders) as filter_mock:
            # Set-up
            cm = self.basic_setup(orders=orders)
            group = cm.group

            # Execute
            bids, offers = cm.get_orders_for_group()

            # Assert
            self.assertEqual(bids, [b_10_05, b_10_06, b_11_05, b_11_06])
            self.assertEqual(offers, [])
            Order.filter.assert_called_with(group=cm.group)

    def test_get_orders_for_group_offers(self):
        orders = [o_05_05, o_05_06, o_06_05, o_06_07]
        with patch.object(Order, 'filter', return_value=orders) as filter_mock:
            # Set-up
            cm = self.basic_setup(orders=orders)
            group = cm.group

            # Execute
            bids, offers = cm.get_orders_for_group()

            # Assert
            self.assertEqual(bids, [])
            self.assertEqual(offers, [o_05_05, o_05_06, o_06_05, o_06_07])
            Order.filter.assert_called_with(group=cm.group)

    def test_get_last_period_price_round_1(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group
        group.round_number = 1
        cm.get_fundamental_value = MagicMock(return_value=800)
        group.in_round = MagicMock(return_value=None)

        # Execute
        last_price = cm.get_last_period_price()

        # Assert
        self.assertEqual(last_price, 800)
        cm.get_fundamental_value.assert_called_with()
        group.in_round.assert_not_called()

    def test_get_last_period_price_round_2(self):
        # Set-up
        c = CallMarket.get_last_period_price
        cm = self.basic_setup()
        group = cm.group
        group.round_number = 2

        cm.get_fundamental_value = MagicMock(return_value=800)
        last_round_group = self.basic_group()
        last_round_group.round_number = 1
        last_round_group.price = 801.1
        group.in_round = MagicMock(return_value=last_round_group)

        # Execute
        last_price = cm.get_last_period_price()

        # Assert
        self.assertEqual(last_price, 801)
        cm.get_fundamental_value.assert_not_called()
        group.in_round.assert_called_with(1)

    def test_set_up_future_player_last_round(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group

        player = Player(round_number=NUM_ROUNDS)
        player.in_round = MagicMock(return_value=None)

        # Execute
        cm.set_up_future_player(player)

        # Assert
        player.in_round.assert_not_called()

    def test_set_up_future_player_penultimate_round(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group

        player = Player(round_number=NUM_ROUNDS - 1
                        , cash_result=123
                        , shares_result=456
                        , margin_violation=True
                        )
        next_player = Player(round_number=NUM_ROUNDS)
        player.in_round = MagicMock(return_value=next_player)

        # Execute
        cm.set_up_future_player(player, margin_violation=True)

        # Assert
        player.in_round.assert_called_with(NUM_ROUNDS)
        self.assertEqual(next_player.cash, 123)
        self.assertEqual(next_player.shares, 456)
        self.assertTrue(next_player.margin_violation)

    def test_get_dividend(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist='0.5 0.5', div_amount='40 100'))

        # Execute
        reps = 100000
        s = sum((cm.get_dividend() for i in range(reps)))
        avg = s / reps

        # Assert
        self.assertTrue(abs(avg - 70) < 0.2,
                        msg="Expecting the avgerage dividend to be around 70, instead it was: {}".format(avg))

    def test_get_fundamental_value_r0(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist='0.5 0.5'
                                         , div_amount='40 100'
                                         , interest_rate=0))

        # Execute
        f = cm.get_fundamental_value()

        # Assert
        self.assertEqual(f, 0)

    def test_get_fundamental_value(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist='0.5 0.5'
                                         , div_amount='0 100'
                                         , interest_rate=0.1))

        # Execute
        f = cm.get_fundamental_value()

        # Assert
        self.assertEqual(f, 500)

    def test_get_fundamental_value_exp_relevant(self):
        # Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist='0.5 0.5'
                                         , div_amount='40 100'
                                         , interest_rate=0.05))

        # Execute
        f = cm.get_fundamental_value()

        # Assert
        self.assertEqual(f, 1400)

    def test_get_orders_by_player(self):
        # Set-up
        p1 = Player(id=1234, id_in_group=1)
        p2 = Player(id=6789, id_in_group=2)

        p1_b_10_05 = Order(player=p1, order_type=BID, price=10, quantity=5)
        p2_b_10_06 = Order(player=p2, order_type=BID, price=10, quantity=6)
        p1_b_11_05 = Order(player=p1, order_type=BID, price=11, quantity=5)
        p2_b_11_06 = Order(player=p2, order_type=BID, price=11, quantity=6)

        p2_o_05_05 = Order(player=p2, order_type=OFFER, price=5, quantity=5)
        p1_o_05_06 = Order(player=p1, order_type=OFFER, price=5, quantity=6)
        p2_o_06_05 = Order(player=p2, order_type=OFFER, price=6, quantity=5)
        p1_o_06_07 = Order(player=p1, order_type=OFFER, price=6, quantity=7)

        orders = [p1_b_10_05, p2_b_10_06, p1_b_11_05, p2_b_11_06, p2_o_05_05, p1_o_05_06, p2_o_06_05, p1_o_06_07]
        cm = self

        # Execute
        d = get_orders_by_player(orders)

        # Assert
        self.assertEqual(set(d.keys()), set([p1, p2]))
        self.assertEqual(d[p1], [p1_b_10_05, p1_b_11_05, p1_o_05_06, p1_o_06_07])
        self.assertEqual(d[p2], [p2_b_10_06, p2_b_11_06, p2_o_05_05, p2_o_06_05])


class TestDataForPlayer(unittest.TestCase):

    def basic_setup(self):
        return Player(shares=100, cash=200)

    def basic_test_object(self, orders):
        p = self.basic_setup()
        for o in orders:
            o.player = p

        return DataForPlayer(p, orders)

    def test_init(self):
        # set-up
        p = self.basic_setup()

        # Execute
        d4p = DataForPlayer(p, [])

        # Assert
        self.assertEqual(d4p.orders, [])
        self.assertEqual(d4p.player, p)
        self.assertIsNone(d4p.shares_result)
        self.assertIsNone(d4p.shares_transacted)
        self.assertIsNone(d4p.trans_cost)
        self.assertIsNone(d4p.cash_after_trade)
        self.assertIsNone(d4p.dividend_earned)
        self.assertIsNone(d4p.interest_earned)
        self.assertIsNone(d4p.cash_result)
        self.assertFalse(d4p.margin_violation_future)

    def test_get_new_player_pos_net_buy(self):
        # Set-up
        o1 = Order(order_type=BID, quantity_final=1)
        o2 = Order(order_type=BID, quantity_final=2)
        o3 = Order(order_type=OFFER, quantity_final=0)
        o4 = Order(order_type=OFFER, quantity_final=1)
        orders = [o1, o2, o3, o4]

        d4p = self.basic_test_object(orders)

        # Execute
        d4p.get_new_player_position(10, R, 15)

        # Assert
        self.assertEqual(d4p.shares_transacted, 2)
        self.assertEqual(d4p.shares_result, 102)
        self.assertEqual(d4p.trans_cost, -30)
        self.assertEqual(d4p.cash_after_trade, 170)
        self.assertEqual(d4p.dividend_earned, 1020)
        self.assertEqual(d4p.interest_earned, 17)
        self.assertEqual(d4p.cash_result, 200 - 30 + 1020 + 17)

    def test_get_new_player_pos_net_sell(self):
        # Set-up
        o1 = Order(order_type=BID, quantity_final=1)
        o2 = Order(order_type=BID, quantity_final=0)
        o3 = Order(order_type=OFFER, quantity_final=2)
        o4 = Order(order_type=OFFER, quantity_final=1)
        orders = [o1, o2, o3, o4]

        d4p = self.basic_test_object(orders)

        # Execute
        d4p.get_new_player_position(10, R, 15)

        # Assert
        self.assertEqual(d4p.shares_transacted, -2)
        self.assertEqual(d4p.shares_result, 98)
        self.assertEqual(d4p.trans_cost, 30)
        self.assertEqual(d4p.cash_after_trade, 230)
        self.assertEqual(d4p.dividend_earned, 980)
        self.assertEqual(d4p.interest_earned, 23)
        self.assertEqual(d4p.cash_result, 200 + 30 + 980 + 23)

    def test_get_new_player_pos_no_orders(self):
        # Set-up
        d4p = self.basic_test_object([])

        # Execute
        d4p.get_new_player_position(10, R, 15)

        # Assert
        self.assertEqual(d4p.shares_transacted, 0)
        self.assertEqual(d4p.shares_result, 100)
        self.assertEqual(d4p.trans_cost, 0)
        self.assertEqual(d4p.cash_after_trade, 200)
        self.assertEqual(d4p.dividend_earned, 1000)
        self.assertEqual(d4p.interest_earned, 20)
        self.assertEqual(d4p.cash_result, 200 + 0 + 1000 + 20)

    def test_is_margin_violation_zero_shares(self):
        # Set-up
        d4p = self.basic_test_object([])
        d4p.cash_result = 10
        d4p.shares_result = 0

        # Execute
        d4p.set_mv_future(MARGIN_RATIO, 60)

        # Assert
        self.assertFalse(d4p.margin_violation_future)

    def test_is_margin_violation_pos_shares(self):
        # Set-up
        d4p = self.basic_test_object([])
        d4p.cash_result = 100
        d4p.shares_result = 1

        # Execute
        d4p.set_mv_future(MARGIN_RATIO, 60)

        # Assert
        self.assertFalse(d4p.margin_violation_future)

    def test_is_margin_violation_neg_shares_under(self):
        # Set-up
        d4p = self.basic_test_object([])
        d4p.cash_result = 100
        d4p.shares_result = -1

        # Execute
        d4p.set_mv_future(MARGIN_RATIO, 49)

        # Assert
        self.assertFalse(d4p.margin_violation_future)

    def test_is_margin_violation_neg_shares_over(self):
        # Set-up
        d4p = self.basic_test_object([])
        d4p.cash_result = 100
        d4p.shares_result = -1

        # Execute
        d4p.set_mv_future(MARGIN_RATIO, 50)

        # Assert
        self.assertFalse(d4p.margin_violation_future)

    def test_get_buy_in_players(self):
        # Set-up
        p1 = Player(margin_violation=False)
        p2 = Player(margin_violation=False)
        p3 = Player(margin_violation=True)
        p4 = Player(margin_violation=True)

        d1 = DataForPlayer(p1, [])
        d1.margin_violation_future = False
        d2 = DataForPlayer(p2, [])
        d2.margin_violation_future = True
        d3 = DataForPlayer(p3, [])
        d3.margin_violation_future = False
        d4 = DataForPlayer(p4, [])
        d4.margin_violation_future = True

        # Execute / Assert
        self.assertFalse(d1.is_buy_in_required())
        self.assertFalse(d2.is_buy_in_required())
        self.assertFalse(d3.is_buy_in_required())
        self.assertTrue(d4.is_buy_in_required())

    def test_generate_buy_in_order(self):
        # Set-up
        d4p = self.basic_test_object([])
        d4p.shares_result = -10
        d4p.cash_result = 1000
        # Order.create = MagicMock(return_value = Order())

        # Execute
        o = d4p.generate_buy_in_order(60, MARGIN_PREM, MARGIN_TARGET)

        # Assert
        self.assertTrue(o.is_buy_in)
        self.assertEqual(o.order_type, BID)
        self.assertEqual(o.price, 75)
        self.assertEqual(o.quantity, 4)
