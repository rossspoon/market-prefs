from otree.api import Submission, expect
from otree.bots import Bot
import random
import time

from landingct import Consent,  Instructions, QuizInstructions, Quiz, Survey1,  WaitForPlayers, ReadyToStart, NoConsent
BUY_RANGE = (-5, 5)
SELL_RANGE = 5

class PlayerBot(Bot):

    def play_round(self):
        yield Consent,  dict(consent_given=True)
        
        yield Submission(Instructions,  check_html=False)
        yield Submission(QuizInstructions,  check_html=False)
        yield Submission(Quiz,  check_html=False)
        q_grade = random.randint(0,5)
        self.player.quiz_grade = q_grade
        
        yield Submission(Survey1,  check_html=False)
        yield Submission(WaitForPlayers,  check_html=False)
        yield Submission(ReadyToStart,  check_html=False)
