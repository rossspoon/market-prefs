import otree.api
from otree.bots import Submission

from bots.scripted_bot import test_place_order
from practice import PracticeMarketPage, PracticeForecastPage, PracticeRoundResultsPage, C, PracticeEndPage, Group

f0s = [0, 30.00, 25.00, 15.00]


class PlayerBot(otree.api.Bot):
    def play_round(self):
        yield Submission(PracticeMarketPage, check_html=False)

        round_number = self.round_number
        f0 = f0s[round_number]
        form_data = {'f0': f0}

        yield otree.api.Submission(PracticeForecastPage, form_data)

        player = self.player
        otree.api.expect(player.forecast_reward, 5.00)
        otree.api.expect(player.forecast_error, 1.00 if round_number == 3 else 0)

        yield PracticeRoundResultsPage

        if round_number == C.NUM_ROUNDS:
            yield PracticeEndPage


def call_live_method(method, **kwargs):
    round_number = kwargs.get('round_number')
    if round_number != 1:
        return

    page_class = kwargs.get('page_class')
    if not (page_class is PracticeMarketPage):
        return

    group: Group = kwargs.get('group')

    for player in group.get_players():
        test_place_order(method, player.id_in_group, -1, 40.00, 2)
