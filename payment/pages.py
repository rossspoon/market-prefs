from ._builtin import Page, WaitPage


class ConsentDeniedPage(Page):
    def is_displayed(self):
        return not self.player.participant.CONSENT


class FinalResultsPage(Page):
    def vars_for_template(self):
        participant = self.player.participant
        session = self.player.session
        return {'bonus_rwc': participant.payoff.to_real_world_currency(session),
                'total_pay': participant.payoff_plus_participation_fee()
                }

    def is_displayed(self):
        return self.player.participant.CONSENT


page_sequence = [ConsentDeniedPage, FinalResultsPage]
