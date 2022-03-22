from otree.api import Submission

from ._builtin import Bot
from .pages import ConsentPage, IdPage


class PlayerBot(Bot):

    # noinspection PyMethodMayBeStatic
    def play_round(self):
        yield Submission(ConsentPage, {'consent_given': True, 'button_clicked': True})
        yield IdPage
