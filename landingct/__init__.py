from otree.api import *
from common.ParticipantFuctions import generate_participant_ids
import time
from datetime import date
import common.SessionConfigFunctions as scf

doc = ''

class C(BaseConstants):
    NAME_IN_URL = 'wait'
    PLAYERS_PER_GROUP = None
    MIN_PLAYERS_PER_GROUP = 3  # should be 25
    NUM_ROUNDS = 1
    WAIT_TIMEOUT = 1200   # 20min max for waiting room
    INST_TIMEOUT = 720    # 12min max for instructions
    CONSENT_TIMEOUT = 900 # 15min max for consent
    START_TIMEOUT = 120   # 2min for start the game
    QUIZ_TIMEOUT = 600
    PRE_SURVEY_TIMEOUT = 900  # 15min max for pre-survey

    # ── Pre-survey: Demographics ───────────────────────────────────
    GENDER_CHOICES = [
        [1, 'Male'],
        [2, 'Female'],
        [3, 'Non-binary'],
        [4, 'Prefer not to say'],
    ]
    HISPANIC_CHOICES = [
        [1, 'No'],
        [2, 'Yes'],
        [3, 'Prefer not to say'],
    ]
    RACE_CHOICES = [
        [1, 'White caucasian'],
        [2, 'Black or African American'],
        [3, 'American Indian or Alaska Native'],
        [4, 'Asian or Asian Indian'],
        [5, 'Native Hawaiian or Other Pacific Islander'],
        [6, 'Other'],
        [7, 'Prefer not to say'],
    ]
    STUDIES_CHOICES = [
        [1, 'Social sciences: economics, psychology'],
        [2, 'IT and software'],
        [3, 'STEM'],
        [4, 'Humanities and arts'],
        [5, "I don't have higher education studies"],
        [6, 'Other (please specify below)'],
    ]
    NATIVE_ENGLISH_CHOICES = [
        [1, 'Yes'],
        [2, 'No'],
    ]
    MEDICATION_CHOICES = [
        [1, 'Yes'],
        [2, 'No'],
        [3, 'Prefer not to say'],
    ]


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    session = subsession.session

    today = date.today().strftime("%Y-%m-%d")
    session.label = today
    session.comment = "Landing Page"

    for player in subsession.get_players():
        player.participant.is_dropout = False    # ← add this
        player.participant.vars['is_dropout'] = False
        player.participant.is_single = 0
    session.arrived_ids = set()
    session.enrolled_ids = 0

    generate_participant_ids(subsession)
    for p in subsession.get_players():
        p.participant.survey_1_click = False


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # ── Landing / quiz fields ──────────────────────────────────────
    timeout = models.FloatField(initial=0.0)
    consent_given = models.BooleanField(initial=False)

    quiz_1 = models.StringField(blank=True,
                label="During order entry you want to input a BUY order at price of 8.52 and a SELL order at a price of 7.89. What will happen to your orders for that period?",
                choices=[["1", "They'll be entered as usual"],
                         ["2", "The SELL order will not go through"]])
    quiz_2 = models.StringField(blank=True,
                label="During order entry the highest price at which you submit a BUY order is 16.78 and the lowest price at which others SELL is 16.22. The market price is 16.56 for that period. You will:",
                choices=[["1", "BUY one unit at 16.78"],
                         ["2", "BUY one unit at 16.56"],
                         ["3", "SELL one unit at 16.56"],
                         ["4", "SELL one unit at 17.22"],
                         ["5", "Not Trade"]])
    quiz_3 = models.StringField(blank=True,
                label="You have 200 units of CASH at the start of a trading period and no STOCK. You do not trade that period. How much CASH do you have at the beginning of the next period?",
                choices=["200", "210", "205", "190"])
    quiz_4 = models.StringField(blank=True,
                label="Your account has 5 STOCK and 100 CASH at the start of a trading period, and you do not BUY or SELL during that period. The dividend for that round is 1.00. How much CASH do you have at the start of the next round?",
                choices=["105", "110", "100", "114"])
    quiz_5 = models.StringField(blank=True,
                label="After the final trading period, you have 1 remaining unit of STOCK. The market price in the final period is 29. How many units of experiment CASH do you receive in exchange for your STOCK?",
                choices=["1", "29", "14", "30"])

    quiz_1_init = models.StringField(blank=True)
    quiz_2_init = models.StringField(blank=True)
    quiz_3_init = models.StringField(blank=True)
    quiz_4_init = models.StringField(blank=True)
    quiz_5_init = models.StringField(blank=True)
    quiz_grade = models.IntegerField(initial=0)
    quiz_attempt = models.IntegerField(initial=0)
    quiz_failed = models.BooleanField(initial=False)

    # ── Pre-survey: Demographics ───────────────────────────────────
    age = models.IntegerField(
        label='Your age (in years):',
        min=18, max=100,
    )
    gender = models.IntegerField(
        label='Your gender:',
        choices=C.GENDER_CHOICES,
    )
    hispanic = models.IntegerField(
        label='Are you of Hispanic, Latino/a, or of Spanish origin? (one or more categories may be selected)',
        choices=C.HISPANIC_CHOICES,
        widget=widgets.RadioSelect,
    )
    race = models.IntegerField(
        label='What is your race?',
        choices=C.RACE_CHOICES,
    )
    studies_background = models.IntegerField(
        label='Studies background',
        choices=C.STUDIES_CHOICES,
        widget=widgets.RadioSelect,
    )
    studies_other = models.StringField(
        label='If "Other", please specify your studies background:',
        blank=True,
    )
    native_english = models.IntegerField(
        label='Are you a native English speaker (i.e. is English your mother tongue?)',
        choices=C.NATIVE_ENGLISH_CHOICES,
    )
    english_proficiency = models.IntegerField(
        label=(
            'On a scale from 0 to 5, how good is your knowledge of English? '
            '(If YES to previous question, please mark 5 here) '
            '0 = Extremely poor, 5 = Proficient'
        ),
        choices=[(i, str(i)) for i in range(0, 6)],
        widget=widgets.RadioSelect,
    )
    medication = models.IntegerField(
        label='Are you currently under medication treatment for depression, anxiety, or other psychiatric or neurological conditions?',
        choices=C.MEDICATION_CHOICES,
    )

    # ── Pre-survey: Risk taking ────────────────────────────────────
    pre_risk_general = models.IntegerField(
        label='How would you rate your risk-taking behavior in general, on a scale from 1-7?',
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect,
    )
    pre_risk_financial = models.IntegerField(
        label='How would you rate your financial risk-taking behavior, on a scale from 1-7?',
        choices=[(i, str(i)) for i in range(1, 8)],
        widget=widgets.RadioSelect,
    )
    pre_investment_amount = models.IntegerField(
        label=(
            'You have been given $100. You can invest any part of this money in a risky asset. '
            'If the investment is successful, the risky asset returns 2.5 times the amount invested '
            'with a probability of one-half and nothing with a probability of one-half. '
            'You can also choose not to invest at all, in which case you will keep the money you have. '
            'How much would you like to invest? (write amount in dollars)'
        ),
        min=0, max=100,
    )

    qualifies_for_study = models.BooleanField(
           blank=True,
           doc="Participant confirmed they meet eligibility criteria",
       )
    future_contact_pref = models.IntegerField(
           blank=True,
           choices=[
               [1, 'Non-profit funded studies only'],
               [2, 'For-profit funded studies only'],
               [3, 'Any Caltech studies regardless of funding'],
               [4, 'Do not contact me'],
           ],
           doc="Future contact preference from consent form",
       )

    consent_initials = models.StringField(
        label="Print your initials (as substitute for signature):",
        blank=True,
    )   

# ── Helpers ────────────────────────────────────────────────────────────────

def get_exp_link(player: Player):
    config = player.session.config
    is_local = config['experiment_link_is_local']
    return config['experiment_link_local'] if is_local else config['experiment_link']


def template_vars_commom(player: Player):
    ret = player.session.config.copy()
    ret['prolific_completion_url'] = player.session.vars.get(
        'prolific_completion_url', 'http://www.prolific.com'
    )
    return ret


def is_displayed_common(player: Player):
    return player.consent_given and not player.quiz_failed


# ── Pages ──────────────────────────────────────────────────────────────────

class Consent(Page):
    timeout_seconds = C.CONSENT_TIMEOUT
    timer_text = "Time Left to Complete the Consent: "
    form_model = 'player'
    form_fields = ['consent_given', 'qualifies_for_study', 'future_contact_pref', 'consent_initials']
 
    @staticmethod
    def vars_for_template(player: Player):
        return player.session.config

    @staticmethod
    def js_vars(player: Player):
        return dict(consent_pg_cnt=player.session.config.get('consent_pg_cnt'))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        p = player.participant
        consent = player.field_maybe_none('consent_given')
        qualifies = player.field_maybe_none('qualifies_for_study')
    
        if timeout_happened or not consent or not qualifies:
            player.consent_given = False
            p.vars['is_dropout'] = True
            p.is_dropout = True
            
    @staticmethod
    def is_displayed(player: Player):
        p = player.participant
        return not p.vars.get('is_dropout', False)


class NoConsent(Page):
    vars_for_template = template_vars_commom

    @staticmethod
    def is_displayed(player: Player):
        return not player.consent_given


class Instructions(Page):
    timeout_seconds = C.INST_TIMEOUT
    timer_text = "Time Left to Complete the Instructions: "
    form_model = 'player'
    is_displayed = is_displayed_common

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['is_dropout'] = timeout_happened
        player.participant.is_dropout = timeout_happened

    @staticmethod
    def app_after_this_page(player, upcoming_apps):
        if player.participant.vars['is_dropout']:
            return upcoming_apps[-1]

    @staticmethod
    def js_vars(player: Player):
        config = player.session.config
        return dict(inst_id=config.get('instruction_id'), show_next=config['show_next'])

    @staticmethod
    def vars_for_template(player: Player):
        return player.session.config


class HighStakes(Page):
    timeout_seconds = 30

    @staticmethod
    def is_displayed(player: Player):
        return is_displayed_common(player) and player.session.config.get('is_hi_stakes')

    @staticmethod
    def vars_for_template(player: Player):
        ret = player.session.config
        ret['conv'] = int(1 / scf.get_conversion_rate(player))
        return ret


class QuizInstructions(Page):
    timeout_seconds = 60
    is_displayed = is_displayed_common

    @staticmethod
    def vars_for_template(player: Player):
        return player.session.config


def quiz_grade_vars(data: dict):
    q1_score = 1 if data.get('quiz_1') == '2' else 0
    q2_score = 1 if data.get('quiz_2') == '2' else 0
    q3_score = 1 if data.get('quiz_3') == '210' else 0
    q4_score = 1 if data.get('quiz_4') == '110' else 0
    q5_score = 1 if data.get('quiz_5') == '14' else 0
    total_score = q1_score + q2_score + q3_score + q4_score + q5_score
    return {
        1: q1_score, 2: q2_score, 3: q3_score, 4: q4_score, 5: q5_score,
        'total_score': total_score,
    }


def quiz_live_method(player, data):
    func = data['func']
    attempt = player.quiz_attempt

    if func == 'grade_it':
        attempt += 1
        form_data = data['data']

        if attempt == 1:
            player.quiz_1_init = form_data['quiz_1']
            player.quiz_2_init = form_data['quiz_2']
            player.quiz_3_init = form_data['quiz_3']
            player.quiz_4_init = form_data['quiz_4']
            player.quiz_5_init = form_data['quiz_5']

        grades = quiz_grade_vars(form_data)
        quiz_grade = grades['total_score']
        show_next = quiz_grade == 5
        is_dev = player.session.config['show_next']
        is_prolific = True if is_dev else len(player.participant.label) > 20
        init_fail = quiz_grade == 0 and attempt == 1 and is_prolific

        ret = {player.id_in_group: dict(
            func="graded",
            grades=grades,
            show_next=show_next,
            failed=init_fail,
        )}

        player.quiz_1 = form_data['quiz_1']
        player.quiz_2 = form_data['quiz_2']
        player.quiz_3 = form_data['quiz_3']
        player.quiz_4 = form_data['quiz_4']
        player.quiz_5 = form_data['quiz_5']
        player.quiz_attempt = attempt
        player.quiz_failed = init_fail

        if init_fail:
            player.participant.vars['is_dropout'] = True
            player.participant.is_dropout = True

        if attempt == 1:
            player.quiz_grade = quiz_grade
            player.participant.quiz_grade = quiz_grade

        return ret

    elif func == 'load':
        ret = dict(
            func="load",
            quiz_1=player.field_maybe_none('quiz_1'),
            quiz_2=player.field_maybe_none('quiz_2'),
            quiz_3=player.field_maybe_none('quiz_3'),
            quiz_4=player.field_maybe_none('quiz_4'),
            quiz_5=player.field_maybe_none('quiz_5'),
        )

        if attempt > 0:
            grades = quiz_grade_vars(ret)
            ret['grades'] = grades
            ret['show_next'] = grades['total_score'] == 5
            ret['failed'] = grades['total_score'] == 0 and attempt == 1

        return {player.id_in_group: ret}


class Quiz(Page):
    form_model = 'player'
    form_fields = ['quiz_1', 'quiz_2', 'quiz_3', 'quiz_4', 'quiz_5']
    timeout_seconds = C.QUIZ_TIMEOUT
    live_method = quiz_live_method
    is_displayed = is_displayed_common

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            is_prolific = len(player.participant.label) > 20
            player.quiz_failed = is_prolific
            if is_prolific:                              # ← add these
                player.participant.vars['is_dropout'] = True
                player.participant.is_dropout = True

# ── Pre-survey pages ───────────────────────────────────────────────────────

class PreSurveyIntro(Page):
    is_displayed = is_displayed_common


class Demographics(Page):
    timeout_seconds = C.PRE_SURVEY_TIMEOUT
    timer_text = "Time Left to Complete the Survey: "
    form_model = 'player'
    form_fields = [
        'age', 'gender', 'hispanic', 'race',
        'studies_background', 'studies_other',
        'native_english', 'english_proficiency', 'medication',
    ]
    is_displayed = is_displayed_common

    @staticmethod
    def error_message(player, values):
        if values.get('studies_background') == 6 and not values.get('studies_other', '').strip():
            return 'Please specify your studies background.'


class PreRiskTaking(Page):
    timeout_seconds = C.PRE_SURVEY_TIMEOUT
    timer_text = "Time Left to Complete the Survey: "
    form_model = 'player'
    form_fields = ['pre_risk_general', 'pre_risk_financial', 'pre_investment_amount']
    is_displayed = is_displayed_common


class PreSurveyConclusion(Page):
    is_displayed = is_displayed_common


# ── Wait / ready pages ─────────────────────────────────────────────────────

class WaitForPlayers(Page):
    is_displayed = is_displayed_common
    vars_for_template = template_vars_commom

    @staticmethod
    def live_method(player: Player, data):
        session = player.session

        if data['func'] == 'status_change':
            if data['out'] == 0:
                session.arrived_ids.add(player.id_in_group)
            elif data['out'] == 1:
                session.arrived_ids.remove(player.id_in_group)

        expected = [
            p for p in session.get_participants()
            if not p.vars.get('is_dropout', False)
        ]
        return {0: {'arrived': len(session.arrived_ids), 'out_of': len(expected)}}


class ReadyToStart(Page):
    timeout_seconds = C.START_TIMEOUT
    timer_text = "Time Left to Enroll in the Game: "
    is_displayed = is_displayed_common

    @staticmethod
    def vars_for_template(player: Player):
        pass

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.wait_page_arrival = time.time()
        player.participant.vars['is_dropout'] = timeout_happened
        player.participant.is_dropout = timeout_happened


def custom_export(players):
    yield ['participant_code', 'label', 'current_app', 'current_page',
           'round_number', 'is_dropout', 'finished']
    for player in players:
        p = player.participant
        yield [
            p.code,
            p.label or '',
            p._current_app_name,
            p._current_page_name,
            player.round_number,
            p.vars.get('is_dropout', False),
            getattr(p, 'finished', False),
        ]


page_sequence = [
    Consent,
    NoConsent,
    Instructions,
    HighStakes,
    QuizInstructions,
    Quiz,
    PreSurveyIntro,
    Demographics,
    PreRiskTaking,
    PreSurveyConclusion,
    WaitForPlayers,
    ReadyToStart,
]
