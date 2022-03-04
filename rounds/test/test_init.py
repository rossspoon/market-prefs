# import os
# print(os.curdir)
# os.chdir("../../")

import unittest
from rounds import get_debt_message
from rounds import get_short_message
from rounds import Constants

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
        rounds = Constants.num_rounds

        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 0, rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        cls, msg = get_debt_message(M_RAT, T_RAT, .1, 0, rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, no delay
        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 0, rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, delay
        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 1, rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, f"next period \\(Period {rounds}\\)")

        # Not last round, long delay - should never happen, but test it for coverage
        cls, msg = get_debt_message(M_RAT, T_RAT, .6, 2, rounds - 1)
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
        rounds = Constants.num_rounds

        cls, msg = get_short_message(M_RAT, T_RAT, .6, 0, rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        cls, msg = get_short_message(M_RAT, T_RAT, .1, 0, rounds)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, no delay
        cls, msg = get_short_message(M_RAT, T_RAT, .6, 0, rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, 'this period')

        # Not last round, delay
        cls, msg = get_short_message(M_RAT, T_RAT, .6, 1, rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, f"next period \\(Period {rounds}\\)")

        # Not last round, long delay - should never happen, but test it for coverage
        cls, msg = get_short_message(M_RAT, T_RAT, .6, 2, rounds - 1)
        self.assertEqual(cls, 'alert-danger')
        self.assertRegex(msg, "a future period")


if __name__ == '__main__':
    unittest.main()
