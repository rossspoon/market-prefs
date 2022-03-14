from otree.api import Bot

from . import page_sequence


class PlayerBot(Bot):
    # noinspection PyMethodMayBeStatic
    def play_round(self):
        for page in page_sequence:
            yield page
