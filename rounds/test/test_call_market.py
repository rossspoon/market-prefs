import unittest
from rounds.models import *
from rounds.call_market import CallMarket
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
MARGIN_TARGET= .3

b_10_05 = Order(order_type = BID, price = 10, quantity = 5)
b_10_06 = Order(order_type = BID, price = 10, quantity = 6)
b_11_05 = Order(order_type = BID, price = 11, quantity = 5)
b_11_06 = Order(order_type = BID, price = 11, quantity = 6)

o_05_05 = Order(order_type = OFFER, price = 5, quantity = 5)
o_05_06 = Order(order_type = OFFER, price = 5, quantity = 6)
o_06_05 = Order(order_type = OFFER, price = 6, quantity = 5)
o_06_07 = Order(order_type = OFFER, price = 6, quantity = 7)

all_orders= [b_10_05, b_10_06, b_11_05, b_11_06, o_05_05, o_05_06, o_06_05, o_06_07]

class TestCallMarket(unittest.TestCase):

    def basic_group(self):
        group = Group()
        config_settings = dict(
                interest_rate = R
                , margin_ratio = MARGIN_RATIO
                , margin_premium = MARGIN_PREM
                , margin_target_ratio = MARGIN_TARGET)
        session = MagicMock()
        session.config = config_settings
        group.session = session

        return group

    def basic_setup(self, orders = all_orders):
        with patch.object(CallMarket, 'get_last_period_price', return_value=47) as mock_method:
            Order.filter = MagicMock(return_value = orders)
            group = self.basic_group()
            cm = CallMarket(group, NUM_ROUNDS)
        return cm

    def test_init(self):
        #Set up and
        with patch.object(CallMarket, 'get_last_period_price', return_value=47) as mock_method:
            Order.filter = MagicMock(return_value = all_orders)
            group = self.basic_group()

            #Execute
            cm = CallMarket(group, NUM_ROUNDS)

            #assert
            self.assertEqual(cm.num_rounds, NUM_ROUNDS)
            self.assertEqual(cm.group, group)
            self.assertEqual(cm.session, group.session)
            self.assertEqual(cm.bids, [b_10_05, b_10_06, b_11_05, b_11_06])
            self.assertEqual(cm.offers, [o_05_05, o_05_06, o_06_05, o_06_07])
            Order.filter.assert_called_with(group=group)
            self.assertEqual(cm.last_price, 47)
            CallMarket.get_last_period_price.assert_called_with()
            self.assertEqual( cm.interest_rate, R)
            self.assertEqual( cm.margin_ratio, MARGIN_RATIO)
            self.assertEqual( cm.margin_premium, MARGIN_PREM)
            self.assertEqual( cm.margin_target_ratio, MARGIN_TARGET)


    def test_get_orders_for_group(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group

        #Execute
        bids, offers = cm.get_orders_for_group()

        #Assert
        self.assertEqual(bids, [b_10_05, b_10_06, b_11_05, b_11_06])
        self.assertEqual(offers, [o_05_05, o_05_06, o_06_05, o_06_07])
        Order.filter.assert_called_with(group=cm.group)

    def test_get_orders_for_group_bids(self):
        #Set-up
        cm = self.basic_setup(orders= [b_10_05, b_10_06, b_11_05, b_11_06])
        group = cm.group

        #Execute
        bids, offers = cm.get_orders_for_group()

        #Assert
        self.assertEqual(bids, [b_10_05, b_10_06, b_11_05, b_11_06])
        self.assertEqual(offers, [])
        Order.filter.assert_called_with(group=cm.group)

    def test_get_orders_for_group_offers(self):
        #Set-up
        cm = self.basic_setup(orders = [o_05_05, o_05_06, o_06_05, o_06_07])
        group = cm.group

        #Execute
        bids, offers = cm.get_orders_for_group()

        #Assert
        self.assertEqual(bids, [])
        self.assertEqual(offers, [o_05_05, o_05_06, o_06_05, o_06_07])
        Order.filter.assert_called_with(group=cm.group)

    def test_get_last_period_price_round_1(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group
        group.round_number = 1
        cm.get_fundamental_value = MagicMock(return_value = 800)
        group.in_round = MagicMock(return_value = None)

        #Execute
        last_price = cm.get_last_period_price()

        #Assert
        self.assertEqual(last_price, 800)
        cm.get_fundamental_value.assert_called_with()
        group.in_round.assert_not_called()


    def test_get_last_period_price_round_2(self):
        #Set-up
        c = CallMarket.get_last_period_price
        cm = self.basic_setup()
        group = cm.group
        group.round_number = 2

        cm.get_fundamental_value = MagicMock(return_value = 800)
        last_round_group = self.basic_group()
        last_round_group.round_number = 1
        last_round_group.price = 801.1
        group.in_round = MagicMock(return_value = last_round_group)

        #Execute
        last_price = cm.get_last_period_price()

        #Assert
        self.assertEqual(last_price, 801)
        cm.get_fundamental_value.assert_not_called()
        group.in_round.assert_called_with(1)

    def test_set_up_future_player_last_round(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group

        player = Player(round_number = NUM_ROUNDS)
        player.in_round = MagicMock(return_value = None)
        
        #Execute
        cm.set_up_future_player(player)

        #Assert
        player.in_round.assert_not_called()

    def test_set_up_future_player_penultimate_round(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group

        player = Player(round_number = NUM_ROUNDS-1
                    , cash_result = 123
                    , shares_result = 456
                    , margin_violation = True
                    )
        next_player = Player(round_number = NUM_ROUNDS)
        player.in_round = MagicMock(return_value = next_player)
        
        #Execute
        cm.set_up_future_player(player, margin_violation=True)

        #Assert
        player.in_round.assert_called_with(NUM_ROUNDS)
        self.assertEqual(next_player.cash, 123)
        self.assertEqual(next_player.shares, 456)
        self.assertTrue(next_player.margin_violation)

    def test_get_dividend(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist = '0.5 0.5', div_amount = '40 100'))

        #Execute
        reps = 100000
        s = sum((cm.get_dividend() for i in range(reps) ))
        avg = s / reps

        #Assert
        self.assertTrue(abs(avg-70) < 0.2,
            msg="Expecting the avgerage dividend to be around 70, instead it was: {}".format(avg) )


    def test_get_fundamental_value_r0(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist = '0.5 0.5'
                                    , div_amount = '40 100'
                                    , interest_rate= 0))

        #Execute
        f = cm.get_fundamental_value()

        #Assert
        self.assertEqual(f, 0)

    def test_get_fundamental_value(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist = '0.5 0.5'
                                    , div_amount = '0 100'
                                    , interest_rate= 0.1))

        #Execute
        f = cm.get_fundamental_value()

        #Assert
        self.assertEqual(f, 500)
 
    def test_get_fundamental_value_exp_relevant(self):
        #Set-up
        cm = self.basic_setup()
        group = cm.group
        group.session.config.update(dict(div_dist = '0.5 0.5'
                                    , div_amount = '40 100'
                                    , interest_rate= 0.05))

        #Execute
        f = cm.get_fundamental_value()

        #Assert
        self.assertEqual(f, 1400)


    def test_get_orders_by_player(self):
        #Set-up
        p1 = Player(id=1234, id_in_group=1)
        p2 = Player(id=6789, id_in_group=2)

        p1_b_10_05 = Order(player = p1, order_type = BID, price = 10, quantity = 5)
        p2_b_10_06 = Order(player = p2, order_type = BID, price = 10, quantity = 6)
        p1_b_11_05 = Order(player = p1, order_type = BID, price = 11, quantity = 5)
        p2_b_11_06 = Order(player = p2, order_type = BID, price = 11, quantity = 6)

        p2_o_05_05 = Order(player = p2, order_type = OFFER, price = 5, quantity = 5)
        p1_o_05_06 = Order(player = p1, order_type = OFFER, price = 5, quantity = 6)
        p2_o_06_05 = Order(player = p2, order_type = OFFER, price = 6, quantity = 5)
        p1_o_06_07 = Order(player = p1, order_type = OFFER, price = 6, quantity = 7)

        orders = [p1_b_10_05, p2_b_10_06, p1_b_11_05, p2_b_11_06, p2_o_05_05, p1_o_05_06, p2_o_06_05, p1_o_06_07]
        cm = self.basic_setup(orders = orders)

        #Execute
        d = cm.get_orders_by_player()

        #Assert
        self.assertEqual(set(d.keys()), set([p1, p2]))
        self.assertEqual(d[p1], [p1_b_10_05, p1_b_11_05, p1_o_05_06, p1_o_06_07])
        self.assertEqual(d[p2], [p2_b_10_06, p2_b_11_06, p2_o_05_05, p2_o_06_05])


    def test_get_new_player_pos_net_buy(self):
        #Set-up
        cm = self.basic_setup()

        p = Player(shares = 100, cash = 200)

        o1 = Order(player = p, order_type = BID, quantity_final = 1)
        o2 = Order(player = p, order_type = BID, quantity_final = 2)
        o3 = Order(player = p, order_type = OFFER, quantity_final = 0)
        o4 = Order(player = p, order_type = OFFER, quantity_final = 1)
        orders = [o1, o2, o3, o4]

        # Execute
        d = cm.get_new_player_position(orders, p, 10, 15)

        # Assert
        self.assertEqual(d['p'], p)
        self.assertEqual(d['shares_transacted'], 2)
        self.assertEqual(d['shares_result'], 102)
        self.assertEqual(d['trans_cost'], -30)
        self.assertEqual(d['cash_after_trade'], 170)
        self.assertEqual(d['dividend_earned'], 1020)
        self.assertEqual(d['interest_earned'], 17)
        self.assertEqual(d['cash_result'], 200 - 30 + 1020 + 17)

    def test_get_new_player_pos_net_sell(self):
        #Set-up
        cm = self.basic_setup()

        p = Player(shares = 100, cash = 200)

        o1 = Order(player = p, order_type = BID, quantity_final = 1)
        o2 = Order(player = p, order_type = BID, quantity_final = 0)
        o3 = Order(player = p, order_type = OFFER, quantity_final = 2)
        o4 = Order(player = p, order_type = OFFER, quantity_final = 1)
        orders = [o1, o2, o3, o4]

        # Execute
        d = cm.get_new_player_position(orders, p, 10, 15)

        # Assert
        self.assertEqual(d['p'], p)
        self.assertEqual(d['shares_transacted'], -2)
        self.assertEqual(d['shares_result'], 98)
        self.assertEqual(d['trans_cost'], 30)
        self.assertEqual(d['cash_after_trade'], 230)
        self.assertEqual(d['dividend_earned'], 980)
        self.assertEqual(d['interest_earned'], 23)
        self.assertEqual(d['cash_result'], 200 + 30 + 980 + 23)

    def test_get_new_player_pos_no_orders(self):
        #Set-up
        cm = self.basic_setup()

        p = Player(shares = 100, cash = 200)

        # Execute
        d = cm.get_new_player_position([], p, 10, 15)

        # Assert
        self.assertEqual(d['p'], p)
        self.assertEqual(d['shares_transacted'], 0)
        self.assertEqual(d['shares_result'], 100)
        self.assertEqual(d['trans_cost'], 0)
        self.assertEqual(d['cash_after_trade'], 200)
        self.assertEqual(d['dividend_earned'], 1000)
        self.assertEqual(d['interest_earned'], 20)
        self.assertEqual(d['cash_result'], 200 + 0 + 1000 + 20)

    def test_is_margin_violation_zero_shares(self):
        #Set-up
        cm = self.basic_setup()
        data = dict(cash_result = 10, shares_result = 0)

        #Execute Test
        self.assertFalse(cm.is_margin_violation(data, 100))

    def test_is_margin_violation_zero_pos_shares(self):
        #Set-up
        cm = self.basic_setup()
        data = dict(cash_result = 100, shares_result = 1)

        #Execute Test
        self.assertFalse(cm.is_margin_violation(data, 100))

    def test_is_margin_violation_zero_neg_shares_under(self):
        #Set-up
        cm = self.basic_setup()
        data = dict(cash_result = 100, shares_result = -1)

        #Execute Test
        self.assertFalse(cm.is_margin_violation(data, 59))

    def test_is_margin_violation_zero_neg_shares_over(self):
        #Set-up
        cm = self.basic_setup()
        data = dict(cash_result = 100, shares_result = -1)

        #Execute #Assert
        self.assertTrue(cm.is_margin_violation(data, 60))

    def test_get_buy_in_players(self):
        #Set-up
        p1 = Player(margin_violation = False)
        p2 = Player(margin_violation = False)
        p3 = Player(margin_violation = True)
        p4 = Player(margin_violation = True)
        p5 = Player(margin_violation = True) # this player tests the non-data condiition
        players = [p1, p2, p3, p4, p5]

        d1 = dict(margin_violation_future = False)
        d2 = dict(margin_violation_future = True)
        d3 = dict(margin_violation_future = False)
        d4 = dict(margin_violation_future = True)
        data = {p1:d1, p2: d2, p3:d3, p4:d4}

        cm = self.basic_setup()

        #Execute
        bip = cm.get_buy_in_players(data, players)

        #assert
        self.assertEqual(bip, [p4])

    def test_generate_buy_in_order(self):
        #Set-up
        player = Player()
        data = dict(shares_result = -10, cash_result = 1000, p = player)
        cm = self.basic_setup()        
        #Order.create = MagicMock(return_value = Order())

        #Execute
        o = cm.generate_buy_in_order(data, 60)

        #Assert
        self.assertTrue(o.is_buy_in)
        self.assertEqual(o.order_type, BID)
        self.assertEqual(o.price, 75)
        self.assertEqual(o.quantity, 4)

