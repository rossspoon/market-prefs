# import os
# print(os.curdir)
# os.chdir("../../")

import unittest
from unittest.mock import MagicMock

from otree.models import Session

import rounds
from rounds import get_debt_message, Subsession
from rounds import get_short_message
from rounds import Constants
from rounds.test.test_market_iteration import basic_player
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


if __name__ == '__main__':
    unittest.main()
