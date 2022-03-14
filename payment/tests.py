from otree.api import Submission

from ._builtin import Bot
from .pages import FinalResultsPage, ConsentDeniedPage


class PlayerBot(Bot):
    # noinspection PyMethodMayBeStatic
    def play_round(self):
        if self.player.participant.vars.get('CONSENT'):
            yield Submission(FinalResultsPage, check_html=False)
        else:
            yield Submission(ConsentDeniedPage, check_html=False)
