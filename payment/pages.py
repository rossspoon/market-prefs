from ._builtin import Page


class ConsentDeniedPage(Page):
    def is_displayed(self):
        participant = self.player.participant
        return not participant.vars.get('CONSENT') and participant.vars.get('CONSENT_BUTTON_CLICKED')


class FinalResultsPage(Page):
    def vars_for_template(self):
        participant = self.player.participant
        session = self.player.session
        return {'bonus_rwc': participant.payoff.to_real_world_currency(session),
                'total_pay': participant.payoff_plus_participation_fee()
                }

    def is_displayed(self):
        participant = self.player.participant
        return participant.vars.get('CONSENT') and participant.vars.get('CONSENT_BUTTON_CLICKED')


class NonParticipantPage(Page):
    def is_displayed(self):
        player = self.player
        return not player.participant.vars.get('CONSENT_BUTTON_CLICKED')


page_sequence = [ConsentDeniedPage, FinalResultsPage, NonParticipantPage]
