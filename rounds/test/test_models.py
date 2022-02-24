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
    group.round_number = 5
    group.session = session
    group.get_last_period_price = MagicMock(return_value=price)

    p = Player()
    p.round_number = 5
    p.session = session
    p.group = group
    p.shares = shares
    p.cash = cash
    return p


def set_up_trans_status_tests(ratio=.4, delay=2, price=None, shares=None, cash=None, sell_period=1, buy_period=1):
    # Setup
    last_p = Player()
    last_p.round_number = 6
    last_p.periods_until_auto_buy = buy_period
    last_p.periods_until_auto_sell = sell_period

    p = setup_margin_violation_tests(ratio=ratio, atd=delay, price=price, shares=shares, cash=cash)
    p.round_number = 7

    p.in_round_or_null = MagicMock(return_value=last_p)
    return p


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

    def test_in_round_or_null_except(self):
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
    def test_determine_auto_trans_status_bankrupt(self):
        # Setup
        p = set_up_trans_status_tests(shares=-1, cash=-1)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(p.periods_until_auto_buy)
        self.assertIsNone(p.periods_until_auto_sell)

    def test_trans_status_no_mv_short_reset(self):
        p = set_up_trans_status_tests(price=1000, shares=-2, cash=5001)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(p.periods_until_auto_buy)
        self.assertIsNone(p.periods_until_auto_sell)

    def test_trans_status_mv_short_base(self):
        # noinspection PyTypeChecker
        p = set_up_trans_status_tests(price=1000, shares=-2, cash=5000, delay=7, buy_period=None)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertEqual(p.periods_until_auto_buy, 7)
        self.assertIsNone(p.periods_until_auto_sell)

    def test_trans_status_mv_short_dec(self):
        p = set_up_trans_status_tests(price=1000, shares=-2, cash=5000, delay=7, buy_period=4)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertEqual(p.periods_until_auto_buy, 3)
        self.assertIsNone(p.periods_until_auto_sell)

    def test_trans_status_mv_short_floor(self):
        p = set_up_trans_status_tests(price=1000, shares=-2, cash=5000, delay=7, buy_period=0)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertEqual(p.periods_until_auto_buy, 0)
        self.assertIsNone(p.periods_until_auto_sell)

    def test_trans_status_no_mv_debt_reset(self):
        p = set_up_trans_status_tests(price=1000, shares=5, cash=-1999)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(p.periods_until_auto_buy)
        self.assertIsNone(p.periods_until_auto_sell)

    def test_trans_status_mv_debt_base(self):
        # noinspection PyTypeChecker
        p = set_up_trans_status_tests(price=1000, shares=5, cash=-2000, delay=7, sell_period=None)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(p.periods_until_auto_buy)
        self.assertEqual(p.periods_until_auto_sell, 7)

    def test_trans_status_mv_debt_dec(self):
        p = set_up_trans_status_tests(price=1000, shares=5, cash=-2000, delay=7, sell_period=4)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(p.periods_until_auto_buy)
        self.assertEqual(p.periods_until_auto_sell, 3)

    def test_trans_status_mv_debt_floor(self):
        p = set_up_trans_status_tests(price=1000, shares=5, cash=-2000, delay=7, sell_period=0)

        # Test
        p.determine_auto_trans_status()

        # Assert
        self.assertIsNone(p.periods_until_auto_buy)
        self.assertEqual(p.periods_until_auto_sell, 0)

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

    def assert_equal_or_none(self, exp, actual):
        if actual is not None:
            self.assertEqual(exp, actual)
        else:
            self.assertIsNone(actual)

    def generic_forecast_test(self, f0=None, price=None, reward=None, error=None):
        # Setup
        p = Player()
        p.f0 = f0
        p.cash_result = 0
        p.forecast_reward = 0

        # Test
        p.determine_forecast_reward(price)

        # Assert
        self.assert_equal_or_none(p.forecast_reward, reward)
        self.assert_equal_or_none(p.forecast_error, error)
        self.assert_equal_or_none(p.cash_result, reward)

    def test_forecasts(self):
        self.generic_forecast_test(f0=1000, price=750, reward=500, error=250)
        self.generic_forecast_test(f0=1001, price=750, reward=0, error=251)
        self.generic_forecast_test(f0=500, price=750, reward=500, error=250)
        self.generic_forecast_test(f0=499, price=750, reward=0, error=251)


class TestGroupMethods(unittest.TestCase):
    def test_in_round_or_none_bad_round(self):
        g = Group()
        g.round_number = 5
        g.in_round = MagicMock(side_effect=InvalidRoundError)

        # Test / Assert
        self.assertIsNone(g.in_round_or_none(7))

    def test_in_round_or_null_valid(self):
        # Setup
        g = Group()
        g2 = Group()
        g2.id_in_group = 34
        g2.round_number = 56

        g.in_round = MagicMock(return_value=g2)

        # Test / Assert
        self.assertEqual(g.in_round_or_none(56), g2)

    def test_get_last_period_price_bad_round_init_value(self):
        # Set-up
        group = Group()
        config = {scf.SK_INITIAL_PRICE: 800}
        session = Session()
        session.config = config
        group.session = session
        group.in_round = MagicMock(side_effect=InvalidRoundError)
        group.round_number = 1

        # Execute
        last_price = group.get_last_period_price()

        # Assert
        self.assertEqual(last_price, 800)
        group.in_round.assert_called_with(0)

    def test_get_last_period_price_bad_round_fund_val(self):
        # Set-up
        group = Group()
        config = dict(div_dist='0.5 0.5',
                      div_amount='40 100',
                      interest_rate=.05)
        session = Session()
        session.config = config
        group.session = session
        group.in_round = MagicMock(side_effect=InvalidRoundError)
        group.round_number = 1

        # Execute
        last_price = group.get_last_period_price()

        # Assert
        self.assertEqual(last_price, 1400)
        group.in_round.assert_called_with(0)

    def test_get_last_period_price_has_prev(self):
        # Set-up
        group = Group()
        group.round_number = 2

        last_round_group = Group()
        last_round_group.round_number = 1
        last_round_group.price = 801.1
        group.in_round = MagicMock(return_value=last_round_group)

        # Execute
        last_price = group.get_last_period_price()

        # Assert
        self.assertEqual(last_price, 801)
        group.in_round.assert_called_with(1)

    def test_copy_results_from_previous_round_first(self):
        # Set-up
        player = Player()
        player.round_number = 1
        player.in_round = MagicMock(side_effect=InvalidRoundError)

        # Execute
        player.copy_results_from_previous_round()

        # Assert
        player.in_round.assert_called_with(0)

    def test_copy_results_from_previous_round_second_round(self):
        # Set-up
        p = Player()
        p.round_number = 4

        last_p = Player()
        last_p.round_number = 3
        last_p.cash_result = 123
        last_p.shares_result = 456
        p.in_round = MagicMock(return_value=last_p)

        # Execute
        p.copy_results_from_previous_round()

        # Assert
        p.in_round.assert_called_with(3)
        self.assertEqual(p.cash, 123)
        self.assertEqual(p.shares, 456)


if __name__ == '__main__':
    unittest.main()
