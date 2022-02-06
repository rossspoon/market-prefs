import inspect
import sys

from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, Player


class IntroPage(Page):
    pass


class InstructionPage_01(Page):
    pass


class InstructionPage_02(Page):
    pass


class InstructionPage_03(Page):
    pass


class InstructionPage_04(Page):
    pass


class InstructionPage_05(Page):
    pass


class InstructionPage_06(Page):
    pass


class InstructionPage_07(Page):
    pass


class InstructionPage_08(Page):
    pass


class InstructionPage_09(Page):
    pass


class InstructionPage_10(Page):
    pass


class InstructionPage_11(Page):
    pass


class InstructionPage_12(Page):
    pass


class InstructionPage_13(Page):
    pass


class InstructionPage_14(Page):
    pass


class InstructionPage_15(Page):
    pass


class Quiz01(Page):
    form_model = Player
    form_fields = ['qz1q1', 'qz1q2', 'qz1q3', 'qz1q4']


class Quiz02(Page):
    form_model = Player
    form_fields = ['qz2q1', 'qz2q2', 'qz2q3']

class OutroPage(Page):
    pass


page_sequence = [IntroPage,
                 InstructionPage_01,
                 InstructionPage_02,
                 InstructionPage_03,
                 InstructionPage_04,
                 InstructionPage_05,
                 InstructionPage_06,
                 InstructionPage_07,
                 Quiz01,
                 InstructionPage_08,
                 InstructionPage_09,
                 InstructionPage_10,
                 InstructionPage_11,
                 InstructionPage_12,
                 InstructionPage_13,
                 InstructionPage_14,
                 InstructionPage_15,
                 Quiz02,
                 OutroPage]
