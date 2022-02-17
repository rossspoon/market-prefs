from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, Player


def determine_app(self, upcoming_apps):
    if not self.player.consent_given:
        return upcoming_apps[-1]


def record_consent(self):
    self.player.participant.CONSENT = self.player.consent_given


class ConsentPage(Page):
    form_model = Player
    form_fields = ['consent_given']
    app_after_this_page = determine_app
    before_next_page = record_consent


class IdPage(Page):
    pass


page_sequence = [ConsentPage, IdPage]
