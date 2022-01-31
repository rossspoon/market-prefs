import inspect
import sys

from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants

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


def get_instruction_class_names():
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and x.__name__.startswith('InstructionPage'))]


page_sequence = [IntroPage] + get_instruction_class_names()
