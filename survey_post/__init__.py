from otree.api import *

doc = "Post-experimental questionnaire"


class C(BaseConstants):
    NAME_IN_URL = 'survey_post'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    PRIOR_EXPERIENCE_CHOICES = [
        [1, 'Yes, multiple times'],
        [2, 'Yes, just once'],
        [3, 'No'],
    ]

    UNDERSTANDING_CHOICES = [
        [1, 'Yes, entirely'],
        [2, 'Yes, but partially, I understood more as I continued trading'],
        [3, 'No, not at all'],
    ]

    OWN_STOCKS_CHOICES = [
        [1, 'YES'],
        [2, 'NO'],
    ]

    # Gamble choices for risk & loss aversion
    # Option 1: 100% chance of $10
    # Option 2: 50% chance of $0, 50% chance of RISKY_AMOUNTS[i]
    RISKY_AMOUNTS = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    # ── Page 3: Feedback ──────────────────────────────────────────────────
    prior_experience = models.IntegerField(
        label='Have you participated in similar trading experiments before?',
        choices=C.PRIOR_EXPERIENCE_CHOICES,
        widget=widgets.RadioSelect,
    )
    task_understanding_scale = models.IntegerField(
        label='On a scale from 1-10, how well did you understand the task and were able to trade as required?',
        choices=[(i, str(i)) for i in range(1, 11)],
        widget=widgets.RadioSelect,
    )
    understood_from_beginning = models.IntegerField(
        label='Did you understand exactly what you had to do from the beginning?',
        choices=C.UNDERSTANDING_CHOICES,
        widget=widgets.RadioSelect,
    )
    trading_strategy = models.LongStringField(
        label='Did you follow any strategy when trading? Please describe, be as detailed as possible.',
    )
    suggestions = models.LongStringField(
        label='Do you have any suggestions to improve the experiment? i.e. the software, the trading instructions, time to enter orders, time to enter forecast, time to do the risk elicitation task etc.',
    )
    own_stocks = models.IntegerField(
        label='Do you own/trade stocks?',
        choices=C.OWN_STOCKS_CHOICES,
        widget=widgets.RadioSelect,
    )

    # ── Page 4: Performance ───────────────────────────────────────────────
    perceived_performance = models.IntegerField(
        label=(
            'Imagine you performed the tasks with another 99 persons. '
            'In terms of performance, on what place do you think you placed? '
            'How would you rate your outcome from 1-100?'
        ),
        min=1,
        max=100,
    )

    # ── Page 5: Risk-taking ───────────────────────────────────────────────
    risk_general = models.IntegerField(
        label='How would you rate your risk-taking behavior in general, on a scale from 1-7?',
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect,
    )
    risk_financial = models.IntegerField(
        label='How would you rate your financial risk-taking behavior, on a scale from 1-7?',
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect,
    )
    investment_amount = models.IntegerField(
        label=(
            'You have been given $100. You can invest any part of this money in a risky asset. '
            'If the investment is successful, the risky asset returns 2.5 times the amount invested '
            'with a probability of one-half and nothing with a probability of one-half. '
            'You can also choose not to invest at all, in which case you will keep the money you have. '
            'How much would you like to invest? (write amount in dollars)'
        ),
        min=0,
        max=100,
    )

    # ── Page 6: Risk & Loss Aversion (12 gamble choices) ──────────────────
    gamble_01 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_02 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_03 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_04 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_05 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_06 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_07 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_08 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_09 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_10 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_11 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)
    gamble_12 = models.IntegerField(choices=[[1,'Option 1'],[2,'Option 2']], widget=widgets.RadioSelect)


# ── PAGES ─────────────────────────────────────────────────────────────────

class Intro(Page):
    """Page 1 — Instructions"""
    pass


class Feedback(Page):
    """Page 3 — Feedback task"""
    form_model = 'player'
    form_fields = [
        'prior_experience',
        'task_understanding_scale',
        'understood_from_beginning',
        'trading_strategy',
        'suggestions',
        'own_stocks',
    ]


class Performance(Page):
    """Page 4 — Performance self-assessment"""
    form_model = 'player'
    form_fields = ['perceived_performance']


class RiskTaking(Page):
    """Page 5 — Risk-taking attitudes"""
    form_model = 'player'
    form_fields = [
        'risk_general',
        'risk_financial',
        'investment_amount',
    ]


class RiskLossAversion(Page):
    """Page 6 — Risk and Loss Aversion gambles"""
    form_model = 'player'
    form_fields = [
        'gamble_01', 'gamble_02', 'gamble_03', 'gamble_04',
        'gamble_05', 'gamble_06', 'gamble_07', 'gamble_08',
        'gamble_09', 'gamble_10', 'gamble_11', 'gamble_12',
    ]

    @staticmethod
    def vars_for_template(player):
        # Build list of (field_name, risky_amount) pairs for the template
        gambles = [
            (f'gamble_{i+1:02d}', amount)
            for i, amount in enumerate(C.RISKY_AMOUNTS)
        ]
        return dict(gambles=gambles)


class Conclusion(Page):
    """Page 7 — Thank you"""
    pass


page_sequence = [
    Intro,
    Feedback,
    Performance,
    RiskTaking,
    RiskLossAversion,
    Conclusion,
]
