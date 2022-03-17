# import os
# print(os.curdir)
# os.chdir("../../")

import unittest
from collections import defaultdict
from unittest.mock import MagicMock, patch, call

from otree.models import Session

import rounds
from rounds import get_debt_message, Subsession, OrderType, OrderErrorCode, Order
from rounds import get_short_message
from rounds import Constants
from rounds.test.test_call_market import get_order
from rounds.test.test_market_iteration import basic_player, get_group
import common.SessionConfigFunctions as scf

M_RAT = .6
T_RAT = .7


class TestInitFunctions(unittest.TestCase):
    def test_debt_msg_no_worries(self):
        cls, msg = get_debt_message(M_RAT, T_RAT, .701, 0, 1)
        self.assertEqual(cls, '')

        cls, msg = get_debt_message(M_RAT, T_RAT, .78, 0, 1)
        self.assertEqual(cls, '')

    def test_debt_msg_no_warning(self):
        cls, msg = get_debt_message(M_RAT, T_RAT, .7, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_debt_message(M_RAT, T_RAT, .699, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_debt_message(M_RAT, T_RAT, .601, 0, 1)
        self.assertEqual(cls, 'alert-warning')

    def test_debt_msg_no_error_last_round_delay(self):
        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 1, Constants.num_rounds)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

    def test_debt_msg_error(self):
        # Last round tests - Need to see a message if there is no delay
        num_rounds = Constants.num_rounds

        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        cls, msg = get_debt_message(M_RAT, T_RAT, .1, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, no delay
        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 0, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, delay
        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 1, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, f"next period \\(Period {num_rounds}\\)")

        # Not last round, long delay - should never happen, but test it for coverage
        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 2, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, "a future period")

    def test_short_msg_no_worries(self):
        cls, msg = get_short_message(M_RAT, T_RAT, .701, 0, 1)
        self.assertEqual(cls, '')

        cls, msg = get_short_message(M_RAT, T_RAT, .78, 0, 1)
        self.assertEqual(cls, '')

    def test_short_msg_no_warning(self):
        cls, msg = get_short_message(M_RAT, T_RAT, .7, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_short_message(M_RAT, T_RAT, .699, 0, 1)
        self.assertEqual(cls, 'alert-warning')

        cls, msg = get_short_message(M_RAT, T_RAT, .601, 0, 1)
        self.assertEqual(cls, 'alert-warning')

    def test_short_msg_no_error_last_round_delay(self):
        cls, msg = get_short_message(M_RAT, T_RAT, .6, 1, Constants.num_rounds)
        self.assertIsNone(cls)
        self.assertIsNone(msg)

    def test_short_msg_error(self):
        # Last round tests - Need to see a message if there is no delay
        num_rounds = Constants.num_rounds

        cls, msg = get_short_message(M_RAT, T_RAT, .6, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        cls, msg = get_short_message(M_RAT, T_RAT, .1, 0, num_rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, no delay
        cls, msg = get_short_message(M_RAT, T_RAT, .6, 0, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, delay
        cls, msg = get_short_message(M_RAT, T_RAT, .6, 1, num_rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, f"next period \\(Period {num_rounds}\\)")

        # Not last round, long delay - should never happen, but test it for coverage
        cls, msg = get_short_message(M_RAT, T_RAT, .6, 2, num_rounds - 1)
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
    def test_is_order_valid_form_not_valid(self, _):
        error_code = rounds.is_order_valid({}, {})

        # Assert
        self.assertEqual(error_code, 999)

    @patch('rounds.is_order_form_valid', return_value=(0, None, -1, -2))
    def test_is_order_valid_neg_price_and_quant(self, _):
        error_code = rounds.is_order_valid({}, {})

        expected_error_code = OrderErrorCode.PRICE_NEGATIVE.value + \
                              OrderErrorCode.QUANT_NEGATIVE.value

        # Assert
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, None, -1, 2))
    def test_is_order_valid_neg_price(self, _):
        error_code = rounds.is_order_valid({}, {})

        expected_error_code = OrderErrorCode.PRICE_NEGATIVE.value

        # Assert
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, None, 1, -2))
    def test_is_order_valid_neg_quant(self, _):
        error_code = rounds.is_order_valid({}, {})

        expected_error_code = OrderErrorCode.QUANT_NEGATIVE.value

        # Assert
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.BID, 4000, 2))
    def test_is_order_valid_buy_price_above_sell(self, _):
        # Set-up
        player = basic_player(id_in_group=-99)
        order = get_order(player=player, order_type=1, price=4000)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.OFFER] = [order]

        # Test
        error_code = rounds.is_order_valid({}, orders_by_price)

        # Assert
        expected_error_code = OrderErrorCode.BID_GREATER_THAN_ASK.value
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.OFFER, 4000, 2))
    def test_is_order_valid_sell_price_below_buy(self, _):
        # Set-up
        player = basic_player(id_in_group=-99)
        order = get_order(player=player, order_type=-1, price=4000)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.BID] = [order]

        # Test
        error_code = rounds.is_order_valid({}, orders_by_price)

        # Assert
        expected_error_code = OrderErrorCode.ASK_LESS_THAN_BID.value
        self.assertEqual(error_code, expected_error_code)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.OFFER, 4000, 2))
    def test_is_order_valid_sell(self, _):
        # Set-up
        player = basic_player(id_in_group=-99)
        sell = get_order(player=player, order_type=1, price=4001)
        buy = get_order(player=player, order_type=-1, price=3999)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.OFFER] = [sell]
        orders_by_price[OrderType.BID] = [buy]

        # Test
        error_code = rounds.is_order_valid({}, orders_by_price)

        # Assert
        self.assertEqual(error_code, 0)

    @patch('rounds.is_order_form_valid', return_value=(0, OrderType.BID, 4000, 2))
    def test_is_order_valid_buy(self, _):
        # Set-up
        player = basic_player(id_in_group=-99)
        sell = get_order(player=player, order_type=1, price=4001)
        buy = get_order(player=player, order_type=-1, price=3999)
        orders_by_price = defaultdict(list)
        orders_by_price[OrderType.OFFER] = [sell]
        orders_by_price[OrderType.BID] = [buy]

        # Test
        error_code = rounds.is_order_valid({}, orders_by_price)

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
        d = rounds.get_orders_for_player_live([sell, buy])

        # Assert

        self.assertEqual(d['func'], 'order_list')
        self.assertEqual(len(d['orders']), 2)
        sell.to_dict.assert_called_once()
        buy.to_dict.assert_called_once()

    @patch.object(Order, 'create')
    @patch.object(Order, 'filter')
    def test_create_order_from_live_submit(self, filter_mock, create_mock):
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
        filter_mock.assert_called_with(player=player)

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

    def test_get_warnings_no_order(self):
        # Set-up
        player = basic_player(shares=4, cash=5000)
        buy1 = get_order(order_type=-1, quantity=1, price=1001)
        buy2 = get_order(order_type=-1, quantity=2, price=2000)
        sell_1 = get_order(order_type=1, quantity=3)
        obt = {OrderType.OFFER: [sell_1], OrderType.BID: [buy1, buy2]}

        # Test
        warnings = rounds.get_order_warnings(player, 'no_order', 0, 2, obt)

        # Assert
        self.assertEqual(len(warnings), 1)
        self.assertRegex(warnings[0], r'BUY.*CASH')


if __name__ == '__main__':
    unittest.main()
