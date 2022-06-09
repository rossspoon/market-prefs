from otree.api import SubmissionMustFail, WaitPage

import instructions.pages
from ._builtin import Bot
from .pages import Quiz02


class PlayerBot(Bot):
    def play_round(self):
        for page in instructions.pages.page_sequence:
            if page == Quiz02:
                yield SubmissionMustFail(page)

            if issubclass(page, WaitPage):
                continue

            yield page
