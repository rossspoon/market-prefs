from otree.api import cu

from ._builtin import Page
import common.SessionConfigFunctions as scf


class ConsentDeniedPage(Page):
    def is_displayed(self):
        participant = self.player.participant
        return not participant.vars.get('CONSENT') and participant.vars.get('CONSENT_BUTTON_CLICKED')

    def vars_for_template(self):
        is_online = scf.is_online(self.player)
        is_prolific = scf.is_prolific(self.player)
        is_mturk = scf.is_mturk(self.player)

        mturk_completion_code = self.player.participant.code

        url = self.player.session.vars.get('prolific_completion_url')
        if not url:
            url = "https://www.vt.edu"

        return {'is_online': is_online,
                'is_prolific': is_prolific,
                'is_mturk': is_mturk,
                'prolific_completion_url': url,
                'mturk_completion_code': mturk_completion_code}


class FinalResultsPage(Page):
    def vars_for_template(self):

        participant = self.player.participant
        session = self.player.session
        market_bonus = participant.vars.get('MARKET_PAYMENT').to_real_world_currency(session)
        forecast_bonus = participant.vars.get('FORECAST_PAYMENT').to_real_world_currency(session)
        risk_bonus = participant.vars.get('RISK_PAYMENT').to_real_world_currency(session)
        is_online = scf.is_online(self.player)
        is_prolific = scf.is_prolific(self.player)
        is_mturk = scf.is_mturk(self.player)
        mturk_completion_code = self.player.participant.code
        url = self.player.session.vars.get('prolific_completion_url')
        if not url:
            url = "https://www.vt.edu"

        return {'market_bonus': market_bonus,
                'forecast_bonus': forecast_bonus,
                'risk_bonus': risk_bonus,
                'total_bonus': market_bonus + forecast_bonus,
                'total_pay': participant.payoff_plus_participation_fee(),
                'is_prolific': is_prolific,
                'is_mturk': is_mturk,
                'is_online': is_online,
                'prolific_completion_url': url,
                'mturk_completion_code': mturk_completion_code}

    def is_displayed(self):
        participant = self.player.participant
        return participant.vars.get('CONSENT') and participant.vars.get('CONSENT_BUTTON_CLICKED')


class NonParticipantPage(Page):
    def is_displayed(self):
        player = self.player
        return not player.participant.vars.get('CONSENT_BUTTON_CLICKED')


page_sequence = [ConsentDeniedPage, FinalResultsPage, NonParticipantPage]
