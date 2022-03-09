import unittest
from unittest.mock import MagicMock, patch, call, PropertyMock

from otree.models import Session

from rounds import OrderType, Group, Player
from rounds.call_market_price import MarketPrice, OrderFill
from rounds.data_structs import DataForOrder, DataForPlayer
from rounds.market_iteration import MarketIteration
from rounds.market_iteration import get_orders_by_player, concat_or_null, ensure_order_data
from test_call_market import get_order
from test_call_market import basic_group

BID = OrderType.BID.value
OFFER = OrderType.OFFER.value


def basic_player(pid=None, id_in_group=None, shares=0):
    player = MagicMock(spec=Player)
    player.shares = shares
    if pid:
        player.id = pid
    if id_in_group:
        player.id_in_group = id_in_group
    return player


def basic_iteration(offers=None, bids=None, group=None, dividend=100, players=None, last_price=1375):
    if not group:
        group = basic_group()
        group.get_last_period_price = MagicMock(return_value=last_price)
    if players:
        group.get_players = MagicMock(return_value=players)
    return MarketIteration(bids, offers, group, dividend)


p1 = basic_player(pid=1234, id_in_group=1)
p2 = basic_player(pid=6789, id_in_group=2)
all_players = [p1, p2]

b_10_05 = get_order(player=p1, order_type=BID, price=10, quantity=5)
b_10_06 = get_order(player=p2, order_type=BID, price=10, quantity=6)
b_11_05 = get_order(order_type=BID, price=11, quantity=5)
b_11_06 = get_order(order_type=BID, price=11, quantity=6)

o_05_05 = get_order(player=p1, order_type=OFFER, price=5, quantity=5)
o_05_06 = get_order(order_type=OFFER, price=5, quantity=6)
o_06_05 = get_order(order_type=OFFER, price=6, quantity=5)
o_06_07 = get_order(order_type=OFFER, price=6, quantity=7)

buy_in_p1 = get_order(player=p1, order_type=BID, price=8, quantity=1)
sell_off_p1 = get_order(player=p1, order_type=OFFER, price=8, quantity=1)

all_bids = [b_10_05, b_10_06, b_11_05, b_11_06]
all_offers = [o_05_05, o_05_06, o_06_05, o_06_07]

sess_config = dict(interest_rate=.1,
                   margin_ratio=.2,
                   margin_premium=.3,
                   margin_target_ratio=.4)


def get_group(players, market_price=98):
    group = Group()
    group.get_players = MagicMock(return_value=players)
    group.get_last_period_price = MagicMock(return_value=market_price)
    group.session = Session()
    group.session.config = sess_config
    return group


class TestMarketIteration(unittest.TestCase):

    def test_init(self):
        # Execute
        group = get_group(all_players, market_price=-99)
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
        group = get_group(all_players, market_price=-99)

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
        p1_b_10_05 = get_order(player=p1, order_type=BID, price=10, quantity=5)
        p2_b_10_06 = get_order(player=p2, order_type=BID, price=10, quantity=6)
        p1_b_11_05 = get_order(player=p1, order_type=BID, price=11, quantity=5)
        p2_b_11_06 = get_order(player=p2, order_type=BID, price=11, quantity=6)

        p2_o_05_05 = get_order(player=p2, order_type=OFFER, price=5, quantity=5)
        p1_o_05_06 = get_order(player=p1, order_type=OFFER, price=5, quantity=6)
        p2_o_06_05 = get_order(player=p2, order_type=OFFER, price=6, quantity=5)
        p1_o_06_07 = get_order(player=p1, order_type=OFFER, price=6, quantity=7)

        orders = [p1_b_10_05, p2_b_10_06, p1_b_11_05, p2_b_11_06, p2_o_05_05, p1_o_05_06, p2_o_06_05,
                  p1_o_06_07]

        # Execute
        d = get_orders_by_player(orders)

        # Assert
        self.assertEqual(set(d.keys()), {p1, p2})
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
        with patch.object(MarketPrice, '__init__', return_value=None):
            with patch.object(MarketPrice, 'get_market_price', return_value=(5, 6)):
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
        with patch.object(MarketPrice, '__init__', return_value=None):
            with patch.object(MarketPrice, 'get_market_price', return_value=(5, 6)):
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
        with patch.object(OrderFill, '__init__', return_value=None):
            with patch.object(OrderFill, 'fill_orders', return_value=([], [])):
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
        with patch.object(OrderFill, '__init__', return_value=None):
            with patch.object(OrderFill, 'fill_orders', return_value=([], [])):
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
        group = get_group([])

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
        group = get_group([])

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

    def test_run_iteration_cancel(self):
        # Set up
        p3 = basic_player()  # These are control characters nothing should happen to their orders
        p4 = basic_player()

        # Orders - A buy and sell for each player
        os1 = get_order(player=p1, quantity=5, order_type=OrderType.OFFER.value)
        ob1 = get_order(player=p1, quantity=5, order_type=OrderType.BID.value)
        os2 = get_order(player=p2, quantity=5, order_type=OrderType.OFFER.value)
        ob2 = get_order(player=p2, quantity=5, order_type=OrderType.BID.value)
        os3 = get_order(player=p3, quantity=5, order_type=OrderType.OFFER.value)
        ob3 = get_order(player=p3, quantity=5, order_type=OrderType.BID.value)
        os4 = get_order(player=p4, quantity=5, order_type=OrderType.OFFER.value)
        ob4 = get_order(player=p4, quantity=5, order_type=OrderType.BID.value)

        _buy_in_p1 = get_order(player=p1, order_type=BID, price=8, quantity=1)
        _sell_off_p2 = get_order(player=p2, order_type=OFFER, price=8, quantity=1)

        buy_in_data = DataForOrder(_buy_in_p1)
        sell_off_data = DataForPlayer(_sell_off_p2)

        group = get_group(players=[p1, p2, p3, p4])
        mi = MarketIteration([ob1, ob2, ob3, ob4], [os1, os2, os3, os4], group, 4,
                             buy_ins=[_buy_in_p1], sell_offs=[_sell_off_p2])
        mi.get_market_price = MagicMock(return_value=(200, 100))
        mi.fill_orders = MagicMock(return_value=([], []))
        mi.compute_player_position = MagicMock(return_value=(None, None))

        # Execute
        buy_ins, sell_offs = mi.run_iteration()

        # Assert
        self.assertEqual(buy_ins, [])
        self.assertEqual(sell_offs, [])
        mi.get_market_price.assert_called_once()
        mi.fill_orders.assert_called_with(200)
        self.assertEqual(mi.compute_player_position.call_count, 4)

        # Check the orders
        for o in mi.get_all_orders():
            o.update_order()
        # Player 1
        self.assertEqual(os1.quantity, 0)
        self.assertEqual(os1.original_quantity, 5)
        self.assertEqual(ob1.quantity, 5)
        self.assertIsNone(ob1.original_quantity)
        # Player 2
        self.assertEqual(os2.quantity, 5)
        self.assertIsNone(os2.original_quantity)
        self.assertEqual(ob2.quantity, 0)
        self.assertEqual(ob2.original_quantity, 5)
        # Player 3
        self.assertEqual(os3.quantity, 5)
        self.assertIsNone(os3.original_quantity)
        self.assertEqual(ob3.quantity, 5)
        self.assertIsNone(ob3.original_quantity)
        # Player 4
        self.assertEqual(os4.quantity, 5)
        self.assertIsNone(os4.original_quantity)
        self.assertEqual(ob4.quantity, 5)
        self.assertIsNone(ob4.original_quantity)

    def test_run_iteration_over_short(self):
        # Set up
        _p1 = basic_player(shares=0)
        _p2 = basic_player(shares=0)

        os11 = get_order(player=p1, quantity=5, price=10, order_type=OrderType.OFFER.value)
        os12 = get_order(player=p1, quantity=5, price=9, order_type=OrderType.OFFER.value)

        group = get_group(players=[p1])
        group.get_short_limit = MagicMock(return_value=1)
        mi = MarketIteration(None, [os11, os12], group, 4)
        mi.get_market_price = MagicMock(return_value=(200, 100))
        mi.fill_orders = MagicMock(return_value=([], []))
        mi.compute_player_position = MagicMock(return_value=(None, None))

        # Execute
        _, _ = mi.run_iteration()

        # Assert
        for o in mi.get_all_orders():
            o.update_order()
        self.assertEqual(os11.quantity, 0)
        self.assertEqual(os11.original_quantity, 5)
        self.assertEqual(os12.quantity, 1)
        self.assertEqual(os12.original_quantity, 5)

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

    def test_supply_for_player(self):
        # Set-up
        player1 = basic_player(shares=0)
        player2 = basic_player(shares=2)

        o1 = get_order(player=player1, quantity=1, order_type=OFFER)
        o21 = get_order(player=player2, quantity=2, order_type=OFFER)
        o22 = get_order(player=player2, quantity=1, order_type=OFFER)
        o23 = get_order(player=player2, quantity=4, order_type=BID)

        itr = basic_iteration(offers=[o1, o21, o22], bids=[o23], players=[player1, player2])

        # Test
        s1 = itr.get_supply_for_player(player1)
        s2 = itr.get_supply_for_player(player2)

        # Assert
        self.assertEqual(s1, 1)
        self.assertEqual(s2, 3)

    def test_get_orders_for_players_single(self):
        player1 = basic_player(shares=0)
        player2 = basic_player(shares=2)
        player3 = basic_player(shares=2)

        o1 = get_order(player=player1, quantity=1, order_type=OFFER)
        o21 = get_order(player=player2, quantity=2, order_type=OFFER)
        o22 = get_order(player=player2, quantity=1, order_type=OFFER)
        o23 = get_order(player=player2, quantity=4, order_type=BID)
        o3 = get_order(player=player3, quantity=4, order_type=OFFER)

        itr = basic_iteration(offers=[o1, o21, o22, o3], bids=[o23], players=[player1, player2, player3])

        # Test
        o_for_p1 = itr.get_orders_for_players(player1)
        o_for_p2 = itr.get_orders_for_players(player2)
        b_for_p2 = itr.get_orders_for_players(player2, order_type=OrderType.BID)
        o_for_p1p2 = itr.get_orders_for_players([player1, player2])

        # Assert
        self.assertEqual(o_for_p1, ensure_order_data([o1]))
        self.assertEqual(o_for_p2, ensure_order_data([o21, o22]))
        self.assertEqual(b_for_p2, ensure_order_data([o23]))
        self.assertEqual(o_for_p1p2, ensure_order_data([o1, o21, o22]))

    def test_get_shorting_players(self):
        # Set-up
        player1 = basic_player(shares=10)  # not selling
        player2 = basic_player(shares=10)  # selling all shares, not shorting
        player3 = basic_player(shares=10)  # Shorting
        player4 = basic_player(shares=-10)  # already short, and selling
        player5 = basic_player(shares=-10)  # already short, but not selling

        o2 = get_order(player=player2, quantity=10, order_type=OFFER)
        o3 = get_order(player=player3, quantity=11, order_type=OFFER)
        o4 = get_order(player=player4, quantity=1, order_type=OFFER)

        itr = basic_iteration(offers=[o2, o3, o4], players=[p1, p2])
        itr.group.get_players = MagicMock(return_value=[player1, player2, player3, player4, player5])

        # Test
        shorting = itr.get_shorting_players()

        # Assert
        self.assertEqual(set(shorting), {player3, player4})

    def test_screen_orders_for_over_shorting_no_limit(self):
        # Set-up
        itr = basic_iteration(players=[p1, p2])
        itr.group.get_short_limit = MagicMock(return_value=Group.NO_SHORT_LIMIT)
        itr.get_shorting_players = MagicMock()

        # Test
        itr.screen_orders_for_over_shorting()

        # Assert
        self.assertEqual(itr.get_shorting_players.call_count, 0)

    def tests_screen_orders_for_over_shorting_at_limit(self):
        # Set-up
        player1 = basic_player(shares=0)
        player2 = basic_player(shares=0)

        o1 = get_order(player=player1, quantity=2, order_type=OFFER)
        o2 = get_order(player=player2, quantity=2, order_type=OFFER)

        p = PropertyMock()
        type(o1).original_quantity = p
        type(o2).original_quantity = p

        itr = basic_iteration(offers=[o1, o2], players=[player1, player2])
        itr.group.get_short_limit = MagicMock(return_value=4)

        # Test
        itr.screen_orders_for_over_shorting()

        # Assert
        o1.original_quantity.assert_not_called()
        o2.original_quantity.assert_not_called()

    def tests_screen_orders_for_over_shorting_cancel_partial(self):
        # Set-up
        player1 = basic_player(shares=0)
        player2 = basic_player(shares=0)

        o1 = get_order(player=player1, quantity=2, price=5, order_type=OFFER, original_quantity=None)
        o2 = get_order(player=player2, quantity=2, price=4, order_type=OFFER, original_quantity=None)

        itr = basic_iteration(offers=[o1, o2], players=[player1, player2])
        itr.group.get_short_limit = MagicMock(return_value=3)

        # Test
        itr.screen_orders_for_over_shorting()
        for o in itr.offers:
            o.update_order()

        # Assert
        self.assertEqual(o1.original_quantity, 2)
        self.assertEqual(o1.quantity, 1)
        self.assertIsNone(o2.original_quantity)
        self.assertEqual(o2.quantity, 2)

    def tests_screen_orders_for_over_shorting_cancel_full(self):
        # Set-up
        player1 = basic_player(shares=0)
        player2 = basic_player(shares=0)

        o1 = get_order(player=player1, quantity=3, price=5, order_type=OFFER, original_quantity=None)
        o2 = get_order(player=player2, quantity=3, price=4, order_type=OFFER, original_quantity=None)

        itr = basic_iteration(offers=[o1, o2], players=[player1, player2])
        itr.group.get_short_limit = MagicMock(return_value=1)

        # Test
        itr.screen_orders_for_over_shorting()
        for o in itr.offers:
            o.update_order()

        # Assert
        self.assertEqual(o1.original_quantity, 3)
        self.assertEqual(o1.quantity, 0)
        self.assertEqual(o2.original_quantity, 3)
        self.assertEqual(o2.quantity, 1)

    def tests_screen_orders_for_over_shorting_overage_just_zeroed(self):
        # Set-up
        player1 = basic_player(shares=0)
        player2 = basic_player(shares=0)

        o1 = get_order(player=player1, quantity=2, price=5, order_type=OFFER, original_quantity=None)
        o2 = get_order(player=player2, quantity=2, price=4, order_type=OFFER, original_quantity=None)

        itr = basic_iteration(offers=[o1, o2], players=[player1, player2])
        itr.group.get_short_limit = MagicMock(return_value=0)

        # Test
        itr.screen_orders_for_over_shorting()
        for o in itr.offers:
            o.update_order()

        # Assert
        self.assertEqual(o1.original_quantity, 2)
        self.assertEqual(o1.quantity, 0)
        self.assertEqual(o2.original_quantity, 2)
        self.assertEqual(o2.quantity, 0)
