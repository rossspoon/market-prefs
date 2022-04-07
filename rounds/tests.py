from otree.api import Submission, expect
from otree.bots import Bot
from otree.models import Session

from bots.scripted_bot import ScriptedBot, test_place_order
from bots.sim_bot import SimulationBot
from rounds import Constants, ForecastPage, RoundResultsPage, Market, FinalResultsPage, Group


class PlayerBot(Bot):
    def __init__(self, **kwargs):
        self.f0s = [14.00] * (Constants.num_rounds + 1)
        super().__init__(**kwargs)

    def __new__(cls, *args, **kwargs):
        session = Session.objects_get(id=kwargs.get('session_pk'))
        s_name = session.config.get('name')
        if s_name == 'rounds_test':
            return ScriptedBot(**kwargs)

        elif s_name == 'sim_1':
            return SimulationBot(**kwargs)

        return super().__new__(cls)

    def play_round(self):
        yield Submission(Market, check_html=False)

        round_number = self.round_number

        # Check the float
        if self.round_number == 1:
            stock_float = sum(p.shares for p in self.group.get_players())
            expect(self.group.float, stock_float)

        # Forcast Page
        f0 = self.f0s[round_number]
        form_data = {'f0': f0}
        yield Submission(ForecastPage, form_data)

        player = self.player
        expect(player.forecast_reward, 5.00)
        expect(player.forecast_error, 0)

        # Round Result Page
        yield Submission(RoundResultsPage)

        if round_number == Constants.num_rounds:
            yield FinalResultsPage


def call_live_method(method, **kwargs):
    round_number = kwargs.get('round_number')
    if round_number != 1:
        return

    group: Group = kwargs.get('group')

    for player in group.get_players():
        test_place_order(method, player.id_in_group, -1, 4000, 2)
