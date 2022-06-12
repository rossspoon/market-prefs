# import os
# print(os.curdir)
# os.chdir("../../")

import unittest
from collections import defaultdict
from unittest.mock import MagicMock, patch, call, ANY

from otree import database
from otree.api import cu
from otree.models import Session, Participant

import rounds
from rounds import get_debt_message, Subsession, OrderType, OrderErrorCode, Order
from rounds import get_short_message
from rounds import Constants
from rounds.test.test_call_market import get_order
from rounds.test.test_market_iteration import basic_player, get_group
import common.SessionConfigFunctions as scf

LIMIT = -600
CLOSE = -500


# noinspection DuplicatedCode
class TestInitFunctions(unittest.TestCase):
    def test_debt_msg_no_worries(self):
        cls, msg = get_debt_message(LIMIT, CLOSE, -499, 0, 1)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

        cls, msg = get_debt_message(LIMIT, CLOSE, -420, 0, 1)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

    def test_debt_msg_no_warning(self):
        cls, msg = get_debt_message(LIMIT, CLOSE, -500, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_debt_message(LIMIT, CLOSE, -501, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_debt_message(LIMIT, CLOSE, -599, 0, 1)
        self.assertEqual(cls, 'alert-warning')

    def test_debt_msg_no_error_last_round_delay(self):
        cls, msg = get_debt_message(LIMIT, CLOSE, -600, 1, Constants.num_rounds)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

    def test_debt_msg_error(self):
        # Last round tests - Need to see a message if there is no delay
        num_rounds = Constants.num_rounds

        cls, msg = get_debt_message(LIMIT, CLOSE, -600, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        cls, msg = get_debt_message(LIMIT, CLOSE, -1000, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, no delay
        cls, msg = get_debt_message(LIMIT, CLOSE, -600, 0, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, delay
        cls, msg = get_debt_message(LIMIT, CLOSE, -600, 1, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, f"next period \\(Period {num_rounds}\\)")

        # Not last round, long delay - should never happen, but test it for coverage
        cls, msg = get_debt_message(LIMIT, CLOSE, -600, 2, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, "a future period")

    def test_short_msg_no_worries(self):
        cls, msg = get_short_message(LIMIT, CLOSE, -499, 0, 1)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

        cls, msg = get_short_message(LIMIT, CLOSE, -420, 0, 1)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

    def test_short_msg_no_warning(self):
        cls, msg = get_short_message(LIMIT, CLOSE, -500, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_short_message(LIMIT, CLOSE, -501, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_short_message(LIMIT, CLOSE, -599, 0, 1)
        self.assertEqual(cls, 'alert-warning')

    def test_short_msg_no_error_last_round_delay(self):
        cls, msg = get_short_message(LIMIT, CLOSE, -600, 1, Constants.num_rounds)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

    def test_short_msg_error(self):
        # Last round tests - Need to see a message if there is no delay
        num_rounds = Constants.num_rounds

        cls, msg = get_short_message(LIMIT, CLOSE, -600, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        cls, msg = get_short_message(LIMIT, CLOSE, -1000, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, no delay
        cls, msg = get_short_message(LIMIT, CLOSE, -600, 0, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, delay
        cls, msg = get_short_message(LIMIT, CLOSE, -600, 1, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, f"next period \\(Period {num_rounds}\\)")

        # Not last round, long delay - should never happen, but test it for coverage
        cls, msg = get_short_message(LIMIT, CLOSE, -600, 2, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, "a future period")

    def test_endowments(self):
        # Set-up
        players = [basic_player(id_in_group=x) for x in range(1, 9)]
        config = {scf.SK_ENDOW_WORTH: 50000,
                  scf.SK_ENDOW_STOCK: '-10 -5 6 12',
                  scf.SK_INTEREST_RATE: 0.025,
                  scf.SK_DIV_DIST: '.5 .5',
                  scf.SK_DIV_AMOUNT: '0 100'
                  }
        session = Session()
        session.config = config
        subsession = Subsession()
        subsession.session = session
        subsession.round_number = 1
        subsession.get_players = MagicMock(return_value=players)
        group = get_group(players)
        subsession.get_groups = MagicMock(return_value=[group])

        # Test
        rounds.creating_session(subsession)
        fund_val = scf.get_fundamental_value(subsession)

        # Assert
        self.assertEqual(fund_val, 2000)
        self.assertEqual(players[0].shares, -10)
        self.assertEqual(players[4].shares, -10)
        self.assertEqual(players[1].shares, -5)
        self.assertEqual(players[5].shares, -5)
        self.assertEqual(players[2].shares, 6)
        self.assertEqual(players[6].shares, 6)
        self.assertEqual(players[3].shares, 12)
        self.assertEqual(players[7].shares, 12)

        self.assertEqual(players[0].cash, 70000)
        self.assertEqual(players[4].cash, 70000)
        self.assertEqual(players[1].cash, 60000)
        self.assertEqual(players[5].cash, 60000)
        self.assertEqual(players[2].cash, 38000)
        self.assertEqual(players[6].cash, 38000)
        self.assertEqual(players[3].cash, 26000)
        self.assertEqual(players[7].cash, 26000)

        for p in players:
            worth = p.cash + p.shares * fund_val
            self.assertEqual(worth, 50000)

    def test_is_order_form_valid(self):
        # Set-up
        data = dict(type='-1', price='3000', quantity='2')

        # Test
        code, t, p, q = rounds.is_order_form_valid(data)

        # Assert
        self.assertEqual(code, 0)
        self.assertEqual(t, OrderType.BID)
        self.assertEqual(p, 3000)
        self.assertEqual(q, 2)

    def test_is_order_form_valid_type(self):
        # Set-up
        data = dict(type='a', price='3000', quantity='2')

        # Test
        code, t, p, q = rounds.is_order_form_valid(data)

        # Assert
        self.assertEqual(code, OrderErrorCode.BAD_TYPE.value)
        self.assertIsNone(t)
        self.assertEqual(p, 3000)
        self.assertEqual(q, 2)

    def test_is_order_form_valid_price(self):
        # Set-up
        data = dict(type='1', price='', quantity='2')

        # Test
        code, t, p, q = rounds.is_order_form_valid(data)

        # Assert
        self.assertEqual(code, OrderErrorCode.PRICE_NOT_NUM.value)
        self.assertEqual(t, OrderType.OFFER)
        self.assertIsNone(p)
        self.assertEqual(q, 2)

    def test_is_order_form_valid_quant(self):
        # Set-up
        data = dict(type='-1', price='3000', quantity='')

        # Test
        code, t, p, q = rounds.is_order_form_valid(data)

        # Assert
        self.assertEqual(code, OrderErrorCode.QUANT_NOT_NUM.value)
        self.assertEqual(t, OrderType.BID)
        self.assertEqual(p, 3000)
        self.assertIsNone(q)

    def test_is_order_form_valid_all_bad(self):
        # Set-up
        data = dict(type='a', price='b', quantity='c')

        # Test
        code, t, p, q = rounds.is_order_form_valid(data)

        # Assert
        expected_code = OrderErrorCode.BAD_TYPE.value + \
                        OrderErrorCode.QUANT_NOT_NUM.value + \
                        OrderErrorCode.PRICE_NOT_NUM.value
        self.assertEqual(code, expected_code)
        self.assertIsNone(t)
        self.assertIsNone(p)
        self.assertIsNone(q)

    @patch('rounds.is_order_form_valid', return_value=(999, None, None, None))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_form_not_valid(self, _, _1):
        error_code = rounds.is_order_valid(None, {}, {})

        # Assert
        self.assertEqual(error_code, 999)

    @patch('rounds.is_order_form_valid', return_value=(0, None, -1, -2))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_neg_price_and_quant(self, _, _1):
        error_code = rounds.is_order_valid(None, {}, {})

        expected_error_code = OrderErrorCode.PRICE_NEGATIVE.value + \
                              OrderErrorCode.QUANT_NEGATIVE.value

        # Assert
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, None, -1, 2))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_neg_price(self, _, _1):
        error_code = rounds.is_order_valid(None, {}, {})

        expected_error_code = OrderErrorCode.PRICE_NEGATIVE.value

        # Assert
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, None, 1, -2))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_neg_quant(self, _, _1):
        error_code = rounds.is_order_valid(None, {}, {})

        expected_error_code = OrderErrorCode.QUANT_NEGATIVE.value

        # Assert
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.BID, 4000, 2))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_buy_price_above_sell(self, _, _1):
        # Set-up
        player = basic_player(id_in_group=-99)
        order = get_order(player=player, order_type=1, price=4000)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.OFFER] = [order]

        # Test
        error_code = rounds.is_order_valid(player, {}, orders_by_price)

        # Assert
        expected_error_code = OrderErrorCode.BID_GREATER_THAN_ASK.value
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.OFFER, 4000, 2))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_sell_price_below_buy(self, _, _1):
        # Set-up
        player = basic_player(id_in_group=-99)
        order = get_order(player=player, order_type=-1, price=4000)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.BID] = [order]

        # Test
        error_code = rounds.is_order_valid(player, {}, orders_by_price)

        # Assert
        expected_error_code = OrderErrorCode.ASK_LESS_THAN_BID.value
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.OFFER, 4000, 2))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_sell(self, _, _1):
        # Set-up
        player = basic_player(id_in_group=-99)
        sell = get_order(player=player, order_type=1, price=4001)
        buy = get_order(player=player, order_type=-1, price=3999)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.OFFER] = [sell]
        orders_by_price[OrderType.BID] = [buy]

        # Test
        error_code = rounds.is_order_valid(player, {}, orders_by_price)

        # Assert
        self.assertEqual(error_code, 0)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.BID, 4000, 2))
    @patch('rounds.is_borrowing_too_much', return_value=False)
    def test_is_order_valid_buy(self, _, _1):
        # Set-up
        player = basic_player(id_in_group=-99)
        sell = get_order(player=player, order_type=1, price=4001)
        buy = get_order(player=player, order_type=-1, price=3999)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.OFFER] = [sell]
        orders_by_price[OrderType.BID] = [buy]

        # Test
        error_code = rounds.is_order_valid(player, {}, orders_by_price)

        # Assert
        self.assertEqual(error_code, 0)

    def test_get_orders_by_type(self):
        # Set-up
        player = basic_player(id_in_group=-99)
        sell = get_order(player=player, order_type=1, price=4001)
        buy = get_order(player=player, order_type=-1, price=3999)

        # Test
        obt = rounds.get_orders_by_type([buy, sell])

        # Assert
        self.assertEqual(obt[OrderType.OFFER], [sell])
        self.assertEqual(obt[OrderType.BID], [buy])

    def test_get_orders_by_type_empty(self):
        # Test
        obt = rounds.get_orders_by_type([])

        # Assert
        self.assertEqual(obt[OrderType.OFFER], [])
        self.assertEqual(obt[OrderType.BID], [])

    def test_get_orders_live(self):
        # Set-up
        player = basic_player(pid=99, id_in_group=101)
        group = get_group([player], gid=98)
        sell = get_order(oid=33, player=player, group=group, order_type=1, price=4001, quantity=2, original_quantity=3)
        buy = get_order(oid=33, player=player, group=group, order_type=-1, price=3999, quantity=4, original_quantity=5)

        # Test
        d = rounds.get_orders_for_player_live([sell, buy], False)

        # Assert

        self.assertEqual(d['func'], 'order_list')
        self.assertEqual(len(d['orders']), 2)
        sell.to_dict.assert_called_once()
        buy.to_dict.assert_called_once()

    @patch.object(database.db, 'commit')
    @patch.object(Order, 'create')
    def test_create_order_from_live_submit(self, create_mock, commit_mock):
        # Set-up
        player = basic_player(id_in_group=55)
        group = get_group([player])
        player.group = group
        o = get_order(oid=44)
        create_mock.return_value = o

        # Test
        d = rounds.create_order_from_live_submit(player, OrderType.OFFER, 3000, 2)

        # Assert
        self.assertEqual(d['func'], 'order_confirmed')
        self.assertEqual(d['order_id'], o.id)
        commit_mock.assert_called_once()

    @patch.object(Order, 'filter')
    @patch.object(Order, 'delete')
    def test_delete_order(self, del_mock, filter_mock):
        # Set-up
        player = basic_player()
        filter_mock.return_value = []

        # Test
        rounds.delete_order(player, 55)

        # Assert
        filter_mock.assert_called_once_with(player=player, id=55)
        del_mock.assert_not_called()

    @patch.object(Order, 'filter')
    @patch.object(Order, 'delete')
    def test_delete_order(self, del_mock, filter_mock):
        # Set-up
        player = basic_player()
        filter_mock.return_value = []

        # Test
        rounds.delete_order(player, 55)

        # Assert
        filter_mock.assert_called_once_with(player=player, id=55)
        del_mock.assert_not_called()

    @patch.object(Order, 'filter')
    @patch.object(Order, 'delete')
    def test_delete_order_found(self, del_mock, filter_mock):
        # Set-up
        player = basic_player()
        filter_mock.return_value = ['o1', 'o2']

        # Test
        rounds.delete_order(player, 55)

        # Assert
        filter_mock.assert_called_once_with(player=player, id=55)
        del_mock.assert_has_calls([call('o1'), call('o2')])

    def test_get_warnings_borrow(self):
        # Set-up
        player = basic_player(shares=4, cash=5000)
        buy1 = get_order(order_type=-1, quantity=1, price=1001)
        sell_1 = get_order(order_type=1, quantity=2)
        sell_2 = get_order(order_type=1, quantity=3)
        obt = {OrderType.OFFER: [sell_1, sell_2], OrderType.BID: [buy1]}

        # Test
        warnings = rounds.get_order_warnings(player, OrderType.BID, 2000, 2, obt)

        # Assert
        self.assertEqual(len(warnings), 2)
        self.assertRegex(warnings[0], r'SELL.*STOCK')
        self.assertRegex(warnings[1], r'BUY.*CASH')

    def test_get_warnings_short(self):
        # Set-up
        player = basic_player(shares=4, cash=5000)
        buy1 = get_order(order_type=-1, quantity=1, price=1001)
        buy2 = get_order(order_type=-1, quantity=2, price=2000)
        sell_1 = get_order(order_type=1, quantity=3)
        obt = {OrderType.OFFER: [sell_1], OrderType.BID: [buy1, buy2]}

        # Test
        warnings = rounds.get_order_warnings(player, OrderType.OFFER, 0, 2, obt)

        # Assert
        self.assertEqual(len(warnings), 2)
        self.assertRegex(warnings[0], r'SELL.*STOCK')
        self.assertRegex(warnings[1], r'BUY.*CASH')

    def test_get_warnings_short_any_supply_is_warn(self):
        # Set-up
        player = basic_player(shares=-1, cash=5000)
        sell_1 = get_order(order_type=1, quantity=3)
        obt = {OrderType.OFFER: [sell_1], OrderType.BID: []}

        # Test
        warnings = rounds.get_order_warnings(player, 'no_order', 0, 0, obt)

        # Assert
        self.assertEqual(len(warnings), 1)
        self.assertRegex(warnings[0], r'SELL.*STOCK')

    def test_get_warnings_short_any_supply_is_warn_2(self):
        # Set-up
        player = basic_player(shares=-1, cash=5000)
        obt = {OrderType.OFFER: [], OrderType.BID: []}

        # Test
        warnings = rounds.get_order_warnings(player, OrderType.OFFER, 0, 1, obt)

        # Assert
        self.assertEqual(len(warnings), 1)
        self.assertRegex(warnings[0], r'SELL.*STOCK')

    def test_get_warnings_any_cost_warn(self):
        # Set-up
        player = basic_player(shares=4, cash=0)
        buy1 = get_order(order_type=-1, quantity=1, price=1001)
        obt = {OrderType.OFFER: [], OrderType.BID: [buy1]}

        # Test
        warnings = rounds.get_order_warnings(player, 'no_order', 0, 0, obt)

        # Assert
        self.assertEqual(len(warnings), 1)
        self.assertRegex(warnings[0], r'BUY.*CASH')

    def test_get_warnings_any_cost_warn_2(self):
        # Set-up
        player = basic_player(shares=4, cash=-1)
        obt = {OrderType.OFFER: [], OrderType.BID: []}

        # Test
        warnings = rounds.get_order_warnings(player, OrderType.BID, 1, 1, obt)

        # Assert
        self.assertEqual(len(warnings), 1)
        self.assertRegex(warnings[0], r'BUY.*CASH')

    def test_get_warnings_no_order(self):
        # Set-up
        player = basic_player(shares=4, cash=5000)
        buy1 = get_order(order_type=-1, quantity=1, price=1001)
        buy2 = get_order(order_type=-1, quantity=2, price=2000)
        sell_1 = get_order(order_type=1, quantity=3)
        obt = {OrderType.OFFER: [sell_1], OrderType.BID: [buy1, buy2]}

        # Test
        warnings = rounds.get_order_warnings(player, 'no_order', 0, 0, obt)

        # Assert
        self.assertEqual(len(warnings), 1)
        self.assertRegex(warnings[0], r'BUY.*CASH')

    def test_get_warnings_no_order_already_short(self):
        # Set-up
        player = basic_player(shares=-4, cash=5000)
        obt = {OrderType.OFFER: [], OrderType.BID: []}

        # Test
        warnings = rounds.get_order_warnings(player, 'no_order', 0, 0, obt)

        # Assert
        self.assertEqual(len(warnings), 0)

    def test_get_warnings_no_order_already_debt(self):
        # Set-up
        player = basic_player(shares=4, cash=-5000)
        obt = {OrderType.OFFER: [], OrderType.BID: []}

        # Test
        warnings = rounds.get_order_warnings(player, 'no_order', 0, 0, obt)

        # Assert
        self.assertEqual(len(warnings), 0)

    @patch('rounds.delete_order')
    @patch('rounds.get_orders_for_player', return_value=[])
    @patch('rounds.get_orders_by_type', return_value={})
    @patch('rounds.is_order_form_valid', side_effect=TypeError)
    @patch('rounds.is_order_valid', side_effect=TypeError)
    @patch('rounds.create_order_from_live_submit', side_effect=TypeError)
    @patch('rounds.get_orders_for_player_live', side_effect=TypeError)
    @patch('rounds.get_order_warnings', return_value=['abc', 'def'])
    def test_market_page_live_delete(self, warn_m, o4pl_m, create_m, is_v_m, is_vf_m, obt_m, o4p_m, del_m):
        # Set-up
        player = basic_player(id_in_group=66)
        data = dict(func='delete_order', oid='7')

        # Test
        d = rounds.market_page_live_method(player, data)

        # Assert
        del_m.assert_called_once_with(player, '7', o_cls=ANY)
        o4p_m.assert_called_once_with(player, o_cls=ANY)
        obt_m.assert_called_once_with([])
        is_vf_m.assert_not_called()
        is_v_m.assert_not_called()
        create_m.assert_not_called()
        o4pl_m.assert_not_called()
        warn_m.assert_called_once_with(player, 'no_order', 0, 0, {})
        self.assertEqual(d.keys(), {66})
        self.assertEqual(d[66]['warnings'], ['abc', 'def'])

    @patch('rounds.delete_order', side_effect=TypeError)
    @patch('rounds.get_orders_for_player', return_value=[])
    @patch('rounds.get_orders_by_type', return_value={})
    @patch('rounds.is_order_form_valid', return_value=(1, None, None, None))
    @patch('rounds.is_order_valid', return_value=1)
    @patch('rounds.create_order_from_live_submit', side_effect=TypeError)
    @patch('rounds.get_orders_for_player_live', side_effect=TypeError)
    @patch('rounds.get_order_warnings', return_value=['abc', 'def'])
    def test_market_page_live_submit_fail(self, warn_m, o4pl_m, create_m, is_v_m, is_vf_m, obt_m, o4p_m, del_m):
        # Set-up
        player = basic_player(id_in_group=66)
        form_data = dict(type='-1', price='3890', quantity='9')
        data = dict(func='submit-order', data=form_data)

        # Test
        d = rounds.market_page_live_method(player, data)

        # Assert
        del_m.assert_not_called()
        o4p_m.assert_called_once_with(player, o_cls=ANY)
        obt_m.assert_called_once_with([])
        is_vf_m.assert_called_once_with(form_data)
        is_v_m.assert_called_once_with(player, form_data, {})
        create_m.assert_not_called()
        o4pl_m.assert_not_called()
        warn_m.assert_called_once_with(player, 'no_order', 0, 0, {})
        self.assertEqual(d.keys(), {66})
        sub_d = d[66]
        self.assertEqual(sub_d['warnings'], ['abc', 'def'])
        self.assertEqual(sub_d['func'], 'order_rejected')
        self.assertEqual(sub_d['error_code'], 1)

    @patch('rounds.delete_order', side_effect=TypeError)
    @patch('rounds.get_orders_for_player', return_value=[])
    @patch('rounds.get_orders_by_type', return_value={})
    @patch('rounds.is_order_form_valid', return_value=(0, None, None, None))
    @patch('rounds.is_order_valid', return_value=1)
    @patch('rounds.create_order_from_live_submit', side_effect=TypeError)
    @patch('rounds.get_orders_for_player_live', side_effect=TypeError)
    @patch('rounds.get_order_warnings', return_value=['abc', 'def'])
    def test_market_page_live_submit_fail2(self, warn_m, o4pl_m, create_m, is_v_m, is_vf_m, obt_m, o4p_m, del_m):
        # Set-up
        player = basic_player(id_in_group=66)
        form_data = dict(type='-1', price='3890', quantity='9')
        data = dict(func='submit-order', data=form_data)

        # Test
        d = rounds.market_page_live_method(player, data)

        # Assert
        del_m.assert_not_called()
        o4p_m.assert_called_once_with(player, o_cls=ANY)
        obt_m.assert_called_once_with([])
        is_vf_m.assert_called_once_with(form_data)
        is_v_m.assert_called_once_with(player, form_data, {})
        create_m.assert_not_called()
        o4pl_m.assert_not_called()
        warn_m.assert_called_once_with(player, 'no_order', 0, 0, {})
        self.assertEqual(d.keys(), {66})
        sub_d = d[66]
        self.assertEqual(sub_d['warnings'], ['abc', 'def'])
        self.assertEqual(sub_d['func'], 'order_rejected')
        self.assertEqual(sub_d['error_code'], 1)

    @patch('rounds.delete_order', side_effect=TypeError)
    @patch('rounds.get_orders_for_player', return_value=[])
    @patch('rounds.get_orders_by_type', return_value={})
    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.BID, 3890, 9))
    @patch('rounds.is_order_valid', return_value=0)
    @patch('rounds.create_order_from_live_submit', return_value={'func': 'order_confirmed', 'order_id': 7})
    @patch('rounds.get_orders_for_player_live', side_effect=TypeError)
    @patch('rounds.get_order_warnings', return_value=['abc', 'def'])
    def test_market_page_live_submit_success(self, warn_m, o4pl_m, create_m, is_v_m, is_vf_m, obt_m, o4p_m, del_m):
        # Set-up
        player = basic_player(id_in_group=66)
        form_data = dict(type='-1', price='3890', quantity='9')
        data = dict(func='submit-order', data=form_data)

        # Test
        d = rounds.market_page_live_method(player, data)

        # Assert
        del_m.assert_not_called()
        o4p_m.assert_called_once_with(player, o_cls=ANY)
        obt_m.assert_called_once_with([])
        is_vf_m.assert_called_once_with(form_data)
        is_v_m.assert_called_once_with(player, form_data, {})
        create_m.assert_called_once_with(player, OrderType.BID, 3890, 9, o_cls=ANY)
        o4pl_m.assert_not_called()
        warn_m.assert_called_once_with(player, OrderType.BID, 3890, 9, {})
        self.assertEqual(d.keys(), {66})
        sub_d = d[66]
        self.assertEqual(sub_d['warnings'], ['abc', 'def'])
        self.assertEqual(sub_d['func'], 'order_confirmed')
        self.assertEqual(sub_d['order_id'], 7)

    @patch('rounds.delete_order')
    @patch('rounds.get_orders_for_player', return_value=[9, 8, 7])
    @patch('rounds.get_orders_by_type', return_value={})
    @patch('rounds.is_order_form_valid')
    @patch('rounds.is_order_valid')
    @patch('rounds.create_order_from_live_submit')
    @patch('rounds.get_orders_for_player_live', return_value={'func': 'order_list', 'orders': [1, 2, 3]})
    @patch('rounds.get_order_warnings', return_value=['abc', 'def'])
    def test_market_page_live_get_o4p(self, warn_m, o4pl_m, create_m, is_v_m, is_vf_m, obt_m, o4p_m, del_m):
        # Set-up
        player = basic_player(id_in_group=66)
        form_data = dict(type='-1', price='3890', quantity='9')
        data = dict(func='get_orders_for_player', data=form_data)

        # Test
        d = rounds.market_page_live_method(player, data)

        # Assert
        del_m.assert_not_called()
        o4p_m.assert_called_once_with(player, o_cls=ANY)
        obt_m.assert_called_once_with([9, 8, 7])
        is_vf_m.assert_not_called()
        is_v_m.assert_not_called()
        create_m.assert_not_called()
        o4pl_m.assert_called_once_with([9, 8, 7], False)
        warn_m.assert_called_once_with(player, 'no_order', 0, 0, {})
        self.assertEqual(d.keys(), {66})
        sub_d = d[66]
        self.assertEqual(sub_d['warnings'], ['abc', 'def'])
        self.assertEqual(sub_d['func'], 'order_list')
        self.assertEqual(sub_d['orders'], [1, 2, 3])

    # noinspection PyArgumentList
    def test_FinalResultsPage_vars(self):
        # Set-up
        p = basic_player(shares=3, cash=1.5)
        p.participant = MagicMock()
        p.participant.payoff = cu(1000)
        p.participant.vars = {'MARKET_PAYMENT': cu(4.56), 'FORECAST_PAYMENT': cu(7.89)}
        p.participant.payoff_plus_participation_fee = MagicMock(return_value=25.55)
        session = Session()
        config = {'real_world_currency_per_point': 0.02, 'participation_fee': 5.55}
        session.config = config
        p.session = session
        p.participant.session = session
        page = rounds.FinalResultsPage({'type': 'http'}, 'rec', 'send')

        # Test
        d = page.vars_for_template(p)

        # Assert
        self.assertEqual({'forecast_bonus': cu(0.16), 'market_bonus': cu(0.09), 'total_pay': 25.55, 'is_online': False}, d)


if __name__ == '__main__':
    unittest.main()
