from abc import abstractmethod, ABCMeta

from otree.bots import Bot

import rounds
from rounds import call_market_price, call_market, Market, Player, Group
import random

ALPHA_LO = 0.01
ALPHA_HI = 0.1
BETA_LO = 0.01
BETA_HI = 0.1
GAMMA_LO = 0.5
GAMMA_HI = 2
DELTA_LO = 0.01
DELTA_HI = 0.1
AGG_LO = 0.5
AGG_HI = 2.0


class SimulationBot(Bot):
    def init_test(self):
        cm = call_market.CallMarket(self.group, rounds.Constants.num_rounds)
        fv = cm.get_fundamental_value()
        OrderMaker.FUNDAMENTAL_VALUE = fv

    def play_round(self):
        round_number = self.player.round_number

        # Looks like execution gets here one time before calling the live methods.
        # So, we can initialize some things like fundamental value
        if round_number == 1:
            self.init_test()

        yield Market


class OrderMaker:
    FUNDAMENTAL_VALUE = -1
    price_history = [0]

    __metaclass__ = ABCMeta
    _aggression = -1
    _player = None

    def __init__(self, player: Player):
        self._aggression = random.uniform(AGG_LO, AGG_HI)
        self._player = player

    @abstractmethod
    def get_demand(self):
        pass

    def get_price(self):
        pass


class FeedbackOrder(OrderMaker):
    _delta = -1
    _beta = -1

    def __init__(self, player: Player):
        super.__init__(player)
        self._delta = random.uniform(DELTA_LO, DELTA_HI)
        self._beta = random.uniform(BETA_LO, BETA_HI)

    def get_demand(self):
        return 0


class PassiveOrder(OrderMaker):
    _alpha = -1

    def __init__(self, player: Player):
        super.__init__(player)
        self._alpha = random.uniform(ALPHA_LO, ALPHA_HI)

    def get_demand(self):
        return 0


class SpeculativeOrder(OrderMaker):
    _gamma = -1

    def __init__(self, player: Player):
        super.__init__(player)
        self._gamma = random.uniform(GAMMA_LO, GAMMA_HI)

    def get_demand(self):
        return 0


def call_live_method(method, **kwargs):

    #cm = call_market.CallMarket(self.group, rounds.Constants.num_rounds)
    #OrderMaker.price_history.append(fv)

    print("Simulation Test")
    print("fundamental value:", OrderMaker.FUNDAMENTAL_VALUE)
    r_num = kwargs.get('round_number')
    group = Group.objects_get(round_number=r_num)
    print(group)
