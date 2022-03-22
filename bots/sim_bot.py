import random
from abc import abstractmethod, ABCMeta

from otree.api import Submission
from otree.bots import Bot

import common.SessionConfigFunctions as scf
import rounds
from rounds import Market, RoundResultsPage, Player, Group, OrderType
from rounds.call_market_price import MarketPrice
from rounds.data_structs import DataForOrder

# Parameters for Feedback investors
BETA_LO = 0.001
BETA_HI = 0.02
DELTA_LO = 0
DELTA_HI = 2

# Parameters for Passive investors
ALPHA_LO = 0.001
ALPHA_HI = 0.02

# Parameters for Speculators
GAMMA_LO = 0.001
GAMMA_HI = .004

# Aggression is used to determine how individual players set the price.
AGG_LO = 0.0
AGG_HI = 0.15


class OrderMaker:
    FUNDAMENTAL_VALUE = -1
    PRICE_HISTORY = []

    __metaclass__ = ABCMeta
    _aggression = -1
    _player = None

    def __init__(self, player: Player):
        self._aggression = random.uniform(AGG_LO, AGG_HI)
        self._part_code = player.participant.code

    def __str__(self):
        return f"{self.kind()}:  Participant {self._part_code}"

    @abstractmethod
    def get_demand(self, expected_price):
        pass

    @abstractmethod
    def kind(self):
        pass

    def get_price(self, base_price, direction):
        return int(base_price * (1 + direction * self._aggression))


class FeedbackOrder(OrderMaker):
    def __init__(self, player: Player):
        super().__init__(player)
        self._delta = random.uniform(DELTA_LO, DELTA_HI)
        self._beta = random.uniform(BETA_LO, BETA_HI)

    def get_demand(self, expected_price):
        # Feedback players will sit out the first round
        if len(OrderMaker.PRICE_HISTORY) < 2:
            return 0

        price_change = OrderMaker.PRICE_HISTORY[-1] - OrderMaker.PRICE_HISTORY[-2]
        return round(-1 * self._delta + self._beta * price_change)

    def kind(self):
        return "FEEDBACK"


class PassiveOrder(OrderMaker):
    def __init__(self, player: Player):
        super().__init__(player)
        self._alpha = random.uniform(ALPHA_LO, ALPHA_HI)

    def get_demand(self, expected_price):
        price_diff = OrderMaker.PRICE_HISTORY[-1] - OrderMaker.FUNDAMENTAL_VALUE
        return -1 * round(self._alpha * price_diff)

    def kind(self):
        return "PASSIVE"


SPECULATING = -99


class SpeculativeOrder(OrderMaker):
    def __init__(self, player: Player):
        super().__init__(player)
        self._gamma = random.uniform(GAMMA_LO, GAMMA_HI)
        self._delta = random.uniform(DELTA_LO, DELTA_HI)

    def get_demand(self, expected_price):
        if expected_price == SPECULATING:
            return 0

        curr_price = OrderMaker.PRICE_HISTORY[-1]
        return round(self._delta + self._gamma * (expected_price - curr_price))

    def kind(self):
        return "SPECULATOR"


class SimulationBot(Bot):
    FIRST_TIME = True
    O_MAKER_BY_PARTICIPANT = {}
    ORDER_TYPE_CLASSES = [FeedbackOrder, FeedbackOrder, PassiveOrder, SpeculativeOrder, SpeculativeOrder, SpeculativeOrder]

    def init_test(self):
        OrderMaker.FUNDAMENTAL_VALUE = scf.get_fundamental_value(self.player)
        OrderMaker.PRICE_HISTORY.append(scf.get_init_price(self.player))

    def play_round(self):
        player = self.player
        round_number = player.round_number

        # Looks like execution gets here one time before calling the live methods.
        # So, we can initialize some things like fundamental value
        if SimulationBot.FIRST_TIME:
            self.init_test()
            SimulationBot.FIRST_TIME = False
        self.player.forecast_error = 0
        self.player.forecast_reward = 0

        yield Submission(Market, dict(), timeout_happened=True, check_html=False)

        if round_number == rounds.Constants.num_rounds:
            yield RoundResultsPage


def assign_types(group: Group):
    for i, player in enumerate(group.get_players()):
        idx = i % len(SimulationBot.ORDER_TYPE_CLASSES)
        SimulationBot.O_MAKER_BY_PARTICIPANT[player.participant.code] = SimulationBot.ORDER_TYPE_CLASSES[idx](player)


def call_live_method(method, **kwargs):
    round_number = kwargs.get('round_number')
    group: Group = kwargs.get('group')
    last_price = OrderMaker.PRICE_HISTORY[-1]

    print("================")
    print(f"==  ROUND: {round_number}")
    print("================")

    # Assign Types
    if round_number == 1:
        assign_types(group)

    # Update price history
    prev_group = group.in_round_or_none(round_number - 1)
    if prev_group:
        OrderMaker.PRICE_HISTORY.append(int(prev_group.price))
    print("Price History:", OrderMaker.PRICE_HISTORY)

    # Get the expected price for the speculators
    exp_bids, exp_offers = get_orders(group, OrderMaker.FUNDAMENTAL_VALUE, last_price)
    mp = MarketPrice(exp_bids, exp_offers)
    expected_price, _ = mp.get_market_price(last_price=last_price)
    print("Expected Value:", expected_price)

    # Place orders for all players
    bids, offers = get_orders(group, expected_price, last_price)
    # calling update on the data objects will create the orders
    for o in bids + offers:
        o.update_order()


def get_orders(group, expected_price, last_price):
    bids = []
    offers = []

    for p in group.get_players():
        participant = p.participant
        order_maker = SimulationBot.O_MAKER_BY_PARTICIPANT.get(participant.code)

        demand = order_maker.get_demand(expected_price)

        if demand != 0:
            o_type = OrderType.OFFER if demand < 0 else OrderType.BID

            price = order_maker.get_price(last_price, o_type.value * -1)
            d4o = DataForOrder(player=p,
                               group=group,
                               order_type=o_type.value,
                               price=price,
                               quantity=abs(demand),
                               )
            if o_type == OrderType.OFFER:
                offers.append(d4o)
            else:
                bids.append(d4o)

            print(f"{order_maker}: Demand: {demand}, Price: {price}")
    return bids, offers
