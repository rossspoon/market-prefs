import unittest
from unittest.mock import MagicMock, patch, call

from otree.models import Session

from rounds import Order, Player, OrderType, Group
from rounds.call_market_price import MarketPrice, OrderFill
from rounds.data_structs import DataForOrder, DataForPlayer
from rounds.market_iteration import MarketIteration
from rounds.market_iteration import get_orders_by_player, concat_or_null, ensure_order_data

BID = OrderType.BID.value
OFFER = OrderType.OFFER.value

p1 = Player(id=1234, id_in_group=1)
p2 = Player(id=6789, id_in_group=2)
all_players = [p1, p2]

b_10_05 = Order(player=p1, order_type=BID, price=10, quantity=5)
b_10_06 = Order(player=p2, order_type=BID, price=10, quantity=6)
b_11_05 = Order(order_type=BID, price=11, quantity=5)
b_11_06 = Order(order_type=BID, price=11, quantity=6)

o_05_05 = Order(player=p1, order_type=OFFER, price=5, quantity=5)
o_05_06 = Order(order_type=OFFER, price=5, quantity=6)
o_06_05 = Order(order_type=OFFER, price=6, quantity=5)
o_06_07 = Order(order_type=OFFER, price=6, quantity=7)

buy_in_p1 = Order(player=p1, order_type=BID, price=8, quantity=1)
sell_off_p1 = Order(player=p1, order_type=OFFER, price=8, quantity=1)

all_bids = [b_10_05, b_10_06, b_11_05, b_11_06]
all_offers = [o_05_05, o_05_06, o_06_05, o_06_07]

sess_config = dict(interest_rate=.1,
                   margin_ratio=.2,
                   margin_premium=.3,
                   margin_target_ratio=.4)


def get_group(players=[], market_price=98):
    group = Group()
    group.get_players = MagicMock(return_value=players)
    group.get_last_period_price = MagicMock(return_value=market_price)
    group.session = Session()
    group.session.config = sess_config
    return group


class TestMarketIteration(unittest.TestCase):

    def test_init(self):
        # Execute
        group = get_group(players=all_players, market_price=-99)
        mi = MarketIteration(all_bids, all_offers, group, 4)

        # Assert
        self.assertEqual(len(mi.bids), 4)
        self.assertEqual(len(mi.offers), 4)
        for i in range(4):
            b = all_bids[i]
            bd = mi.bids[i]
            self.assertIsInstance(bd, DataForOrder)
            self.assertEqual(b, bd.order)

            o = all_offers[i]
            od = mi.offers[i]
            self.assertIsInstance(od, DataForOrder)
            self.assertEqual(o, od.order)

        self.assertEqual(len(mi.players), 2)
        for i in range(2):
            p = all_players[i]
            pdat = mi.players[i]
            self.assertIsInstance(pdat, DataForPlayer)
            self.assertEqual(p, pdat.player)

        o4p = mi.orders_by_player
        self.assertEqual(len(o4p[mi.players[0].player]), 2)
        self.assertEqual(len(o4p[mi.players[1].player]), 1)

        self.assertEqual(mi.dividend, 4)
        self.assertEqual(mi.last_price, -99)
        self.assertIsNone(mi.buy_ins)
        self.assertEqual(mi.interest_rate, .1)
        self.assertEqual(mi.margin_ratio, .2)
        self.assertEqual(mi.margin_premium, .3)
        self.assertEqual(mi.margin_target_ratio, .4)

    def test_init_with_buy_in(self):
        # Set-up
        buy_ins = [buy_in_p1]
        buy_in_data = ensure_order_data(buy_ins)
        group = get_group(players=all_players, market_price=-99)

        # Execute
        mi = MarketIteration(None, None, group, 4, buy_ins=buy_ins)

        # Assert
        self.assertEqual(mi.dividend, 4)
        self.assertEqual(mi.last_price, -99)
        self.assertIsNotNone(mi.buy_ins)
        self.assertEqual(len(mi.buy_ins), 1)
        orders_for_p1 = mi.orders_by_player[p1]
        self.assertEqual(orders_for_p1, buy_in_data)
        orders_for_p2 = mi.orders_by_player[p2]
        self.assertEqual(orders_for_p2, [])
        self.assertIsInstance(mi.buy_ins[0], DataForOrder)
        self.assertEqual(mi.interest_rate, .1)
        self.assertEqual(mi.margin_ratio, .2)
        self.assertEqual(mi.margin_premium, .3)
        self.assertEqual(mi.margin_target_ratio, .4)

    def test_get_orders_by_player(self):
        # Set-up
        p1_b_10_05 = Order(player=p1, order_type=BID, price=10, quantity=5)
        p2_b_10_06 = Order(player=p2, order_type=BID, price=10, quantity=6)
        p1_b_11_05 = Order(player=p1, order_type=BID, price=11, quantity=5)
        p2_b_11_06 = Order(player=p2, order_type=BID, price=11, quantity=6)

        p2_o_05_05 = Order(player=p2, order_type=OFFER, price=5, quantity=5)
        p1_o_05_06 = Order(player=p1, order_type=OFFER, price=5, quantity=6)
        p2_o_06_05 = Order(player=p2, order_type=OFFER, price=6, quantity=5)
        p1_o_06_07 = Order(player=p1, order_type=OFFER, price=6, quantity=7)

        orders = [p1_b_10_05, p2_b_10_06, p1_b_11_05, p2_b_11_06, p2_o_05_05, p1_o_05_06, p2_o_06_05,
                  p1_o_06_07]
        self

        # Execute
        d = get_orders_by_player(orders)

        # Assert
        self.assertEqual(set(d.keys()), set([p1, p2]))
        self.assertEqual(d[p1], [p1_b_10_05, p1_b_11_05, p1_o_05_06, p1_o_06_07])
        self.assertEqual(d[p2], [p2_b_10_06, p2_b_11_06, p2_o_05_05, p2_o_06_05])

    def test_get_orders_by_player_none(self):
        d = get_orders_by_player(None)
        self.assertIsNotNone(d)
        self.assertEqual(len(d), 0)

    def test_concat_or_null(self):
        l1 = [1, 2, 3]
        l2 = [4, 5, 6]
        l3 = [7, 8, 9]

        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9], concat_or_null([l1, l2, l3]))
        self.assertEqual([1, 2, 3], concat_or_null([l1, None]))
        self.assertEqual([1, 2, 3, 7, 8, 9], concat_or_null([l1, None, l3]))
        self.assertIsNone(concat_or_null([None, None]))

    def test_get_market_price_no_buy_ins(self):
        with patch.object(MarketPrice, '__init__', return_value=None) as mock_init:
            with patch.object(MarketPrice, 'get_market_price', return_value=(5, 6)) as mock_gmp:
                # Set up
                bids_data = ensure_order_data(all_bids)
                offer_data = ensure_order_data(all_offers)
                group = get_group(players=all_players, market_price=-99)

                mi = MarketIteration(all_bids, all_offers, group, 4)

                # Execute
                price, volume = mi.get_market_price()

                # Assert
                self.assertEqual(price, 5)
                self.assertEqual(volume, 6)
                MarketPrice.__init__.assert_called_with(bids_data, offer_data)
                MarketPrice.get_market_price.assert_called_once_with(last_price=-99)

    def test_get_market_price_with_buy_ins(self):
        with patch.object(MarketPrice, '__init__', return_value=None) as mock_init:
            with patch.object(MarketPrice, 'get_market_price', return_value=(5, 6)) as mock_gmp:
                # Set up
                bids_data = ensure_order_data(all_bids + [buy_in_p1])
                offer_data = ensure_order_data(all_offers)
                group = get_group(players=all_players, market_price=-98)
                mi = MarketIteration(all_bids, all_offers, group, 4, buy_ins=[buy_in_p1])

                # Execute
                price, volume = mi.get_market_price()

                # Assert
                self.assertEqual(price, 5)
                self.assertEqual(volume, 6)
                MarketPrice.__init__.assert_called_with(bids_data, offer_data)
                MarketPrice.get_market_price.assert_called_once_with(last_price=-98)

    def test_fill_orders_no_buy_ins(self):
        with patch.object(OrderFill, '__init__', return_value=None) as mock_init:
            with patch.object(OrderFill, 'fill_orders', return_value=([], [])) as mock_gmp:
                bids_data = ensure_order_data(all_bids)
                offer_data = ensure_order_data(all_offers)
                group = get_group(players=all_players, market_price=-98)

                mi = MarketIteration(all_bids, all_offers, group, 4)

                # Execute
                mi.fill_orders(-78)

                # Assert
                OrderFill.__init__.assert_called_with(bids_data + offer_data)
                OrderFill.fill_orders.assert_called_with(-78)

    def test_fill_orders_with_buy_ins(self):
        with patch.object(OrderFill, '__init__', return_value=None) as mock_init:
            with patch.object(OrderFill, 'fill_orders', return_value=([], [])) as mock_gmp:
                bids_data = ensure_order_data(all_bids)
                offer_data = ensure_order_data(all_offers)
                buy_in_data = ensure_order_data([buy_in_p1])
                group = get_group(players=all_players, market_price=-98)

                mi = MarketIteration(all_bids, all_offers, group, 4, buy_ins=[buy_in_p1])

                # Execute
                mi.fill_orders(-78)

                # Assert
                OrderFill.__init__.assert_called_with(bids_data + offer_data + buy_in_data)
                OrderFill.fill_orders.assert_called_with(-78)

    def test_compute_player_pos_no_buy_in(self):
        # Set up
        d4p = DataForPlayer(p1)
        d4p.get_new_player_position = MagicMock()
        d4p.set_mv_short_future = MagicMock()
        d4p.set_mv_debt_future = MagicMock()
        d4p.is_buy_in_required = MagicMock(return_value=False)
        d4p.generate_buy_in_order = MagicMock(return_value=buy_in_p1)
        group = get_group()

        mi = MarketIteration(None, None, group, 4)

        # Execute
        buy_in_order, sell_off_order = mi.compute_player_position(d4p, 44)

        # Assert
        self.assertIsNone(buy_in_order)
        self.assertIsNone(sell_off_order)
        d4p.get_new_player_position.assert_called_with([], 4, .1, 44)
        d4p.set_mv_short_future.assert_called_with(.2, 44)
        d4p.is_buy_in_required.assert_called_once()
        d4p.generate_buy_in_order.assert_not_called()
        group.get_players.assert_called_once()
        group.get_last_period_price.assert_called_once()
        self.assertEqual(mi.last_price, 98)

    def test_compute_player_pos_with_buy_in(self):
        # Set up
        d4p = DataForPlayer(p1)
        d4p.get_new_player_position = MagicMock()
        d4p.set_mv_short_future = MagicMock()
        d4p.set_mv_debt_future = MagicMock()
        d4p.is_buy_in_required = MagicMock(return_value=True)
        d4p.generate_buy_in_order = MagicMock(return_value=buy_in_p1)
        group = get_group()

        mi = MarketIteration(None, None, group, 4)

        # Execute
        buy_order, sell_order = mi.compute_player_position(d4p, 44)

        # Assert
        self.assertEqual(buy_order, buy_in_p1)
        self.assertIsNone(sell_order)
        d4p.get_new_player_position.assert_called_with([], 4, .1, 44)
        d4p.set_mv_short_future.assert_called_with(.2, 44)
        d4p.is_buy_in_required.assert_called_once()
        d4p.generate_buy_in_order.assert_called_with(44)
        group.get_players.assert_called_once()
        group.get_last_period_price.assert_called_once()
        self.assertEqual(mi.last_price, 98)

    def test_run_iteration(self):
        # Set up
        buy_in_data = DataForOrder(buy_in_p1)
        group = get_group(players=[p1, p2])
        mi = MarketIteration(None, None, group, 4)
        mi.get_market_price = MagicMock(return_value=(200, 100))
        mi.fill_orders = MagicMock(return_value=([], []))
        mi.compute_player_position = MagicMock(return_value=(buy_in_data, None))
        mi.compute_player_position.side_effect = [(buy_in_data, None), (None, None)]

        # Execute
        buy_ins, sell_offs = mi.run_iteration()

        # Assert
        self.assertEqual(buy_ins, ensure_order_data([buy_in_p1]))
        self.assertEqual(sell_offs, [])
        mi.get_market_price.assert_called_once()
        mi.fill_orders.assert_called_with(200)
        self.assertEqual(mi.compute_player_position.call_count, 2)
        calls = [call(DataForPlayer(p1), 200),
                 call(DataForPlayer(p2), 200)]
        mi.compute_player_position.assert_has_calls(calls, any_order=True)

    def test_get_all_orders_with_buy_in(self):
        group = get_group(players=[p1, p2], market_price=-98)

        mi = MarketIteration(all_bids, all_offers, group, 4, buy_ins=[buy_in_p1])

        # Execute
        o = mi.get_all_orders()

        # Assert
        o_data = ensure_order_data(all_bids + all_offers + [buy_in_p1])
        self.assertEqual(o, o_data)

    def test_get_all_orders_no_buy_in(self):
        group = get_group(players=[p1, p2], market_price=-98)

        mi = MarketIteration(all_bids, all_offers, group, 4)

        # Execute
        o = mi.get_all_orders()

        # Assert
        o_data = ensure_order_data(all_bids + all_offers)
        self.assertEqual(o, o_data)
