import sys
import unittest
from threading import Lock

from . import *

P_TYPE_TREATMENT = 0
P_TYPE_BUYER = 1
P_TYPE_SELLER = 2


class PlayerBot(Bot):
    p_type = -1

    def __init__(self,
                 case_number: int,
                 app_name,
                 player_pk: int,
                 subsession_pk: int,
                 session_pk,
                 participant_code,
                 ):
        super().__init__(case_number, app_name, player_pk, subsession_pk, session_pk, participant_code)
        self.p_type = (self.player.id_in_group - 1) % 3  # 0 - treatment  :: 1 - first buyer :: 2 - first seller

    # only run the unit tests once, this lock of class-level variable control that
    lock = Lock()
    unit_tests_run = False

    def run_unit_tests(self):
        suite = unittest.defaultTestLoader.discover('rounds/test')
        print("\n===========================\nRUNNING UNIT TESTS")
        # for s in suite:
        #    for t in s:
        #        for i in t:
        #            print("TEST", i, "\n")

        ttr = unittest.TextTestRunner(stream=sys.stdout)
        ttr.run(suite)
        print("\n FINISHED UNIT TESTS\n===========================\n\n")

    def init_tests(self):
        """ Run Unit tests and first-round player tests """
        # Only run the unit tests once
        if not PlayerBot.unit_tests_run:
            self.lock.acquire()
            if not PlayerBot.unit_tests_run:
                PlayerBot.unit_tests_run = True
                self.run_unit_tests()
            self.lock.release()

        # test treatment assignments
        cash_control = self.session.config['cash_endowment_control']
        shares_control = self.session.config['shares_endowment_control']
        cash_treatment = self.session.config['cash_endowment_treatment']
        shares_treatment = self.session.config['shares_endowment_treatment']

        print("PLAYER:", self.player.id_in_group, self.p_type, self.player.cash, self.player.shares)
        if self.p_type == P_TYPE_TREATMENT:
            # Should be treatment
            expect(self.player.cash, cash_treatment)
            expect(self.player.shares, shares_treatment)

        else:
            # Should be control
            expect(self.player.cash, cash_control)
            expect(self.player.shares, shares_control)

    def before_market_page_tests(self):
        r_num = self.round_number

        # the float should never change
        expect(self.group.float, 10)

        if r_num == 1:
            expect(self.group.short, 10)
        elif r_num == 2:
            expect(self.group.short, 10)
        elif r_num == 3:
            expect(self.group.short, 10)
        elif r_num == 4:
            expect(self.group.short, 6)
        elif r_num == 5:
            expect(self.group.short, 6)

        # Player-level tests
        if r_num == 2 and self.p_type == P_TYPE_BUYER:
            expect(self.player.cash, 0)
            expect(self.player.shares, 20)
            expect(self.player.margin_violation, False)

        elif r_num == 2 and self.p_type == P_TYPE_SELLER:
            expect(self.player.cash, 1000)
            expect(self.player.shares, 0)
            expect(self.player.margin_violation, False)

        elif r_num == 2 and self.p_type == P_TYPE_TREATMENT:
            expect(self.player.cash, 1000)
            expect(self.player.shares, -10)
            expect(self.player.margin_violation, True)

        elif r_num == 4 and self.p_type == P_TYPE_TREATMENT:
            expect(self.player.cash, 800)
            expect(self.player.shares, -6)
            expect(self.player.margin_violation, False)

        elif r_num == 4 and self.p_type == P_TYPE_BUYER:
            expect(self.player.cash, 200)
            expect(self.player.shares, 16)
            expect(self.player.margin_violation, False)

    def after_market_page_tests(self):
        r_num = self.round_number

        # In this test, all dividends are 0
        expect(self.group.dividend, 0)

        # Round 1 tests
        if r_num == 1:
            expect(self.group.price, 50)
            expect(self.group.volume, 10)

        if r_num == 2:
            expect(self.group.price, 50)
            expect(self.group.volume, 0)

        if r_num == 3:
            expect(self.group.price, 50)
            expect(self.group.volume, 4)

        # Round 2 & 3 Tests for Treatment player
        # immediately after the close of the round-2 market
        # the treatment player should have submitted an auto buy-in order
        if r_num in [2, 3] and self.p_type == P_TYPE_TREATMENT:
            orders = Order.filter(player=self.player)
            expect(len(orders), 1)
            o = orders[0]
            expect(o.order_type, -1)
            expect(o.price, 55)
            expect(o.quantity, 4)

    def play_round(self):
        pid = self.player.id_in_group
        print("\n==================\nRound Number:", self.round_number, "  Player:", pid)

        # overhead
        if self.player.round_number == 1:
            self.init_tests()

        # Market Page Tests
        self.before_market_page_tests()
        yield Market
        self.after_market_page_tests()

        yield Survey, dict(emotion=5)


# LIVE METHOD TESTS
def test_place_order(method, id_, type_, price, quant, valid=True, code_expect=0):
    res = method(id_, {'func': 'submit-order', 'data': {'type': type_, 'price': price, 'quantity': quant}})
    data = res.get(id_)

    if type(code_expect) is OrderErrorCode:
        code_expect = code_expect.value

    if valid:
        expect(data.get('func'), 'order_confirmed')
        expect(data.get('order_id'), '>', 0)
    else:
        code_actual = data.get('error_code')
        expect(data.get('func'), 'order_rejected')

        expect(code_actual, code_expect)

    return res


def test_get_orders_for_player(method, id_, expected_num):
    res = method(id_, {'func': 'get_orders_for_player'})

    ret_dict = res.get(id_)
    expect(ret_dict.get('func'), 'order_list')
    orders = ret_dict.get('orders')
    expect(len(orders), expected_num)
    return orders


def test_delete_order(method, player_id, oid):
    res = method(player_id, {'func': 'delete_order', 'oid': oid})


def round_1_live_tests(method, kwargs):
    # valid orders
    test_place_order(method, 2, '-1', '50', '10')
    test_get_orders_for_player(method, 2, 1)

    test_place_order(method, 3, '1', '50', '10')
    test_get_orders_for_player(method, 3, 1)

    # test order deletion
    # generate some sell orders for player 1 and delete them.
    test_place_order(method, 2, '1', '12', '12')
    test_place_order(method, 2, '1', '6', '6')
    orders = test_get_orders_for_player(method, 2, 3)
    # we'll delete the sell orders for this player
    for o in orders:
        if o.get('type') == 1:
            test_delete_order(method, 2, o.get('oid'))
    test_get_orders_for_player(method, 2, 1)

    # expecting rejected orders
    test_place_order(method, 2, '2', '50', '10', valid=False, code_expect=OrderErrorCode.BAD_TYPE)
    test_place_order(method, 2, '1', 'a', '10', valid=False, code_expect=OrderErrorCode.PRICE_NOT_NUM)
    test_place_order(method, 2, '1', '-1', '10', valid=False, code_expect=OrderErrorCode.PRICE_NEGATIVE)
    test_place_order(method, 2, '1', '50', 'a', valid=False, code_expect=OrderErrorCode.QUANT_NOT_NUM)
    test_place_order(method, 2, '1', '50', '-1', valid=False, code_expect=OrderErrorCode.QUANT_NEGATIVE)
    test_place_order(method, 2, '2', 'a', '-1', valid=False, code_expect=22)
    test_place_order(method, 2, '2', '-1', 'a', valid=False, code_expect=25)


def round_2_live_tests(method, kwargs):
    pass


def round_3_live_tests(method, kwargs):
    test_place_order(method, 2, '1', '50', '10')


def call_live_method(method, **kwargs):
    r_num = kwargs.get('round_number')
    if r_num == 1:
        round_1_live_tests(method, kwargs)

    elif r_num == 2:
        round_2_live_tests(method, kwargs)

    elif r_num == 3:
        round_3_live_tests(method, kwargs)


class PlayerType(Enum):
    REACTIVE = 0
    PROACTIVE = 1
