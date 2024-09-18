from os import environ

SESSION_CONFIGS = [
    dict(
        name='rounds',
        app_sequence=['consent', 'rounds', 'payment'],
        num_demo_participants=2,
        random_hist=False
    )
    , dict(
        name='rounds_test',
        app_sequence=['rounds'],
        num_demo_participants=3,
        interest_rate=.05,
        div_amount='.4 1.00',
        div_dist='.5 .5',
        margin_ratio=.5,
        margin_premium=0.1,
        margin_target_ratio=.6,
        auto_trans_delay=0,
    )
    , dict(
        name="ctlanding",
        app_sequence=['landingct'],
        num_demo_participants=40,
        consent_link="https://docs.google.com/forms/d/e/1FAIpQLScuxDtP9dEzRk89ru7z2ekLCmG0a5TQKFYgA-cB7EMtunar5w/viewform?embedded=true&usp=pp_url&entry.755475846",
        consent_pg_cnt=4,
        survey_1_link="https://docs.google.com/forms/d/e/1FAIpQLSffLRaG5rYyrSYGaSK8Vzj6b_yllfQ5A8sWPMfvLdEf5xMISA/viewform?embedded=true&usp=pp_url&entry.181925610",
        survey_1_pg_cnt = 7,
        instruction_id = '232inD_HChc', 
        experiment_link = "https://vt-market-experiment.herokuapp.com/room/market2",
        experiment_link_local = 'http://localhost:8000/room/market2',
        experiment_link_is_local=False,
        waiting_group_size=25,
        landing_wait_timeout=1200,
        is_hi_stakes=False,
    )
    
    , dict(
        name='sim_1',
        app_sequence=['rounds'],
        num_demo_participants=3,
    )

    , dict(
        name='consent',
        app_sequence=['consent', 'payment'],
        num_demo_participants=1,
    )

    , dict(
        name='payment',
        app_sequence=['payment'],
        num_demo_participants=1
    )

    , dict(
        participation_fee=0.75,

        name='prescreen',
        app_sequence=['prescreen'],
        num_demo_participants=1,

        slot_01='',
        slot_02='',
        slot_03='',
        slot_04='',
        slot_05='',
        slot_06='',
        slot_07='',
        slot_08='',
        slot_09='',
        slot_10='',
    )

]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.005,
    participation_fee=12.00,
    doc="",
    use_browser_bots=False,
    interest_rate=0.05,
    div_amount='0.40 1.00',
    div_dist='.5 .5',
    margin_ratio=.5,
    margin_premium=0.1,
    margin_target_ratio=.6,
    auto_trans_delay=0,
    float_ratio_cap=1.0,

    endow_stock='4 4 4',
    endow_worth=156.0,

    initial_price=14.0,
    bonus_cap=None,
    forecast_thold=2.5,
    forecast_reward=2.5,
    forecast_range=50,
    forecast_periods='0,2,5,10',
    
    quiz_reward = .25,
    
    market_time=20,
    fixate_time=2,
    forecast_time=30,
    summary_time=10,
    practice_time=15,
    practice_end_time=30,
    final_results_time=75,
    risk_elic_time=5,
    show_next=False,
    is_prolific=False,
    is_mturk=False,

    is_pilot=False,
    expected_time_pilot=1,
    expected_time_live=2,
    arrived_ids=0,
)
if environ.get('MTURK_HIT_TYPE') == 'SCREEN_PILOT':
    SESSION_CONFIG_DEFAULTS['mturk_hit_settings'] = dict(
        keywords='bonus, study',
        title='Pre-Screen Survey for a Market Pilot Experiment',
        description='This is a pre-screening survey to determine participant availability for a forthcoming '
                    'market experiment conducted by the VT Econ Lab at Virginia Tech University.  This research'
                    ' studies how market institutions affect asset prices.',
        frame_height=500,
        template='global/mturk_screen_pilot_template.html',
        minutes_allotted_per_assignment=15,
        expiration_hours=3 * 24,
        qualification_requirements=[]
        # grant_qualification_id='YOUR_QUALIFICATION_ID_HERE', # to prevent retakes
    )
elif environ.get('MTURK_HIT_TYPE') == 'SCREEN':
    SESSION_CONFIG_DEFAULTS['mturk_hit_settings'] = dict(
        keywords='bonus, study',
        title='Pre-Screen Survey for a Market Experiment',
        description='This is a pre-screening survey to determine participant availability for a forthcoming '
                    'market experiment conducted by the VT Econ Lab at Virginia Tech University.  This research'
                    ' studies how market institutions affect asset prices.',
        frame_height=500,
        template='global/mturk_screen_live_template.html',
        minutes_allotted_per_assignment=15,
        expiration_hours=3 * 24,
        qualification_requirements=[]
        # grant_qualification_id='YOUR_QUALIFICATION_ID_HERE', # to prevent retakes
    )
elif environ.get('MTURK_HIT_TYPE') == 'EXP_PILOT':
    SESSION_CONFIG_DEFAULTS['mturk_hit_settings'] = dict(
        keywords='bonus, study',
        title='VT Market Experiment Pilot',
        description='This is a pilot study to test the experiment software.\n '
                    'Participate is a market experiment where you will buy and sell shares of a risky asset '
                    '(STOCK) with other traders in the market.  This research'
                    ' studies how market institutions affect asset prices.\n '
                    'This study will take about 1 hour to complete.',
        frame_height=500,
        template='global/mturk_exp_pilot_template.html',
        minutes_allotted_per_assignment=300,
        expiration_hours=3 * 24,
        qualification_requirements=[]
        # grant_qualification_id='YOUR_QUALIFICATION_ID_HERE', # to prevent retakes
    )
elif environ.get('MTURK_HIT_TYPE') == 'EXP':
    SESSION_CONFIG_DEFAULTS['mturk_hit_settings'] = dict(
        keywords='bonus, study',
        title='VT Market Experiment',
        description='Participate is a market experiment where you will buy and sell shares of a risky asset '
                    '(STOCK) with other traders in the market.  This research'
                    ' studies how market institutions affect asset prices.\n '
                    'This study will take about 2 hours to complete.',
        frame_height=500,
        template='global/mturk_exp_template.html',
        minutes_allotted_per_assignment=300,
        expiration_hours=3 * 24,
        qualification_requirements=[]
        # grant_qualification_id='YOUR_QUALIFICATION_ID_HERE', # to prevent retakes
    )
PARTICIPANT_FIELDS = ['CONSENT', 'CONSENT_BUTTON_CLICKED', 'MARKET_PAYMENT', 'FORECAST_PAYMENT', 'RISK_PAYMENT', 'QUIZ_PAYMENT',  'quiz_grade', 'finished', 'consent', 'inactive', 'wait_page_arrival', 'survey_1_click']
SESSION_FIELDS = ['prolific_completion_url', 'arrived_ids']

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True
POINTS_CUSTOM_NAME = " "
POINTS_DECIMAL_PLACES = 2

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '7763949237284'

ROOMS = [
    dict(
        name='market',
        display_name='Market Experiment',
        participant_label_file='_rooms/market.txt',
        use_secure_urls=False
    ),
    dict(
        name='market2',
        display_name='Market Experiment (w/o participant labels)'
    ),
    dict(
        name='prescreen',
        display_name='Pre-Screen Survey Room'
    ),

    dict(
        name='CTlanding',
        display_name='CT - Landing Page Room'
    ),
]
