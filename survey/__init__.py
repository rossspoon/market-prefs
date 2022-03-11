import inspect
import sys

from otree.api import *
from otree.forms.widgets import RadioSelectHorizontal, RadioSelect
from common.ParticipantFuctions import generate_participant_ids

doc = """
Socioeconomic Survey
"""


def creating_session(subsession):
    generate_participant_ids(subsession)


def make_likert_scale(label):
    return models.IntegerField(blank=True,
                               label=label,
                               # choices=[[-1, 'N/A'] + [[x, x] for x in range(11)]],
                               choices=list(range(-1, 11)),
                               widget=RadioSelect)


class Constants(BaseConstants):
    name_in_url = 'survey'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    @staticmethod
    def creating_session(subsession: BaseSubsession):
        generate_participant_ids(subsession)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    page_num = models.IntegerField(initial=0)
    gender = models.IntegerField(blank=True,
                                 choices=[[0, 'Male'],
                                          [1, 'Female'],
                                          [2, 'Non-binary'],
                                          [4, 'Prefer not to say']],
                                 label="What is your gender?")
    age = models.IntegerField(blank=True,
                              label="What is your age?")
    hisp = models.BooleanField(blank=True,
                               label="Are you Hispanic or Latino?",
                               widget=RadioSelectHorizontal)
    race = models.IntegerField(blank=True,
                               label="How would you describe yourself?",
                               choices=[
                                   [0, 'American Indian or Alaska Native '],
                                   [1, 'Asian'],
                                   [2, 'Black or African American'],
                                   [3, 'Native Hawaiian or Other Pacific Islander'],
                                   [4, 'Caucasian']
                               ])
    college = models.IntegerField(blank=True,
                                  label="How many years have you been at university/college?",
                                  choices=[
                                      [0, 'None'],
                                      [1, 1], [2, 2], [3, 3], [4, 4], [5, 5],
                                      [6, '6 or More']
                                  ])
    income = models.IntegerField(blank=True,
                                 label='What is your household income relative to others in your community?',
                                 choices=[
                                     [0, 'Significantly Higher'],
                                     [1, 'Somewhat Higher'],
                                     [2, 'About the Same'],
                                     [3, 'Somewhat Lower'],
                                     [4, 'Significantly Lower']
                                 ])
    employment = models.IntegerField(blank=True,
                                     label='What is your employment status:',
                                     choices=[
                                         [0, 'Employed Full-time'],
                                         [1, 'Employed Part-time'],
                                         [2, 'Do not have a job']
                                     ])
    major = models.IntegerField(blank=True,
                                label='What is your Major/College? (if more than one pick what you consider to be '
                                      'your primary Major or College)',
                                choices=[
                                    [-1, 'Not in College'],
                                    [0, 'Economics (either in COB or COS)'],
                                    [1, 'Architecture and Urban Studies'],
                                    [2, 'Agriculture and Life Science'],
                                    [3, 'Business other than Economics'],
                                    [4, 'Engineering '],
                                    [5, 'Liberal Arts and Human Sciences  '],
                                    [6, 'Natural Resources and Environment'],
                                ])
    econ_class = models.IntegerField(blank=True,
                                     label='How many Economics classes have you taken at the university level?',
                                     choices=[
                                         [0, 0],
                                         [1, 1],
                                         [2, 2],
                                         [3, 3],
                                         [4, '4 or more']
                                     ])
    religious_service = models.IntegerField(blank=True,
                                            label='Aside from weddings and funerals, about how often do you attend '
                                                  'religious services?',
                                            choices=[
                                                [0, 'Never'],
                                                [1, 'Less than once a year '],
                                                [3, 'Once a year'],
                                                [4, 'A few times a year'],
                                                [5, 'Once a month '],
                                                [6, 'Two or three times a month']
                                            ])
    vote_reg = models.BooleanField(blank=True,
                                   label="Are you registered to vote?",
                                   widget=RadioSelectHorizontal)
    vote_freq = models.IntegerField(blank=True,
                                    label="Which of the following best describes your voting behavior?",
                                    choices=[
                                        [0, 'I do not vote '],
                                        [1, 'I have not voted previously but plan to vote in the future  '],
                                        [2, 'I voted previously but do not plan to vote in the future '],
                                        [3, 'I vote only in minor elections '],
                                        [4, 'I vote only in major elections '],
                                        [5, 'I vote in all elections  ']
                                    ])
    politics = make_likert_scale(
        """Please describe your political orientation in general, using a scale from 0 to 10, where 0 means you are 
        “complete conservative” and 10 means you are “complete liberal.”""")
    risk = make_likert_scale(
        """How willing or unwilling you are to take risks, using a scale from 0 to 10, where 0 means you are 
        “completely unwilling to take risks” and 10 means you are “very willing to take risks.”""")
    time = make_likert_scale(
        """How willing are you to give up something that is beneficial for you today in order to benefit more from 
        that in the future? Please again indicate your answer on a scale from 0 to 10. A 0 means “completely 
        unwilling to do so,” and a 10 means “very willing to do so.”""")
    procrast = make_likert_scale(
        """How well does the following statement describe you as a person? “I tend to postpone tasks even if I know 
        it would be better to do them right away.” Please indicate your answer on a scale from 0 to 10. A 0 means 
        “does not describe me at all,” and a 10 means “describes me perfectly.”""")
    pos_reciprocity = make_likert_scale(
        """How well does the following statement describe you as a person? “When someone does me a favor, 
        I am willing to return it.” Please indicate your answer on a scale from 0 to 10. A 0 means “does not describe 
        me at all,” and a 10 means “describes me perfectly.”""")
    neg_reciprocity = make_likert_scale(
        """How willing are you to punish someone who treats YOU unfairly, even if there may be costs for you? Please 
        again indicate your answer on a scale from 0 to 10. A 0 means “completely unwilling to do so,” and a 10 means 
        “very willing to do so.”""")
    good_cause = make_likert_scale(
        """How willing are you to give to good causes without expecting anything in return? Please again indicate 
        your answer on a scale from 0 to 10. A 0 means “completely unwilling to do so,” and a 10 means “very willing 
        to do so.”""")
    good_intent = make_likert_scale(
        """How well does the following statement describe you as a person? “I assume that people have only the best 
        intentions.” Please indicate your answer on a scale from 0 to 10. A 0 means “does not describe me at all,
        ” and a 10 means “describes me perfectly.”""")
    punish_self = make_likert_scale(
        """How well does the following statement describe you as a person? “If I am treated very unjustly, 
        I will take revenge at the first occasion, even if there is a cost to do so.” Please indicate your answer on 
        a scale from 0 to 10. A 0 means “does not describe me at all,” and a 10 means “describes me perfectly.”""")
    punish_others = make_likert_scale(
        """How willing are you to punish someone who treats OTHERS unfairly, even if there may be costs for you? 
        Please again indicate your answer on a scale from 0 to 10. A 0 means “completely unwilling to do so,
        ” and a 10 means “very willing to do so.”""")
    math = make_likert_scale(
        """How well does the following statement describe you as a person? “I am good at math.” Please indicate your 
        answer on a scale from 0 to 10. A 0 means “does not describe me at all,” and a 10 means “describes me 
        perfectly.”""")

    bat_and_ball = models.IntegerField(blank=True,
                                       label="""A bat and a ball cost 22 dollars in total. The bat costs 20 dollars 
                                       more than the ball. How many dollars does the ball cost? """,
                                       choices=[[x, f'${x}.00'] for x in range(22)]
                                       )
    widgets = models.IntegerField(blank=True,
                                  label="""If it takes 5 machines 5 minutes to make 5 widgets, how many minutes would 
                                  it take 100 machines to make 100 widgets? """,
                                  choices=list(range(0, 105, 5))
                                  )
    lilies_on_lake = models.IntegerField(blank=True,
                                         label="""In a lake there is a patch of lily pads. Every day the patch 
                                          doubles in size. If it takes 48 days for the patch to cover the entire 
                                          lake, how many days would it take for the patch to cover half of the
                                           lake? """,
                                         choices=list(range(24, 49))
                                         )
    confuse = models.LongStringField(blank=True,
                                     label="""Did anything in the experiment confuse you?"""
                                     )
    anything_else = models.LongStringField(blank=True,
                                           label="""Is there anything else you would like to tell the experimenters 
                                           about this 
                                            experiment? """
                                           )


def is_SP_class(x):
    return inspect.isclass(x) and x.__name__.startswith('SurveyPage_')


def get_SP_classes():
    return [t[1] for t in inspect.getmembers(sys.modules[__name__], predicate=is_SP_class)]


def common_vars_for_temp(player: Player):
    number_of_pages = len(get_SP_classes())
    return dict(number_of_pages=number_of_pages)


def update_player_page_number(player: Player, timeout_happened):
    if not player.page_num:
        player.page_num = 0
    player.page_num += 1


# FUNCTIONS
# PAGES
class SurveyBasePage(Page):
    form_model = Player
    before_next_page = update_player_page_number
    vars_for_template = common_vars_for_temp


class IntroPage(SurveyBasePage):
    pass


class SurveyPage_01(SurveyBasePage):
    form_fields = ['gender', 'age', 'hisp', 'race', 'college', 'income', 'employment']
    template_name = 'survey/survey_page_side_by_side.html'


class SurveyPage_02(SurveyBasePage):
    form_fields = ['major', 'econ_class', 'religious_service', 'vote_reg', 'vote_freq']
    template_name = 'survey/survey_page_side_by_side.html'


class SurveyPage_03(SurveyBasePage):
    form_fields = ['politics', 'risk', 'time', 'procrast']
    template_name = 'survey/survey_page_likert.html'


class SurveyPage_04(SurveyBasePage):
    form_fields = ['pos_reciprocity', 'neg_reciprocity', 'good_cause', 'good_intent']
    template_name = 'survey/survey_page_likert.html'


class SurveyPage_05(SurveyBasePage):
    form_fields = ['punish_self', 'punish_others', 'math']
    template_name = 'survey/survey_page_likert.html'


class SurveyPage_06(SurveyBasePage):
    form_fields = ['bat_and_ball', 'widgets', 'lilies_on_lake', 'confuse', 'anything_else']
    template_name = 'survey/survey_page_side_by_side.html'


page_sequence = [IntroPage] + get_SP_classes()
