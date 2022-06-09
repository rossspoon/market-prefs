from otree.api import WaitPage
from otree.models import Participant

from common.CommonPges import UpdatedWaitPage
from ._builtin import Page
from .models import Player
import common.SessionConfigFunctions as scf


def determine_app(self, upcoming_apps):
    player = self.player
    if not player.consent_given:
        return upcoming_apps[-1]


def show_id_page(self):
    # Don't show this page for online experiments
    if scf.is_online(self.player):
        return False

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
    timeout_seconds = 120
    is_displayed = show_id_page

    def vars_for_template(self):
        p = self.player
        is_online = scf.is_online(p)
        return dict(is_online = is_online)


class ConsentWaitPage(UpdatedWaitPage):
    body_text = "Welcome to the Virginia Tech Econ Lab Market experiment.  " \
                "The experiment will start when all participants have joined. Please be patient."


page_sequence = [ConsentWaitPage, ConsentPage, IdPage]
