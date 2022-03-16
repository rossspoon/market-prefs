import unittest

import numpy as np
import pandas as pd

from rounds.call_market_price import MarketPrice, ensure_tuples, get_cxq
from rounds.call_market_price import Principle
from rounds.models import *


def o(price=None, quantity=None):
    _o = Order()
    _o.price = price
    _o.quantity = quantity
    return _o


# noinspection DuplicatedCode
class TestCallMarketPrice(unittest.TestCase):

    def test_init(self):
        bids = [o(price=10, quantity=20),
                o(price=11, quantity=21)]
        offers = [o(price=5, quantity=15),
                  o(price=6, quantity=16)]

        # Basic instantiation with lists of orders
        mp = MarketPrice(bids, offers)
        df = mp.price_df
        expected_prices = {5, 6, 10, 11}
        actual_prices = df.price.values
        expected_vol = {20, 21, 15, 16}
        actual_vol = df.volume.values

        self.assertEqual(df.shape, (4, 2))
        self.assertEqual(expected_prices, set(actual_prices))
        self.assertEqual(expected_vol, set(actual_vol))

        # Basic instantiation with lists of orders
        # in this test we also see volume around the price of 11
        bids_tup = [(10, 20), (11, 21), (11, 5)]
        offers_tup = [(5, 15), (6, 16), (11, 2)]
        mp = MarketPrice(bids_tup, offers_tup)
        df = mp.price_df
        expected_prices = {5, 6, 10, 11}
        actual_prices = df.price.values
        expected_vol = {20, 28, 15, 16}
        actual_vol = df.volume.values

        self.assertEqual(df.shape, (4, 2))
        self.assertEqual(expected_prices, set(actual_prices))
        self.assertEqual(expected_vol, set(actual_vol))

        # null input
        mp = MarketPrice(None, offers_tup)
        self.assertIsNone(mp.price_df)
        mp = MarketPrice(bids_tup, None)
        self.assertIsNone(mp.price_df)
        mp = MarketPrice([], offers_tup)
        self.assertIsNone(mp.price_df)
        mp = MarketPrice(bids_tup, [])
        self.assertIsNone(mp.price_df)

    def test_ensure_tuples(self):
        bids = [o(price=10, quantity=20),
                o(price=11, quantity=21)]
        offers = [o(price=5, quantity=15),
                  o(price=6, quantity=16)]

        b_tup = [(10, 20), (11, 21)]
        o_tup = [(5, 15), (6, 16)]

        # Test object
        MarketPrice(None, None)

        # Test with lists of Orders
        b_actual, o_actual = ensure_tuples(bids, offers)
        self.assertEqual(b_actual, b_tup)
        self.assertEqual(o_actual, o_tup)

        # Test with lists of tuples
        b_actual, o_actual = ensure_tuples(b_tup, o_tup)
        self.assertEqual(b_actual, b_tup)
        self.assertEqual(o_actual, o_tup)

        # Test with lists of None
        b_actual, o_actual = ensure_tuples(None, None)
        self.assertIsNone(b_actual)
        self.assertIsNone(o_actual)

    def test_get_cxb(self):
        orders = [(2, 2), (3, 4), (4, 8), (4, 16), (5, 32), (6, 64)]

        MarketPrice(None, None)

        # Regular test - Sell
        csq = get_cxq(4, orders, OrderType.OFFER)
        self.assertEqual(csq, 30)

        # Regular test - Buy
        csq = get_cxq(4, orders, OrderType.BID)
        self.assertEqual(csq, 120)

        # Test no orders
        csq = get_cxq(4, None, OrderType.OFFER)
        self.assertEqual(csq, 0)
        csq = get_cxq(4, [], OrderType.OFFER)
        self.assertEqual(csq, 0)

    def test_get_mev_more_than_one(self):
        mp = MarketPrice(None, None)

        # More than one market_price indicated
        mp.price_df = pd.DataFrame(dict(market_price=[True, False, True, False], mev=[1, 2, 4, 8]))
        self.assertRaises(ValueError, mp.get_mev)

    def test_get_mev_zero(self):
        mp = MarketPrice(None, None)

        # Zero market_price indicated
        mp.price_df = pd.DataFrame(dict(market_price=[False, False, False, False], mev=[1, 2, 4, 8]))
        self.assertRaises(ValueError, mp.get_mev)

    def test_get_mev_pass(self):
        mp = MarketPrice(None, None)

        # One market_price indicated - success
        mp.price_df = pd.DataFrame(dict(market_price=[False, True, False, False], mev=[1, 2, 4, 8]))
        mev = mp.get_mev()
        self.assertEqual(mev, 2)

    def test_only_one_cand(self):
        mp = MarketPrice(None, None)

        mp.candidate_prices = (True, False, False, False)
        self.assertTrue(mp.only_one_candidate_price())
        mp.candidate_prices = (1, 0, 0, 0)
        self.assertTrue(mp.only_one_candidate_price())

        mp.candidate_prices = (True, True, False, False)
        self.assertFalse(mp.only_one_candidate_price())
        mp.candidate_prices = (1, 1, 0, 0)
        self.assertFalse(mp.only_one_candidate_price())

        mp.candidate_prices = (False, False, False, False)
        self.assertFalse(mp.only_one_candidate_price())
        mp.candidate_prices = (0, 0, 0, 0)
        self.assertFalse(mp.only_one_candidate_price())

    def test_finalize(self):
        # Set up
        mp = MarketPrice(None, None)
        df = pd.DataFrame(dict(
            price=[1, 2, 3, 4],
            mev=[5, 6, 7, 8]
        ))
        mp.price_df = df
        mp.candidate_prices = [True, False, False, False]

        # Execute / Test
        tup = mp.finalize_and_get_result()
        self.assertEqual(tup, (1, 5))
        self.assertEqual(mp.price_df.shape, (4, 3))
        self.assertEqual(list(mp.price_df), ['price', 'mev', 'market_price'])
        self.assertEqual(list(mp.price_df.market_price), list(mp.candidate_prices))

    def test_finalize_more_than_one(self):
        # Set up
        mp = MarketPrice(None, None)
        df = pd.DataFrame(dict(
            price=[1, 2, 3, 4],
            mev=[5, 6, 7, 8]
        ))
        mp.price_df = df
        mp.candidate_prices = [True, True, False, False]

        # Execute / Test
        self.assertRaises(ValueError, mp.finalize_and_get_result)

    def test_finalize_zero(self):
        # Set up
        mp = MarketPrice(None, None)
        df = pd.DataFrame(dict(
            price=[1, 2, 3, 4],
            mev=[5, 6, 7, 8]
        ))
        mp.price_df = df
        mp.candidate_prices = [False, False, False, False]

        # Execute / Test
        self.assertRaises(ValueError, mp.finalize_and_get_result)

    def test_apply_max_vol(self):
        b_vol = [(1, 1), (2, 2)]
        o_vol = [(1, 1), (2, 2)]

        mp = MarketPrice(b_vol, o_vol)
        mp.apply_max_volume_princ()

        df = mp.price_df

        self.assertEqual(mp.final_principle, Principle.VOLUME)
        self.assertEqual(list(df), ['price', 'volume', 'cbq', 'csq', 'mev', 'max_volume_cand'])
        self.assertEqual(df.shape, (2, 6))
        self.assertEqual(list(df.cbq), [3, 2])
        self.assertEqual(list(df.csq), [1, 3])
        self.assertEqual(list(df.mev), [1, 2])
        self.assertEqual(list(df.max_volume_cand), [False, True])
        self.assertEqual(list(mp.candidate_prices), [False, True])

    def test_apply_max_vol_multiple(self):
        b_resid = [(4, 2), (6, 1)]
        o_resid = [(4, 1), (6, 1)]

        mp = MarketPrice(b_resid, o_resid)
        mp.apply_max_volume_princ()

        df = mp.price_df

        self.assertEqual(mp.final_principle, Principle.VOLUME)
        self.assertEqual(list(df), ['price', 'volume', 'cbq', 'csq', 'mev', 'max_volume_cand'])
        self.assertEqual(df.shape, (2, 6))
        self.assertEqual(list(df.cbq), [3, 1])
        self.assertEqual(list(df.csq), [1, 2])
        self.assertEqual(list(df.mev), [1, 1])
        self.assertEqual(list(df.max_volume_cand), [True, True])
        self.assertEqual(list(mp.candidate_prices), [True, True])

    def test_apply_min_resid_one(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11, 12, 13),
            cbq=(100, 99, 98, 97),
            csq=(1, 2, 3, 4)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [True, True, True, True]

        # Execute
        mp.apply_least_residual_princ()
        df = mp.price_df

        # / Assert
        self.assertEqual(mp.final_principle, Principle.RESIDUAL)
        self.assertEqual(list(df), ['price', 'cbq', 'csq', 'residual', 'min_res_cand'])
        self.assertEqual(df.shape, (4, 5))
        self.assertEqual(list(df.residual), [99, 97, 95, 93])
        self.assertEqual(list(df.min_res_cand), [False, False, False, True])
        self.assertEqual(list(df.min_res_cand), list(mp.candidate_prices))

    def test_apply_min_resid_two(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11, 12, 13),
            cbq=(10, 99, 10, 97),
            csq=(10, 2, 10, 4)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [True, True, True, True]

        # Execute
        mp.apply_least_residual_princ()
        df = mp.price_df

        # / Assert
        self.assertEqual(mp.final_principle, Principle.RESIDUAL)
        self.assertEqual(list(df), ['price', 'cbq', 'csq', 'residual', 'min_res_cand'])
        self.assertEqual(df.shape, (4, 5))
        self.assertEqual(list(df.residual), [0, 97, 0, 93])
        self.assertEqual(list(df.min_res_cand), [True, False, True, False])
        self.assertEqual(list(df.min_res_cand), list(mp.candidate_prices))

    def test_apply_min_resid_non_full_cand(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11, 12, 13),
            cbq=(10, 100, 10, 100),
            csq=(10, 2, 10, 1)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [False, True, False, True]

        # Execute
        mp.apply_least_residual_princ()
        df = mp.price_df

        # / Assert
        self.assertEqual(mp.final_principle, Principle.RESIDUAL)
        self.assertEqual(list(df), ['price', 'cbq', 'csq', 'residual', 'min_res_cand'])
        self.assertEqual(df.shape, (4, 5))
        res_act = list(df.residual)
        self.assertTrue(np.isnan(res_act[0]))
        self.assertEqual(res_act[1], 98)
        self.assertTrue(np.isnan(res_act[2]))
        self.assertEqual(res_act[3], 99)
        self.assertEqual(list(df.min_res_cand), [False, True, False, False])
        self.assertEqual(list(df.min_res_cand), list(mp.candidate_prices))

    def test_apply_pressure_buy(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11),
            cbq=(16, 17),
            csq=(16, 16)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [True, True]

        mp.apply_market_pressure_princ()
        df = mp.price_df
        self.assertEqual(mp.final_principle, Principle.PRESSURE)
        self.assertEqual(list(df), ['price', 'cbq', 'csq', 'buy_pressure', 'pressure_cand'])
        self.assertEqual(df.shape, (2, 5))
        self.assertEqual(list(df.buy_pressure), [1, 1])
        self.assertEqual(list(df.pressure_cand), [False, True])
        self.assertEqual(list(df.pressure_cand), list(mp.candidate_prices))

    def test_apply_pressure_sell(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11),
            cbq=(14, 15),
            csq=(16, 16)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [True, True]

        mp.apply_market_pressure_princ()
        df = mp.price_df
        self.assertEqual(mp.final_principle, Principle.PRESSURE)
        self.assertEqual(list(df), ['price', 'cbq', 'csq', 'buy_pressure', 'pressure_cand'])
        self.assertEqual(df.shape, (2, 5))
        self.assertEqual(list(df.buy_pressure), [0, 0])
        self.assertEqual(list(df.pressure_cand), [True, False])
        self.assertEqual(list(df.pressure_cand), list(mp.candidate_prices))

    def test_apply_pressure_both(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11, 12, 13),
            cbq=(14, 15, 16, 17),
            csq=(16, 16, 16, 16)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [True, True, True, True]

        mp.apply_market_pressure_princ()
        df = mp.price_df
        self.assertEqual(mp.final_principle, Principle.PRESSURE)
        self.assertEqual(list(df), ['price', 'cbq', 'csq', 'buy_pressure', 'pressure_cand'])
        self.assertEqual(df.shape, (4, 5))
        self.assertEqual(list(df.buy_pressure), [0, 0, 1, 1])
        self.assertEqual(list(df.pressure_cand), [True, False, False, True])
        self.assertEqual(list(df.pressure_cand), list(mp.candidate_prices))

    def test_apply_pressure_both_excluding(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11, 12, 13),
            cbq=(14, 15, 16, 17),
            csq=(16, 16, 16, 16)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [True, False, False, True]

        # Execute / Assert
        mp.apply_market_pressure_princ()
        df = mp.price_df
        self.assertEqual(mp.final_principle, Principle.PRESSURE)
        self.assertEqual(list(df), ['price', 'cbq', 'csq', 'buy_pressure', 'pressure_cand'])
        self.assertEqual(df.shape, (4, 5))
        buy_press_actual = list(df.buy_pressure)
        self.assertEqual(buy_press_actual[0], 0)
        self.assertTrue(np.isnan(buy_press_actual[1]))
        self.assertTrue(np.isnan(buy_press_actual[2]))
        self.assertEqual(buy_press_actual[3], 1)
        self.assertEqual(list(df.pressure_cand), [True, False, False, True])
        self.assertEqual(list(df.pressure_cand), list(mp.candidate_prices))

    def test_apply_ref_price(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11, 12, 13)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [True, True, True, True]

        # Execute / Assert
        mp.apply_reference_price_princ()
        df = mp.price_df

        self.assertEqual(mp.final_principle, Principle.REFERENCE)
        self.assertEqual(list(df), ['price', 'reference_cand'])
        self.assertEqual(df.shape, (4, 2))
        self.assertEqual(list(df.reference_cand), [False, False, False, True])
        self.assertEqual(list(df.reference_cand), list(mp.candidate_prices))

    def test_apply_ref_price_exclude(self):
        # set up
        mp = MarketPrice(None, None)
        price_df = pd.DataFrame(dict(
            price=(10, 11, 12, 13)
        ))
        mp.price_df = price_df
        mp.candidate_prices = [False, True, True, False]

        # Execute / Assert
        mp.apply_reference_price_princ()
        df = mp.price_df

        self.assertEqual(mp.final_principle, Principle.REFERENCE)
        self.assertEqual(list(df), ['price', 'reference_cand'])
        self.assertEqual(df.shape, (4, 2))
        self.assertEqual(list(df.reference_cand), [False, False, True, False])
        self.assertEqual(list(df.reference_cand), list(mp.candidate_prices))

    def test_market_price_volume(self):
        # Set up
        b_vol = [(1, 1), (2, 2)]
        o_vol = [(1, 1), (2, 2)]
        mp = MarketPrice(b_vol, o_vol)

        # Execute
        price, volume = mp.get_market_price(last_price=-1)  # last price is not needed here

        # Assert
        self.assertEqual(price, 2)
        self.assertEqual(volume, 2)
        self.assertEqual(mp.final_principle, Principle.VOLUME)

    def test_market_price_resid(self):
        # Set up
        b_resid = [(4, 2), (6, 1)]
        o_resid = [(4, 1), (6, 1)]
        mp = MarketPrice(b_resid, o_resid)

        # Execute
        price, volume = mp.get_market_price(last_price=-1)  # last price is not needed here

        # Assert
        self.assertEqual(price, 6)
        self.assertEqual(volume, 1)
        self.assertEqual(mp.final_principle, Principle.RESIDUAL)

    def test_market_price_pressure(self):
        # Set up
        b_press = [(55, 4)]
        o_press = [(50, 10)]
        mp = MarketPrice(b_press, o_press)

        # Execute
        price, volume = mp.get_market_price(last_price=-1)  # last price is not needed here

        # Assert
        self.assertEqual(price, 50)
        self.assertEqual(volume, 4)
        self.assertEqual(mp.final_principle, Principle.PRESSURE)

    def test_market_price_ref(self):
        # Set up
        b_ref = [(5, 10), (6, 10)]
        o_ref = [(5, 10), (6, 10)]
        mp = MarketPrice(b_ref, o_ref)

        # Execute
        price, volume = mp.get_market_price(last_price=-1)  # last price is not needed here

        # Assert
        self.assertEqual(price, 6)
        self.assertEqual(volume, 10)
        self.assertEqual(mp.final_principle, Principle.REFERENCE)

    def test_market_price_no_trade(self):
        # Set up
        b_no_trade = [(1, 1)]
        o_no_trade = [(10, 1)]
        mp = MarketPrice(b_no_trade, o_no_trade)

        # Execute
        price, volume = mp.get_market_price(last_price=-1)  # last price is not needed here

        # Assert
        self.assertEqual(price, -1)
        self.assertEqual(volume, 0)
        self.assertEqual(mp.final_principle, Principle.REFERENCE)

    # noinspection DuplicatedCode
    def test_get_market_price_no_orders(self):
        bids = [o(price=10, quantity=20),
                o(price=11, quantity=21)]
        offers = [o(price=5, quantity=15),
                  o(price=6, quantity=16)]

        # Offers None
        mp = MarketPrice(bids, None)
        p, v = mp.get_market_price(last_price=1)
        self.assertEqual(p, 1)
        self.assertEqual(v, 0)
        self.assertEqual(mp.final_principle, Principle.NO_ORDERS)
        self.assertIsNone(mp.price_df)
        self.assertTrue(mp.has_bids)
        self.assertFalse(mp.has_offers)

        # Offers Empty
        mp = MarketPrice(bids, [])
        p, v = mp.get_market_price(last_price=1)
        self.assertEqual(p, 1)
        self.assertEqual(v, 0)
        self.assertEqual(mp.final_principle, Principle.NO_ORDERS)
        self.assertIsNone(mp.price_df)
        self.assertTrue(mp.has_bids)
        self.assertFalse(mp.has_offers)

        # Bids None
        mp = MarketPrice(None, offers)
        p, v = mp.get_market_price(last_price=1)
        self.assertEqual(p, 1)
        self.assertEqual(v, 0)
        self.assertEqual(mp.final_principle, Principle.NO_ORDERS)
        self.assertIsNone(mp.price_df)
        self.assertFalse(mp.has_bids)
        self.assertTrue(mp.has_offers)

        # Bids Empty
        mp = MarketPrice([], offers)
        p, v = mp.get_market_price(last_price=1)
        self.assertEqual(p, 1)
        self.assertEqual(v, 0)
        self.assertEqual(mp.final_principle, Principle.NO_ORDERS)
        self.assertIsNone(mp.price_df)
        self.assertFalse(mp.has_bids)
        self.assertTrue(mp.has_offers)

        # Both None
        mp = MarketPrice(None, None)
        p, v = mp.get_market_price(last_price=1)
        self.assertEqual(p, 1)
        self.assertEqual(v, 0)
        self.assertEqual(mp.final_principle, Principle.NO_ORDERS)
        self.assertIsNone(mp.price_df)
        self.assertFalse(mp.has_bids)
        self.assertFalse(mp.has_offers)

        # Both Empty
        mp = MarketPrice([], [])
        p, v = mp.get_market_price(last_price=1)
        self.assertEqual(p, 1)
        self.assertEqual(v, 0)
        self.assertEqual(mp.final_principle, Principle.NO_ORDERS)
        self.assertIsNone(mp.price_df)
        self.assertFalse(mp.has_bids)
        self.assertFalse(mp.has_offers)
