from otree.api import Submission

from ._builtin import Bot
from .pages import ConsentPage, IdPage
import common.SessionConfigFunctions as scf


class PlayerBot(Bot):

    # noinspection PyMethodMayBeStatic
    def play_round(self):
        yield Submission(ConsentPage, {'consent_given': True, 'button_clicked': True})
        if not scf.is_online(self.player):
            yield IdPage
