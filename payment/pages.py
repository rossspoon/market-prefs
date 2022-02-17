from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
from rounds import get_js_vars


class ConsentDeniedPage(Page):
    def is_displayed(self):
        return not self.player.participant.CONSENT


class MarketResults(Page):
    js_vars = get_js_vars

    def is_displayed(self):
        return self.player.participant.CONSENT


page_sequence = [ConsentDeniedPage]
