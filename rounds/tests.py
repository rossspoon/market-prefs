from otree.api import Submission, expect
from otree.bots import Bot
from .models import Group
import random
import time

from rounds import Constants,PracticeStartPage,PracticeEndPage,Fixate,MarketGridChoice,ForecastPage,RoundResultsPage,RiskPage1,RiskPage2,RiskPage3,RiskPage4,FinalResultsPage

BUY_RANGE = (-5, 5)
SELL_RANGE = 5

class PlayerBot(Bot):
    def __init__(self, **kwargs):
        self.f0s = [14.00] * (Constants.num_rounds + 1)
        super().__init__(**kwargs)



    def play_round(self):
        
        if self.round_number == 1:
            yield Submission(PracticeStartPage, check_html=False)
            
        if self.round_number == Constants.num_practice + 1:
            yield Submission(PracticeEndPage, check_html=False)
            
        
            
        yield Submission(Fixate, check_html=False)
        yield Submission(MarketGridChoice, check_html=False)
        yield Submission(Fixate, check_html=False)
        
        #Generate forcast amount
        price = self.group.get_last_period_price()
        f0 = int(max(0, random.randint(-6, 6) + price))
        f1 = int(max(0, random.randint(-6, 6) + price))
        f2 = int(max(0, random.randint(-6, 6) + price))
        f3 = int(max(0, random.randint(-6, 6) + price))
        yield Submission(ForecastPage, dict(f0=f0, f1=f1, f2=f2, f3=f3), check_html=False)
        yield Submission(Fixate, check_html=False)
        yield Submission(RoundResultsPage, check_html=False)
        yield Submission(Fixate, check_html=False)
        yield Submission(RiskPage1, dict(risk=random.randint(0,1)), check_html=False)
        yield Submission(RiskPage2, dict(risk=random.randint(0,1)), check_html=False)
        yield Submission(RiskPage3, dict(risk=random.randint(0,1)), check_html=False)
        yield Submission(RiskPage4, dict(risk=random.randint(0,1)), check_html=False)
        
        # if self.round_number == Constants.num_rounds:
        #     yield Submission(FinalResultsPage, check_html=False)


def call_live_method(method, **kwargs):

    page_class = kwargs.get('page_class')
    if not (page_class is MarketGridChoice):
        return
    print(page_class)

    
    group: Group = kwargs.get('group')
    mp = group.get_last_period_price()

    for player in group.get_players():
        buy_price = mp + random.randint(BUY_RANGE[0], BUY_RANGE[1])
        sell_price = buy_price + random.randint(1, SELL_RANGE)
        
        place_order(method, player.id_in_group, 'BUY', buy_price, 1)
        place_order(method, player.id_in_group, 'SELL', sell_price, 1)
        


def place_order(method, id_, type_, price, quant, valid=True, code_expect=None):
    _price = str(price)
    _quant = str(quant)
    _type = str(type_)

    req = {'func': 'submit-order', 'data': {'type': _type, 'price': _price, 'quantity': _quant}}
    res = method(id_, req)
    data = res.get(id_)

    return res

