from otree.api import Currency as c, currency_range, expect, Submission
from . import pages
from ._builtin import Bot
from .models import Constants
from .pages import ConsentPage, IdPage
import common.SessionConfigFunctions as scf


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(ConsentPage, {'consent_given': True})
        yield IdPage
