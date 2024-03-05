from otree.api import Submission

from ._builtin import Bot
from .pages import ConsentPage, IdPage, InfoSheet, SplashPage
import common.SessionConfigFunctions as scf


class PlayerBot(Bot):

    # noinspection PyMethodMayBeStatic
    def play_round(self):
        if scf.is_online(self.player):
            yield Submission(InfoSheet, {'consent_given': True, 'button_clicked': True})
        else:
            #yield Submission(SplashPage, check_html=False)
            yield Submission(ConsentPage, {'consent_given': True, 'button_clicked': True})
            #yield Submission(IdPage, check_html=False)
