from ._builtin import Page
from .models import Player


def determine_app(self, upcoming_apps):
    player = self.player
    if not player.consent_given:
        return upcoming_apps[-1]


def show_id_page(self):
    player = self.player
    return player.consent_given


def record_consent(self):
    self.player.participant.CONSENT = self.player.consent_given
    self.player.participant.CONSENT_BUTTON_CLICKED = self.player.button_clicked


class ConsentPage(Page):
    form_model = Player
    form_fields = ['consent_given', 'button_clicked']
    app_after_this_page = determine_app
    before_next_page = record_consent


class IdPage(Page):
    is_displayed = show_id_page


page_sequence = [ConsentPage, IdPage]
