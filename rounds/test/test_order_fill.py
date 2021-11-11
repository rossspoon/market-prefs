import unittest
from rounds.models import *
from rounds.call_market_price import OrderFill
from rounds.call_market_price import Principle
from unittest.mock import MagicMock
import pandas as pd
import numpy as np

BID = -1
OFFER = 1

b_10_05 = Order(order_type = BID, price = 10, quantity = 5)
b_10_06 = Order(order_type = BID, price = 10, quantity = 6)
b_11_05 = Order(order_type = BID, price = 11, quantity = 5)
b_11_06 = Order(order_type = BID, price = 11, quantity = 6)

o_05_05 = Order(order_type = OFFER, price = 5, quantity = 5)
o_05_06 = Order(order_type = OFFER, price = 5, quantity = 6)
o_06_05 = Order(order_type = OFFER, price = 6, quantity = 5)
o_06_07 = Order(order_type = OFFER, price = 6, quantity = 7)

def set_up_orders():
    orders = [b_10_06, o_05_06, b_11_06, o_05_05, b_11_05, o_06_05, b_10_05, o_06_07]
    for o in orders:
        o.quantity_final = None
    return orders

class TestCallMarketPrice(unittest.TestCase):

    def test_init(self):
        #Setup
        orders = set_up_orders()

        #Execute
        of = OrderFill(orders)

        #Assert
        self.assertEqual(of.orders, orders)
        self.assertEqual(of.bids, [b_11_06, b_11_05, b_10_06, b_10_05])
        self.assertEqual(of.offers, [o_05_05, o_05_06, o_06_05, o_06_07])

    def test_init_zero(self):
        #Execute
        of = OrderFill([])

        #Assert
        self.assertEqual(of.orders, [])
        self.assertEqual(of.bids, [])
        self.assertEqual(of.offers, [])

    def test_select_bids(self):
        #Setup
        b_10_05 = Order(order_type = BID, price = 10, quantity = 5)
        b_11_06 = Order(order_type = BID, price = 11, quantity = 6)
        b_12_05 = Order(order_type = BID, price = 12, quantity = 5)
        b_13_06 = Order(order_type = BID, price = 13, quantity = 6)
        orders = [ b_10_05, b_11_06, b_12_05, b_13_06 ]

        of = OrderFill(orders)
        
        #Execute
        bids = of.select_bids(12)

        #Assert
        self.assertEqual(bids, [b_13_06, b_12_05])

    def test_select_bids_hi(self):
        #Setup
        b_10_05 = Order(order_type = BID, price = 10, quantity = 5)
        b_11_06 = Order(order_type = BID, price = 11, quantity = 6)
        b_12_05 = Order(order_type = BID, price = 12, quantity = 5)
        b_13_06 = Order(order_type = BID, price = 13, quantity = 6)
        orders = [ b_10_05, b_11_06, b_12_05, b_13_06 ]

        of = OrderFill(orders)
        
        #Execute
        bids = of.select_bids(14)

        #Assert
        self.assertEqual(bids, [])

    def test_select_offers(self):
        #Setup
        o_10_05 = Order(order_type = OFFER, price = 10, quantity = 5)
        o_11_06 = Order(order_type = OFFER, price = 11, quantity = 6)
        o_12_05 = Order(order_type = OFFER, price = 12, quantity = 5)
        o_13_06 = Order(order_type = OFFER, price = 13, quantity = 6)
        orders = [ o_10_05, o_11_06, o_12_05, o_13_06 ]

        of = OrderFill(orders)
        
        #Execute
        offers = of.select_offers(12)

        #Assert
        self.assertEqual(offers, [o_10_05, o_11_06, o_12_05])

    def test_select_offers_lo(self):
        #Setup
        o_10_05 = Order(order_type = OFFER, price = 10, quantity = 5)
        o_11_06 = Order(order_type = OFFER, price = 11, quantity = 6)
        o_12_05 = Order(order_type = OFFER, price = 12, quantity = 5)
        o_13_06 = Order(order_type = OFFER, price = 13, quantity = 6)
        orders = [ o_10_05, o_11_06, o_12_05, o_13_06 ]

        of = OrderFill(orders)
        
        #Execute
        offers = of.select_offers(1)

        #Assert
        self.assertEqual(offers, [])


    def test_count_volume(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        bv = of.count_volume(of.bids)
        ov = of.count_volume(of.offers)

        #Assert
        self.assertEqual(bv, 22)
        self.assertEqual(ov, 23)

    def test_count_volume_zero(self):
        #Setup
        of = OrderFill([])

        #Execute
        bv = of.count_volume(of.bids)
        ov = of.count_volume(of.offers)

        #Assert
        self.assertEqual(bv, 0)
        self.assertEqual(ov, 0)


    def test_partial_fill_1(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.bids, 1)
        #Assert
        self.assertEqual(part_orders, [b_11_06])
        self.assertEqual(part_orders[0].quantity_final, 1)

    def test_partial_fill_2(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.bids, 7)
        #Assert
        self.assertEqual(part_orders, [b_11_06, b_11_05])
        self.assertEqual(part_orders[0].quantity_final, 6)
        self.assertEqual(part_orders[1].quantity_final, 1)

    def test_partial_fill_3(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.bids, 11)
        #Assert
        self.assertEqual(part_orders, [b_11_06, b_11_05])
        self.assertEqual(part_orders[0].quantity_final, 6)
        self.assertEqual(part_orders[1].quantity_final, 5)

    def test_partial_fill_4(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.bids, 12)
        #Assert
        self.assertEqual(part_orders, [b_11_06, b_11_05, b_10_06])
        self.assertEqual(part_orders[0].quantity_final, 6)
        self.assertEqual(part_orders[1].quantity_final, 5)
        self.assertEqual(part_orders[2].quantity_final, 1)
        self.assertEqual(of.bids[0].quantity_final, 6)
        self.assertEqual(of.bids[1].quantity_final, 5)
        self.assertEqual(of.bids[2].quantity_final, 1)
        self.assertIsNone(of.bids[3].quantity_final)

    def test_partial_fill_5(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.offers, 1)
        #Assert
        self.assertEqual(part_orders, [o_05_05])
        self.assertEqual(part_orders[0].quantity_final, 1)

    def test_partial_fill_6(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.offers, 5)
        #Assert
        self.assertEqual(part_orders, [o_05_05])
        self.assertEqual(part_orders[0].quantity_final, 5)

    def test_partial_fill_7(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.offers, 6)
        #Assert
        self.assertEqual(part_orders, [o_05_05, o_05_06])
        self.assertEqual(part_orders[0].quantity_final, 5)
        self.assertEqual(part_orders[1].quantity_final, 1)

    def test_partial_fill_8(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.offers, 11)
        #Assert
        self.assertEqual(part_orders, [o_05_05, o_05_06])
        self.assertEqual(part_orders[0].quantity_final, 5)
        self.assertEqual(part_orders[1].quantity_final, 6)
        self.assertEqual(of.offers[0].quantity_final, 5)
        self.assertEqual(of.offers[1].quantity_final, 6)
        self.assertIsNone(of.offers[2].quantity_final)
        self.assertIsNone(of.offers[3].quantity_final)


    def test_partial_fill_zero(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        part_orders = of.partial_fill(of.bids, 0)
        #Assert
        self.assertEqual(part_orders, [])

    def test_partial_fill_none(self):
        #Setup
        of = OrderFill([])

        #Execute
        part_orders = of.partial_fill(of.bids, 1)
        #Assert
        self.assertEqual(part_orders, [])

        #Execute
        part_orders = of.partial_fill(of.offers, 1)
        #Assert
        self.assertEqual(part_orders, [])

    def test_fill_order_hi(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        b, o = of.fill_orders(12)

        #Assert
        self.assertEqual(b, []) 
        self.assertEqual(o, []) 

    def test_fill_order_lo(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        b, o = of.fill_orders(1)

        #Assert
        self.assertEqual(b, []) 
        self.assertEqual(o, []) 

    def test_fill_order_matched(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        #Execute
        b, o = of.fill_orders(5)

        #Assert
        self.assertEqual(b, [b_11_06, b_11_05]) 
        self.assertEqual(o, [o_05_05, o_05_06]) 
        
        self.assertEqual(b_11_06.quantity_final, 6)
        self.assertEqual(b_11_05.quantity_final, 5)
        self.assertIsNone(b_10_06.quantity_final)
        self.assertIsNone(b_10_05.quantity_final)

        self.assertEqual(o_05_06.quantity_final, 6)
        self.assertEqual(o_05_05.quantity_final, 5)
        self.assertIsNone(o_06_07.quantity_final)
        self.assertIsNone(o_06_05.quantity_final)


    def test_count_filled_volume(self):
        #Setup
        orders = set_up_orders()
        of = OrderFill(orders)

        b_10_05.quantity_final = 1
        b_10_06.quantity_final = 2
        b_11_05.quantity_final = 3
        b_11_06

        o_05_05.quantity_final = 4
        o_05_06.quantity_final = 5
        o_06_05.quantity_final = 6
        o_06_07

        of = OrderFill([])

        #Execute
        cnt = of.count_filled_volume(orders)

        #Assert
        self.assertEqual(cnt, 21)
