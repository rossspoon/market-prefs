from otree.api import (
    models,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
)

from common.ParticipantFuctions import generate_participant_ids

doc = """
Handle Consent
"""

NON_PARTICIPANT = -1
CONSENT_NOT_GIVEN = 0
CONSENT_GIVEN = 1


class Constants(BaseConstants):
    name_in_url = 'consent'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    @staticmethod
    def creating_session(subsession: BaseSubsession):
        generate_participant_ids(subsession)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consent_given = models.BooleanField()
    button_clicked = models.BooleanField()
