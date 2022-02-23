#!/usr/bin/env python
# coding: utf-8

import unittest

from otree.models import Session

from rounds.models import *
from unittest.mock import MagicMock
import common.SessionConfigFunctions as scf


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
            player=p,
            group=g,
            order_type=-1,
            price=79,
            quantity=80
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


def setup_margin_violation_tests(ratio=None, price=None, shares=None, cash=None, atd=None):
    config = {scf.SK_MARGIN_RATIO: ratio,
              scf.SK_AUTO_TRANS_DELAY: atd}
    session = Session()
    session.config = config
    group = Group()
    group.price = price
    p = Player()
    p.session = session
    p.group = group
    p.shares = shares
    p.cash = cash
    return p


def set_up_trans_status_tests(ratio=.4, delay=2, price=None, shares=None, cash=None, sell_period=1, buy_period=1):
    # Setup
    np = Player()
    np.round_number = 8
    np.periods_until_auto_sell = -1  # set these to a nonsensical value
    np.periods_until_auto_buy = -1  # that these get modified

    p = setup_margin_violation_tests(ratio=ratio, atd=delay, price=price, shares=shares, cash=cash)
    p.round_number = 7
    p.periods_until_auto_buy = buy_period
    p.periods_until_auto_sell = sell_period
    p.in_round_or_null = MagicMock(return_value=np)
    return np, p


class TestPlayerMethods(unittest.TestCase):
    def test_personal_stock_margin_0(self):
        # Setup
        p = Player()
        p.cash = 0
        p.shares = 1

        # Run
        pm = p.get_personal_stock_margin(1000)

        # Assert
        self.assertEqual(0, pm)

    def test_personal_stock_margin_neg_shares(self):
        # Setup
        p = Player()
        p.cash = 2000
        p.shares = -1

        # Run
        pm = p.get_personal_stock_margin(1000)

        # Assert
        self.assertEqual(0.5, pm)

    def test_personal_stock_margin_pos_shares(self):
        # Setup
        p = Player()
        p.cash = 2000
        p.shares = 1

        # Run
        pm = p.get_personal_stock_margin(1000)

        # Assert
        self.assertEqual(0.5, pm)

    def test_personal_cash_margin_0(self):
        # Setup
        p = Player()
        p.cash = 1000
        p.shares = 0

        # Run
        pm = p.get_personal_cash_margin(2000)

        # Assert
        self.assertEqual(0, pm)

    def test_personal_cash_margin_neg_cash(self):
        # Setup
        p = Player()
        p.cash = 1000
        p.shares = 1

        # Run
        pm = p.get_personal_cash_margin(2000)

        # Assert
        self.assertEqual(0.5, pm)

    def test_personal_cash_margin_pos_cash(self):
        # Setup
        p = Player()
        p.cash = 1000
        p.shares = 1

        # Run
        pm = p.get_personal_cash_margin(2000)

        # Assert
        self.assertEqual(0.5, pm)

    def test_is_short(self):
        # Setup  ------------  TEST 1
        p = Player()
        p.shares = -1

        # Run / Assert
        self.assertTrue(p.is_short())

        # Setup  ------------  TEST 2
        p.shares = 0

        # Run / Assert
        self.assertFalse(p.is_short())

        # Setup  ------------  TEST 3
        p.shares = 1

        # Run / Assert
        self.assertFalse(p.is_short())

    def test_is_debt(self):
        # Setup  ------------  TEST 1
        p = Player()
        p.cash = -1

        # Run / Assert
        self.assertTrue(p.is_debt())

        # Setup  ------------  TEST 2
        p.cash = 0

        # Run / Assert
        self.assertFalse(p.is_debt())

        # Setup  ------------  TEST 3
        p.cash = 1

        # Run / Assert
        self.assertFalse(p.is_debt())

    def test_is_bankrupt(self):
        # Setup  ------------  TEST 1
        p = Player()
        p.cash = -1
        p.shares = -1

        # Run / Assert
        self.assertTrue(p.is_bankrupt())

        # Setup  ------------  TEST 2
        p.cash = 1
        p.shares = -1

        # Run / Assert
        self.assertFalse(p.is_bankrupt())

        # Setup  ------------  TEST 3
        p.cash = -1
        p.shares = 1

        # Run / Assert
        self.assertFalse(p.is_bankrupt())

        # Setup  ------------  TEST 4
        p.cash = 1
        p.shares = 1

        # Run / Assert
        self.assertFalse(p.is_bankrupt())

    def test_in_round_or_null_exepct(self):
        # Setup
        p = Player()
        p.in_round = MagicMock(side_effect=InvalidRoundError)

        # Test / Assert
        self.assertIsNone(p.in_round_or_null(7), None)

    def test_in_round_or_null_valid(self):
        # Setup
        p = Player()
        p2 = Player()
        p2.id_in_group = 34
        p2.round_number = 56

        p.in_round = MagicMock(return_value=p2)

        # Test / Assert
        self.assertEqual(p.in_round_or_null(56), p2)

    # Short Margin Violation Tests
    def test_is_short_margin_violation(self):
        p = setup_margin_violation_tests(.4, 4000, -1, 10000)
        # Test / Assert
        self.assertTrue(p.is_short_margin_violation())

    def test_is_short_margin_violation_not_short(self):
        p = setup_margin_violation_tests(.4, 4000, 1, 10000)
        # Test / Assert
        self.assertFalse(p.is_short_margin_violation())

    def test_is_short_margin_violation_not_mv(self):
        p = setup_margin_violation_tests(.4, 3999, -1, 10000)
        # Test / Assert
        self.assertFalse(p.is_short_margin_violation())

    def test_is_short_margin_violation_not_mv2(self):
        p = setup_margin_violation_tests(.4, 4000, -1, 10001)
        # Test / Assert
        self.assertFalse(p.is_short_margin_violation())

    def test_is_short_margin_violation_bankrupt(self):
        p = setup_margin_violation_tests(.4, -4000, -1, 10001)
        # Test / Assert
        self.assertFalse(p.is_short_margin_violation())

    # End Short Margin Violation Tests

    # Cash Margin Violation Tests
    def test_is_debt_margin_violation(self):
        p = setup_margin_violation_tests(.4, 4000, 2, -4000)
        # Test / Assert
        self.assertTrue(p.is_debt_margin_violation())

    def test_is_debt_margin_violation_not_debt(self):
        p = setup_margin_violation_tests(.4, 4000, 2, 4000)
        # Test / Assert
        self.assertFalse(p.is_debt_margin_violation())

    def test_is_debt_margin_violation_not_mv(self):
        p = setup_margin_violation_tests(.4, 4001, -2, 4000)
        # Test / Assert
        self.assertFalse(p.is_debt_margin_violation())

    def test_is_debt_margin_violation_not_mv2(self):
        p = setup_margin_violation_tests(.4, 4000, -2, 3999)
        # Test / Assert
        self.assertFalse(p.is_debt_margin_violation())

    def test_is_debt_margin_violation_bankrupt(self):
        p = setup_margin_violation_tests(.4, -4000, -2, 3999)
        # Test / Assert
        self.assertFalse(p.is_debt_margin_violation())

    # End Cash Margin Violation Tests

    def test_calculate_delay(self):
        p = Player

        self.assertEqual(p.calculate_delay(None, 7), 7)
        self.assertEqual(p.calculate_delay(1, 7), 0)
        self.assertEqual(p.calculate_delay(0, 7), 0)
        self.assertEqual(p.calculate_delay(-1, 7), 0)

    # BEGIN determine_auto_trans_status TESTS
    def test_determine_auto_trans_status_no_next(self):
        # Setup
        np, p = set_up_trans_status_tests()
        p.in_round_or_null = MagicMock(return_value=None)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertEqual(np.periods_until_auto_buy, -1)
        self.assertEqual(np.periods_until_auto_sell, -1)

    def test_determine_auto_trans_status_bankrupt(self):
        # Setup
        np, p = set_up_trans_status_tests(shares=-1, cash=-1)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(np.periods_until_auto_buy)
        self.assertIsNone(np.periods_until_auto_sell)

    def test_trans_status_no_mv_short_reset(self):
        np, p = set_up_trans_status_tests(price=1000, shares=-2, cash=5001)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(np.periods_until_auto_buy)
        self.assertIsNone(np.periods_until_auto_sell)

    def test_trans_status_mv_short_base(self):
        # noinspection PyTypeChecker
        np, p = set_up_trans_status_tests(price=1000, shares=-2, cash=5000, delay=7, buy_period=None)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertEqual(np.periods_until_auto_buy, 7)
        self.assertIsNone(np.periods_until_auto_sell)

    def test_trans_status_mv_short_dec(self):
        np, p = set_up_trans_status_tests(price=1000, shares=-2, cash=5000, delay=7, buy_period=4)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertEqual(np.periods_until_auto_buy, 3)
        self.assertIsNone(np.periods_until_auto_sell)

    def test_trans_status_mv_short_floor(self):
        np, p = set_up_trans_status_tests(price=1000, shares=-2, cash=5000, delay=7, buy_period=0)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertEqual(np.periods_until_auto_buy, 0)
        self.assertIsNone(np.periods_until_auto_sell)

    def test_trans_status_no_mv_debt_reset(self):
        np, p = set_up_trans_status_tests(price=1000, shares=5, cash=-1999)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(np.periods_until_auto_buy)
        self.assertIsNone(np.periods_until_auto_sell)

    def test_trans_status_mv_debt_base(self):
        # noinspection PyTypeChecker
        np, p = set_up_trans_status_tests(price=1000, shares=5, cash=-2000, delay=7, sell_period=None)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(np.periods_until_auto_buy)
        self.assertEqual(np.periods_until_auto_sell, 7)

    def test_trans_status_mv_debt_dec(self):
        np, p = set_up_trans_status_tests(price=1000, shares=5, cash=-2000, delay=7, sell_period=4)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(np.periods_until_auto_buy)
        self.assertEqual(np.periods_until_auto_sell, 3)

    def test_trans_status_mv_debt_floor(self):
        np, p = set_up_trans_status_tests(price=1000, shares=5, cash=-2000, delay=7, sell_period=0)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(np.periods_until_auto_buy)
        self.assertEqual(np.periods_until_auto_sell, 0)

    # END determine_auto_trans_status TESTS

    prop_names = ['cash', 'shares', 'periods_until_auto_buy', 'periods_until_auto_sell', 'shares_transacted',
                  'trans_cost', 'cash_after_trade', 'interest_earned', 'dividend_earned', 'cash_result',
                  'shares_result']

    prop_names_from_dict = ['periods_until_auto_buy', 'periods_until_auto_sell', 'shares_transacted',
                            'trans_cost', 'cash_after_trade', 'interest_earned', 'dividend_earned', 'cash_result',
                            'shares_result']

    def test_to_dict_none(self):
        # Setup
        p = Player()

        # Test
        d = p.to_dict()

        # Assert
        for prop in self.prop_names:
            self.assertIsNone(d.get(prop), msg=f"testing {prop}")

    def test_to_dict(self):
        # Setup
        p = Player()
        test_values = {prop: n for n, prop in enumerate(self.prop_names)}
        for prop in test_values:
            setattr(p, prop, test_values.get(prop))

        d = p.to_dict()  # Test

        # Assert
        for prop in self.prop_names:
            self.assertEqual(d.get(prop), test_values.get(prop), msg=f"testing {prop}")

    def test_update_from_dict_none(self):
        # Setup
        p = Player()
        for n, prop in enumerate(self.prop_names_from_dict):
            setattr(p, prop, n)
        d = {}

        # Test
        p.update_from_dict(d)

        # Assert
        for prop in self.prop_names_from_dict:
            self.assertIsNone(p.field_maybe_none(prop), msg=f"testing {prop}")

    def test_update_from_dict(self):
        # Setup
        p = Player()
        test_values = {prop: n for n, prop in enumerate(self.prop_names_from_dict)}

        # Test
        p.update_from_dict(test_values)

        # Assert
        for prop in test_values:
            self.assertEqual(getattr(p, prop), test_values.get(prop), msg=f"testing {prop}")


if __name__ == '__main__':
    unittest.main()
