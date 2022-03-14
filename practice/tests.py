import otree.api

from bots.scripted_bot import test_place_order
from practice import PracticeMarketPage, PracticeForecastPage, PracticeRoundResultsPage, C, PracticeEndPage, Group

f0s = [0, 3000, 2500, 1500]


class PlayerBot(otree.api.Bot):
    def play_round(self):
        yield PracticeMarketPage
        round_number = self.round_number
        f0 = f0s[round_number]
        form_data = {'f0': f0}
        if round_number < C.NUM_ROUNDS:
            form_data['f1'] = 0
        if round_number < C.NUM_ROUNDS - 1:
            form_data['f2'] = 0

        yield otree.api.Submission(PracticeForecastPage, form_data)

        player = self.player
        otree.api.expect(player.forecast_reward, 500)
        otree.api.expect(player.forecast_error, 100 if round_number == 3 else 0)

        yield PracticeRoundResultsPage

        if round_number == C.NUM_ROUNDS:
            yield PracticeEndPage


def call_live_method(method, **kwargs):
    round_number = kwargs.get('round_number')
    if round_number != 1:
        return

    group: Group = kwargs.get('group')

    for player in group.get_players():
        test_place_order(method, player.id_in_group, -1, 4000, 2)
