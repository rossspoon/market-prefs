#!/usr/bin/env python
# coding: utf-8

import unittest
from rounds.models import *


class TestOrderErrorCodeMethods(unittest.TestCase):

    def test_combine(self):
        self.assertEqual(OrderErrorCode.PRICE_NEGATIVE.combine(OrderErrorCode.PRICE_NOT_NUM), 3)
        self.assertEqual(OrderErrorCode.PRICE_NEGATIVE.combine(OrderErrorCode.QUANT_NEGATIVE), 5)
        self.assertEqual(OrderErrorCode.PRICE_NEGATIVE.combine(OrderErrorCode.QUANT_NOT_NUM), 9)
        self.assertEqual(OrderErrorCode.PRICE_NEGATIVE.combine(OrderErrorCode.BAD_TYPE), 17)
        a = OrderErrorCode.PRICE_NEGATIVE.combine(OrderErrorCode.QUANT_NOT_NUM)
        a = OrderErrorCode.BAD_TYPE.combine(a)
        self.assertEqual(a, 25)

        self.assertEqual(OrderErrorCode.BAD_TYPE.desc, 'Select a type')
        self.assertEqual(OrderErrorCode.BAD_TYPE.field, OrderField.TYPE)

    def test_to_dict(self):
        for e in OrderErrorCode:
            d = e.to_dict()
            self.assertEqual(len(d), 3)
            self.assertEqual(d['value'], e.value)
            self.assertEqual(d['field'], e.field.value)
            self.assertEqual(d['desc'], e.desc)


class TestOrderMethods(unittest.TestCase):

    def test_to_dict(self):
        # Setup
        p = Player()
        p.id_in_group = 77
        g = Group()
        g.id = 78

        o = Order.create(
            player=p
            , group=g
            , order_type=-1
            , price=79
            , quantity=80
        )

        # Some initializing tests
        self.assertEqual(o.quantity_final, 0)
        self.assertFalse(o.is_buy_in)

        # Continue setup
        o.id = 76
        o.quantity_final = 81
        o.is_buy_in = True

        d = o.to_dict()

        self.assertEqual(d['oid'], 76)
        self.assertEqual(d['p_id'], 77)
        self.assertEqual(d['group_id'], 78)
        self.assertEqual(d['type'], -1)
        self.assertEqual(d['price'], 79)
        self.assertEqual(d['quantity'], 80)


if __name__ == '__main__':
    unittest.main()
