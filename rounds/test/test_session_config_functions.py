import unittest

from otree.models import Session

import common.SessionConfigFunctions as scf
from rounds import Group


class Test_Session_Config_Functions(unittest.TestCase):
    def test_get_fundamental_value_r0(self):
        # Set-up
        group = Group()
        group.session = Session()
        group.session.config = dict(div_dist='0.5 0.5',
                                    div_amount='0.40 1.00',
                                    interest_rate=0)
        # Execute
        f = scf.get_fundamental_value(group)

        # Assert
        self.assertEqual(f, 0)

    def test_get_fundamental_value(self):
        # Set-up
        group = Group()
        group.session = Session()
        group.session.config = dict(div_dist='0.5 0.5',
                                    div_amount='0.0 1.00',
                                    interest_rate=0.1)
        # Execute
        f = scf.get_fundamental_value(group)

        # Assert
        self.assertEqual(f, 5.00)

    def test_get_fundamental_value_exp_relevant(self):
        # Set-up
        group = Group()
        group.session = Session()
        group.session.config = dict(div_dist='0.5 0.5',
                                    div_amount='0.40 1.00',
                                    interest_rate=0.05)
        # Execute
        f = scf.get_fundamental_value(group)

        # Assert
        self.assertEqual(f, 14.00)
