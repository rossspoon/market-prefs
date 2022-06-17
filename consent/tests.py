from otree.api import Submission

from ._builtin import Bot
from .pages import ConsentPage, IdPage, InfoSheet
import common.SessionConfigFunctions as scf


class PlayerBot(Bot):

    # noinspection PyMethodMayBeStatic
    def play_round(self):
        if scf.is_online(self.player):
            yield Submission(InfoSheet, {'consent_given': True, 'button_clicked': True})
        else:
            yield Submission(ConsentPage, {'consent_given': True, 'button_clicked': True})
            yield IdPage
