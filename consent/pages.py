import common.SessionConfigFunctions as scf
from common.CommonPges import UpdatedWaitPage
from ._builtin import Page
from .models import Player

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
    player = self.player
    player.participant.CONSENT = self.player.consent_given
    player.participant.CONSENT_BUTTON_CLICKED = self.player.button_clicked

    if not player.consent_given:
        player.participant.finished = True

class SplashPage(Page):
    def vars_for_template(self):
        p = self.player
        show_next = scf.show_next_button(p)
        return dict(show_next=show_next)


class InfoSheet(Page):
    form_model = Player
    form_fields = ['consent_given', 'button_clicked']
    app_after_this_page = determine_app
    before_next_page = record_consent
    #timeout_seconds = 600

    def is_displayed(self):
        player = self.player
        return scf.is_online(player)

    def vars_for_template(self):
        player = self.player
        ret = scf.ensure_config(player)
        exp_time = scf.get_expected_time(player)
        ret['expected_time'] = exp_time
        s = 's' if exp_time > 1 else ''
        ret['s'] = s
        return ret


class ConsentPage(Page):
    form_model = Player
    form_fields = ['consent_given', 'button_clicked']
    app_after_this_page = determine_app
    before_next_page = record_consent

    def is_displayed(self):
        player = self.player
        return not scf.is_online(player)


class IdPage(Page):
    #timeout_seconds = 120
    is_displayed = show_id_page

    def vars_for_template(self):
        p = self.player
        is_online = scf.is_online(p)
        show_next = scf.show_next_button(p)
        return dict(is_online=is_online, show_next=show_next)


class ConsentWaitPage(UpdatedWaitPage):
    body_text = "Welcome to the Virginia Tech Econ Lab Market experiment.  " \
                "The experiment will start when all participants have joined. Please be patient."


# page_sequence = [SplashPage, ConsentWaitPage, InfoSheet, ConsentPage, IdPage]
page_sequence = [ConsentWaitPage, ConsentPage]
