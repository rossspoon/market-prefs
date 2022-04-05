import sys
import unittest

from otree.bots.bot import ExpectError

from rounds import *

BUY = -1
SELL = 1
RUN_UNITS = True


def run_unit_tests():
    if not RUN_UNITS:
        return

    suite = unittest.defaultTestLoader.discover('rounds/test')
    print("\n===========================\nRUNNING UNIT TESTS")
    ttr = unittest.TextTestRunner(stream=sys.stdout)
    ttr.run(suite)
    database.db.rollback()
    print("\n FINISHED UNIT TESTS\n===========================\n\n")


def test_get_orders_for_player(method, id_, expected_num):
    res = method(id_, {'func': 'get_orders_for_player'})

    ret_dict = res.get(id_)
    expect(ret_dict.get('func'), 'order_list')
    orders = ret_dict.get('orders')
    expect(len(orders), expected_num)
    return orders


def test_delete_order(method, player_id, oid):
    method(player_id, {'func': 'delete_order', 'oid': oid})


def run_order_placement_coverage_tests(method):
    # First test errors codes for rejecting order problems
    # test order deletion
    # generate some sell orders for player 1 and delete them.
    test_place_order(method, 2, '1', '12', '6')
    test_place_order(method, 2, '1', '12.50', '6')

    orders = test_get_orders_for_player(method, 2, 2)
    # we'll delete the sell orders for this player
    for o in orders:
        if o.get('type') == 1:
            test_delete_order(method, 2, o.get('oid'))
    test_get_orders_for_player(method, 2, 0)

    # expecting rejected orders
    test_place_order(method, 2, '2', '50', '10', valid=False, code_expect=OrderErrorCode.BAD_TYPE)
    # test_place_order(method, 2, '1', 'a', '10', valid=False, code_expect=OrderErrorCode.PRICE_NOT_NUM)
    test_place_order(method, 2, '1', '-1', '10', valid=False, code_expect=OrderErrorCode.PRICE_NEGATIVE)
    test_place_order(method, 2, '1', '50', 'a', valid=False, code_expect=OrderErrorCode.QUANT_NOT_NUM)
    test_place_order(method, 2, '1', '50', '-1', valid=False, code_expect=OrderErrorCode.QUANT_NEGATIVE)


#############################################################################################################
class Actor:
    def __init__(self, name: str):
        self.player = None
        self.rounds = {}
        self.name = name

    def round(self, round_number):
        actor_round = ActorRound(round_number)
        self.rounds[round_number] = actor_round
        return actor_round

    def for_round(self, round_number):
        return self.rounds.get(round_number)


class ActorRound:
    def __init__(self, round_number):
        self.round_number = round_number
        self.orders = []
        self.cash = None
        self.shares = None
        self.expected_values = {}
        self.expected_orders = []
        self.order_count = -1  # Setting to zero signals to expect exactly zero orders.

    # Configure Interface
    def set(self, cash, shares):
        self.cash = cash
        self.shares = shares
        return self

    def buy(self, shares, at=None):
        self._store_order(BUY, shares, at)
        return self

    def sell(self, shares, at=None):
        self._store_order(SELL, shares, at)
        return self

    def expect(self, **kwargs):
        self.expected_values.update(kwargs)
        return self

    def expect_num_orders(self, count):
        self.order_count = count
        return self

    def expect_order(self,
                     price=None,
                     quant=None,
                     quant_orig=None,
                     quant_final=None,
                     otype=None,
                     is_auto=False):
        # Try to parse order information
        if not (price and quant and otype):
            print("Incomplete Order specification:  Skipping")
            return self

        self.expected_orders.append(dict(price=price, quant=quant, otype=otype, is_auto=is_auto,
                                         quant_orig=quant_orig, quant_final=quant_final))
        self.order_count = 1 if self.order_count < 1 else self.order_count + 1
        return self

    # Bot Interface
    def do_set(self):
        return self.cash is not None and self.shares is not None

    def expects_any(self):
        return len(self.expected_values.keys()) > 0

    def expects(self, key):
        return key in self.expected_values

    def expects_orders(self):
        return len(self.expected_orders) > 0

    # Helpers
    def _store_order(self, otype, shares, price):
        self.orders.append(dict(otype=otype, shares=shares, price=price))


class MarketTests:
    def __init__(self):
        self.rounds = {}  # round number to MarketRound
        self.part_id_to_actor_name = {}  # participant id to actor name
        self.name_to_player = {}
        self.actor_names = set()  # set of actor names

    # Bot Interface
    def attach_actors(self, players):
        for name, player in zip(self.actor_names, players):
            part_id = player.participant.code
            self.part_id_to_actor_name[part_id] = name
            self.name_to_player[name] = player

    def get_actor_name(self, player):
        part_id = player.participant.code
        name = self.part_id_to_actor_name.get(part_id)

        return name

    def for_round(self, round_number):
        """
        Gets the set of actor-actions for the given round number
        @param round_number: The round number
        @return: MarketRound The market round for the given round number
        """
        return self.rounds.get(round_number)

    def for_player_and_round(self, player, round_number):
        """
        Get the player actions for the given player in the given round
        @param round_number: the given round number
        @param player: the given player
        @return: ActorRound for the player in this round
        """
        mr: MarketRound = self.for_round(round_number)
        if not mr:
            return None

        name = self.get_actor_name(player)
        return mr.actions_for_actor(name)

    def get_num_defined_rounds(self):
        return len(self.rounds.keys())

    # Config Interface
    def round(self, round_number):
        market_round = MarketRound(self, round_number)
        self.rounds[round_number] = market_round
        return market_round

    def next_round(self):
        round_num = self.get_num_defined_rounds() + 1
        return self.round(round_num)


class MarketRound:
    def __init__(self, tests: MarketTests, round_number):
        self.tests = tests
        self.round_number = round_number
        self.player_actions = {}  # ActionRounds  - The player actions for a particular round
        self.expected_values = {}
        self.set_values = {}
        self.is_not_set = True

    # Configuration Interface
    def set(self, **kwargs):
        self.set_values.update(kwargs)
        return self

    def expect(self, **kwargs):
        self.expected_values.update(kwargs)
        return self

    def actor(self, name: str, setup):
        """
        Registers a new Actor in the test.
        @param name: The Actor's name for ID purposes
        @param setup: Callable statement to register ActorRound Actions
        @return: This MarketRound object
        """
        ar = ActorRound(self.round_number)
        # tell the MarketTest object about this
        self.tests.actor_names.add(name)
        self.player_actions[name] = ar
        setup(ar)
        return self

    def finish(self):
        return self.tests

    # Bot Interface
    def actions_for_actor(self, name):
        return self.player_actions.get(name)

    def expects_any(self):
        return len(self.expected_values.keys()) > 0

    def expects(self, key):
        return key in self.expected_values


#############################################################################################################
class ScriptedBot(Bot):
    first_time = True
    number_of_bots_in_round = defaultdict(int)
    errors_by_round = defaultdict(list)

    def play_round(self):
        # The first time we get here, we need to assign players to all the actor objects
        if self.first_time:
            ScriptedBot.first_time = False
            market.attach_actors(self.group.get_players())
            run_unit_tests()

        round_number = self.round_number
        # exit if we are past the defined rounds
        if round_number > market.get_num_defined_rounds() + 1:
            return

        # Set group-level items
        market_round_this_round: MarketRound = market.for_round(round_number)
        if market_round_this_round and market_round_this_round.is_not_set:
            market_round_this_round.is_not_set = False
            d = market_round_this_round.set_values
            self.group_level_sets(self.group, d)

        ScriptedBot.number_of_bots_in_round[round_number] += 1
        number_of_bots = len(self.group.get_players())
        num_bots_already_in_round = ScriptedBot.number_of_bots_in_round[round_number]
        last_bot_in_round = number_of_bots == num_bots_already_in_round

        player = self.player
        actor_name = market.get_actor_name(player)
        this_round: ActorRound = market.for_player_and_round(player, round_number)
        last_round: ActorRound = market.for_player_and_round(player, round_number - 1)

        # last round tests are usually to test market results
        if last_round:
            print(f"Player Tests: {actor_name}")
            self.last_round_tests(last_round)

        # market level tests
        # and present all test errors for that round
        last_round_market: MarketRound = market.for_round(round_number - 1)
        if last_round_market and last_bot_in_round:
            print(f"Market-level Tests")
            self.last_round_market_tests(last_round_market)
            self.show_errors()

        # display the round number after finishing off the last round
        if last_bot_in_round:
            print(f"===========\n\tROUND {round_number}")

        # Set up Player for round
        if this_round and this_round.do_set():
            player.cash = this_round.cash
            player.shares = this_round.shares
            player.periods_until_auto_buy = -99
            player.periods_until_auto_sell = -99

        yield Submission(Market, dict(), timeout_happened=True, check_html=False)
        yield Submission(ForecastPage, dict(f0=0))
        yield RoundResultsPage
        if this_round:
            self.after_market_page_tests(actor_name, this_round)

    def last_round_tests(self, actions):
        player = self.player
        last_player = player.in_round_or_null(actions.round_number)

        # Player Tests
        if actions.expects_any():
            for var in vars(player):
                self.test_object_attribute(player, actions, var)

        # Order Tests
        # This is a last-round test, so we need the last-round player
        if not last_player:
            return

        actor_name = market.get_actor_name(last_player)
        orders = Order.filter(player=last_player)
        if actions.order_count >= 0:
            print(f"Round {actions.round_number}: Testing expected number of orders")
            try:
                expect(len(orders), actions.order_count)
            except ExpectError as err:
                error = f"Round {self.round_number - 1}: Actor {actor_name}: Testing Order Count: {err}"
                ScriptedBot.errors_by_round[actions.round_number].append(error)

        # Compare actual orders with expected orders
        if actions.expects_orders():
            order_keys = set(self.order_key_order(o) for o in orders)
            added_order_keys = False
            for exp_key in [self.order_key_expects(o) for o in actions.expected_orders]:
                if not order_keys.__contains__(exp_key):
                    if not added_order_keys:
                        order_key_msg = f"Round {actions.round_number}: Actor {actor_name}:" \
                                        f" Found Orders Keys:{order_keys}"
                        ScriptedBot.errors_by_round[actions.round_number].append(order_key_msg)

                    error = f"Round {actions.round_number}: Actor {actor_name}: Did not find order {exp_key}"
                    ScriptedBot.errors_by_round[actions.round_number].append(error)

    @staticmethod
    def group_level_sets(group, d):
        stock_float = d.get('float')
        if stock_float:
            group.float = stock_float

    @staticmethod
    def order_key_order(o):
        q_orig_str = "None" if o.original_quantity is None else f"{o.original_quantity}"
        q_final_str = ""
        if o.quantity_final:
            q_final_str = f":::q_final:{o.quantity_final}"
        return f"p:{o.price:.2f}:::q:{o.quantity}:::t:{o.order_type}:::a:{o.is_buy_in}" \
               f":::q_orig:{q_orig_str}{q_final_str}"

    @staticmethod
    def order_key_expects(o):
        q_orig_str = "None" if o['quant_orig'] is None else f"{o['quant_orig']}"
        q_final_str = ""
        if o.get('quant_final'):
            q_final_str = f":::q_final:{o.get('quant_final')}"
        return f"p:{o['price']:.2f}:::q:{o['quant']}:::t:{o['otype']}:::a:{o['is_auto']}" \
               f":::q_orig:{q_orig_str}{q_final_str}"

    def after_market_page_tests(self, actor, actions):
        pass

    def init_tests(self):
        pass

    def last_round_market_tests(self, last_round_market: MarketRound):
        if not last_round_market.expects_any():
            return

        if self.round_number > 1:
            group = self.group.in_round(self.round_number - 1)
            for var in vars(group):
                self.test_object_attribute(group, last_round_market, var)

    @staticmethod
    def test_object_attribute(obj, actions, attr):
        if not actions.expects(attr):
            return

        print(f"in round {actions.round_number}: testing: ", attr)
        actual = obj.field_maybe_none(attr)
        expected = actions.expected_values.get(attr)

        # Collect error for this attribute and save it on the object
        error = None
        try:
            expect(actual, expected)
        except ExpectError as err:
            if type(obj) is Group:
                error = f"In round {actions.round_number}: Testing {attr}: {err}"
            if type(obj) is Player:
                actor_name = market.get_actor_name(obj)
                error = f"Round {actions.round_number}: Actor {actor_name}: Testing {attr}: {err}"

        # Save away the error
        if error:
            ScriptedBot.errors_by_round[actions.round_number].append(error)

    def show_errors(self):
        errors = ScriptedBot.errors_by_round[self.round_number - 1]
        if errors:
            msg = "\n".join(errors)
            raise ExpectError(msg)


# LIVE METHOD TESTS
def test_place_order(method, id_, type_, price, quant, valid=True, code_expect=None):
    _price = str(price)
    _quant = str(quant)
    _type = str(type_)
    res = method(id_, {'func': 'submit-order', 'data': {'type': _type, 'price': _price, 'quantity': _quant}})
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


def call_live_method(method, **kwargs):
    if kwargs.get('page_class') != Market:
        return
    round_number = kwargs.get('round_number')
    group: Group = kwargs.get('group')

    if round_number > market.get_num_defined_rounds():
        return

    # Run coverage tests in the first round
    if round_number == 1:
        run_order_placement_coverage_tests(method)

    for player in group.get_players():
        ar: ActorRound = market.for_player_and_round(player, round_number)
        for o in ar.orders:
            test_place_order(method, player.id_in_group, o['otype'], o['price'], o['shares'])


#############################################################################################################
market = MarketTests()

# TEST CASE: Test buy-in
market.round(1) \
    .expect(price=5.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(10.00, 5)
           .buy(1, at=5.00)
           .expect(cash=5.00, shares=6, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.set(10.00, 5)
           .sell(1, at=5.00)
           .expect(cash=15.00, shares=4, periods_until_auto_buy=-99)
           .expect_order(price=5.00, quant=1, quant_final=1, otype=SELL, quant_orig=None)) \
    .actor("Treated", lambda ar: ar.set(15.00, -2)
           .expect(cash=15.00, shares=-2, periods_until_auto_buy=0)
           .expect_num_orders(0))
market.round(2) \
    .expect(price=5.00, volume=0) \
    .actor("Buyer", lambda ar: ar.expect(cash=5.00, shares=6, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.expect(cash=15.00, shares=4, periods_until_auto_buy=-99,
                                          interest_earned=None, dividend_earned=None)) \
    .actor("Treated", lambda ar: ar.expect(cash=15.00, shares=-2, periods_until_auto_buy=0)
           .expect_order(price=5.50, quant=1, quant_final=0, otype=BUY, is_auto=True).expect_num_orders(1))
market.round(3) \
    .expect(price=5.50, volume=1) \
    .actor("Buyer", lambda ar: ar.expect(cash=5.00, shares=6, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.sell(1, at=5.00)
           .expect(cash=20.50, shares=3, periods_until_auto_buy=-99)) \
    .actor("Treated", lambda ar: ar.expect(cash=9.50, shares=-1, periods_until_auto_buy=-99)
           .expect_order(price=5.50, quant=1, quant_final=1, otype=BUY, is_auto=True).expect_num_orders(1))

# TEST CASE:  Test Sell-off
market.round(4) \
    .expect(price=5.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(20.00, 5)
           .buy(1, at=5.00)
           .expect(cash=15.00, shares=6, periods_until_auto_sell=-99)) \
    .actor("Seller", lambda ar: ar.set(10.00, 5)
           .sell(1, at=5.00)
           .expect(cash=15.00, shares=4, periods_until_auto_sell=-99)) \
    .actor("Treated", lambda ar: ar.set(-10.00, 3)
           .expect(cash=-10.00, shares=3, periods_until_auto_sell=0, periods_until_auto_buy=-99)
           .expect_num_orders(0))
market.round(5) \
    .expect(price=5.00, volume=0) \
    .actor("Buyer", lambda ar: ar.expect(cash=15.00, shares=6, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.expect(cash=15.00, shares=4, periods_until_auto_buy=-99)) \
    .actor("Treated", lambda ar: ar.expect(cash=-10.00, shares=3, periods_until_auto_sell=0)
           .expect_order(price=4.50, quant=3, quant_final=0, otype=SELL, is_auto=True).expect_num_orders(1))
market.round(6) \
    .expect(price=4.50, volume=3) \
    .actor("Buyer", lambda ar: ar.buy(4, at=4.50)
           .expect(cash=1.50, shares=9, periods_until_auto_sell=-99)) \
    .actor("Seller", lambda ar: ar.expect(cash=15.00, shares=4, periods_until_auto_sell=-99)) \
    .actor("Treated", lambda ar: ar.expect(cash=3.50, shares=0, periods_until_auto_sell=-99)
           .expect_order(price=4.50, quant=3, quant_final=3, otype=SELL, is_auto=True).expect_num_orders(1)) \

market.round(7)\
    .set(float=2) \
    .expect(price=5.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(20.00, 2)
           .buy(1, at=5.00)
           .expect(cash=15.00, shares=3)) \
    .actor("Seller", lambda ar: ar.set(10.00, 0)
           .sell(1, at=5.00)
           .expect(cash=15.00, shares=-1)
           .expect_order(price=5.00, quant=1, otype=SELL, quant_orig=None, quant_final=1)) \
    .actor("Treated", lambda ar: ar.set(0, 0)) \

market.round(8) \
    .expect(price=5.00, volume=1) \
    .actor("Buyer", lambda ar: ar.buy(2, at=5.00)
           .expect(cash=10.00, shares=4)) \
    .actor("Seller", lambda ar: ar.sell(2, at=5.00)
           .expect(cash=20.00, shares=-2)
           .expect_order(price=5.00, quant=1, otype=SELL, quant_orig=2, quant_final=1)) \
    .actor("Treated", lambda ar: ar.set(0, 0)) \

# TEST CASE:  No volume market should not change the market price
market.round(9)\
    .set(float=6) \
    .actor("Buyer", lambda ar: ar.set(cash=137.43, shares=10)) \
    .actor("Seller", lambda ar: ar.set(cash=823.38, shares=-6)) \
    .actor("Treated", lambda ar: ar.set(cash=297.94, shares=2))

market.round(10) \
    .actor("Buyer", lambda ar: ar.set(cash=137.43, shares=10)
           .sell(4, at=40.00).sell(5, at=40.00)
           ) \
    .actor("Seller", lambda ar: ar.set(cash=823.38, shares=-6)
           .buy(6, at=20.00).sell(1, at=60.00)) \
    .actor("Treated", lambda ar: ar.set(cash=297.94, shares=2)
           .sell(2, at=60.00).buy(3, at=30.00)) \
    .expect(price=5.00, volume=0, float=6, short=6)

#  Test Case:  Buy - Generated and requires multiple iterations
#  The sell price is more that 10% over the current market price
market.round(11) \
    .expect(price=170.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(170.00, 18)
           .buy(1, at=170.00)
           .expect(cash=0, shares=19, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.set(48.00, 10)
           .sell(1, at=170.00)
           .expect(cash=218.00, shares=9, periods_until_auto_buy=-99)
           .expect_order(price=170.00, quant=1, quant_final=1, otype=SELL, quant_orig=None)) \
    .actor("Treated", lambda ar: ar.set(328.00, -2)
           .expect(cash=328.00, shares=-2, periods_until_auto_buy=0)
           .expect_num_orders(0))
market.round(12) \
    .expect(price=205.70, volume=1) \
    .actor("Buyer", lambda ar: ar.expect(cash=0, shares=19, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.sell(1, at=188.00)
           .expect(cash=423.70, shares=8)) \
    .actor("Treated", lambda ar: ar.expect(cash=122.30, shares=-1, periods_until_auto_buy=0)
           .expect_order(price=205.70, quant=3, quant_final=1, otype=BUY, is_auto=True).expect_num_orders(1))

#  Test Case:  Buy-in when the treated actor has an outstanding sell
#  The sell price is more that 10% over the current market price
#  and the treated player's sell should be canceled.
market.round(13) \
    .expect(price=170.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(170.00, 18)
           .buy(1, at=170.00)
           .expect(cash=0, shares=19, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.set(48.00, 10)
           .sell(1, at=170.00)
           .expect(cash=218.00, shares=9, periods_until_auto_buy=-99)
           .expect_order(price=170.00, quant=1, quant_final=1, otype=SELL, quant_orig=None)) \
    .actor("Treated", lambda ar: ar.set(328.00, -2)
           .expect(cash=328.00, shares=-2, periods_until_auto_buy=0)
           .expect_num_orders(0))
market.round(14) \
    .expect(price=205.70, volume=1) \
    .actor("Buyer", lambda ar: ar.expect(cash=0, shares=19, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.sell(1, at=188.00)
           .expect(cash=423.70, shares=8)) \
    .actor("Treated", lambda ar: ar.sell(1, at=5.0)
           .expect(cash=122.30, shares=-1, periods_until_auto_buy=0)
           .expect_order(price=205.70, quant=3, quant_final=1, otype=BUY, is_auto=True)
           .expect_order(price=5.0, quant=0, quant_final=0, quant_orig=1, otype=SELL, is_auto=False)
           .expect_num_orders(2))


#  Test Case:  Buy-in when the trade already happened
# The buyer and seller actors trade and the treated player has to compete
market.round(15) \
    .expect(price=170.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(170.00, 18)
           .buy(1, at=170.00)
           .expect(cash=0, shares=19, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.set(48.00, 10)
           .sell(1, at=170.00)
           .expect(cash=218.00, shares=9, periods_until_auto_buy=-99)
           .expect_order(price=170.00, quant=1, quant_final=1, otype=SELL, quant_orig=None)) \
    .actor("Treated", lambda ar: ar.set(328.00, -2)
           .expect(cash=328.00, shares=-2, periods_until_auto_buy=0)
           .expect_num_orders(0))
market.round(16) \
    .expect(price=209.00, volume=1) \
    .actor("Buyer", lambda ar: ar.buy(1, at=190.00)
           .expect(cash=0, shares=19, periods_until_auto_buy=-99)
           .expect_order(price=190.00, quant=1, quant_final=0, otype=BUY)) \
    .actor("Seller", lambda ar: ar.sell(1, at=188.00)
           .expect(cash=427.00, shares=8)) \
    .actor("Treated", lambda ar: ar.expect(cash=119.00, shares=-1, periods_until_auto_buy=0)
           .expect_order(price=209.00, quant=3, quant_final=1, otype=BUY, is_auto=True)
           .expect_num_orders(1))

#  Test Case:  Buy - Generated and requires multiple iterations
#  The buy price is less than 90% of the market price
market.round(17) \
    .expect(price=170.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(400.00, 18)
           .buy(1, at=170.00)
           .expect(cash=230.00, shares=19, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.set(48.00, 10)
           .sell(1, at=170.00)
           .expect(cash=218.00, shares=9, periods_until_auto_buy=-99)
           .expect_order(price=170.00, quant=1, quant_final=1, otype=SELL, quant_orig=None)) \
    .actor("Treated", lambda ar: ar.set(-340.00, 3)
           .expect(cash=-340.00, shares=3, periods_until_auto_sell=0, period_until_auto_buy=-99)
           .expect_num_orders(0))
market.round(18) \
    .expect(price=137.70, volume=1) \
    .actor("Buyer", lambda ar: ar.buy(1, at=152.00)
                            .expect(cash=92.30, shares=20, periods_until_auto_sell=-99)
                            .expect_order(price=152.00, quant=1, quant_final=1, otype=BUY, is_auto=False)) \
    .actor("Seller", lambda ar: ar.expect(cash=218.00, shares=9)) \
    .actor("Treated", lambda ar: ar.expect(cash=-202.30, shares=2, periods_until_auto_sell=0)
           .expect_order(price=137.70, quant=3, quant_final=1, otype=SELL, is_auto=True).expect_num_orders(1))

#  Test Case:  Buy - Generated and requires multiple iterations
#  The buy price is less than 90% of the market price
market.round(19) \
    .expect(price=170.00, volume=1) \
    .actor("Buyer", lambda ar: ar.set(400.00, 18)
           .buy(1, at=170.00)
           .expect(cash=230.00, shares=19, periods_until_auto_buy=-99)) \
    .actor("Seller", lambda ar: ar.set(48.00, 10)
           .sell(1, at=170.00)
           .expect(cash=218.00, shares=9, periods_until_auto_buy=-99)
           .expect_order(price=170.00, quant=1, quant_final=1, otype=SELL, quant_orig=None)) \
    .actor("Treated", lambda ar: ar.set(-340.00, 3)
           .expect(cash=-340.00, shares=3, periods_until_auto_sell=0, period_until_auto_buy=-99)
           .expect_num_orders(0))
market.round(20) \
    .expect(price=137.70, volume=1) \
    .actor("Buyer", lambda ar: ar.buy(1, at=152.00)
                            .expect(cash=92.30, shares=20, periods_until_auto_sell=-99)
                            .expect_order(price=152.00, quant=1, quant_final=1, otype=BUY, is_auto=False)) \
    .actor("Seller", lambda ar: ar.expect(cash=218.00, shares=9)) \
    .actor("Treated", lambda ar: ar.buy(1, at=5)
                        .expect(cash=-202.30, shares=2, periods_until_auto_sell=0)
                        .expect_order(price=137.70, quant=3, quant_final=1, otype=SELL, is_auto=True)
                        .expect_order(price=5, quant=0, quant_final=0, quant_orig=1, otype=BUY, is_auto=False)
                        .expect_num_orders(2))
