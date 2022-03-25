from os import environ

SESSION_CONFIGS = [
    dict(
        name='rounds',
        app_sequence=['rounds'],
        num_demo_participants=2,
        random_hist=False
    )
    , dict(
        name='rounds_sell_off',
        app_sequence=['rounds'],
        num_demo_participants=2,
        random_hist=False,
    )
    , dict(
        name='rounds_test',
        app_sequence=['rounds'],
        num_demo_participants=3,
        interest_rate=0,
        div_amount='0 0',
        div_dist='.5 .5',
        margin_ratio=.5,
        margin_premium=0.1,
        margin_target_ratio=.6,
        auto_trans_delay=0,
    )
    , dict(
        name='sim_1',
        app_sequence=['rounds'],
        num_demo_participants=3,
    )
    , dict(
        name='instructions',
        app_sequence=['instructions'],
        num_demo_participants=1,

        _08_example_cash=60.00,
        _08_example_short=2
    )
    , dict(
        name='consent',
        app_sequence=['consent', 'payment'],
        num_demo_participants=1,
    )
    , dict(
        name='survey',
        app_sequence=['survey'],
        num_demo_participants=1,
    )
    , dict(
        name='payment',
        app_sequence=['payment'],
        num_demo_participants=1
    )
    , dict(
        name='practice',
        app_sequence=['practice'],
        num_demo_participants=1,
    )
    , dict(
        name='whole_experiment',
        app_sequence=['consent', 'instructions', 'practice', 'rounds', 'survey', 'payment'],
        num_demo_participants=2,
    )
    , dict(
        name='with_practice',
        app_sequence=['practice', 'rounds', 'survey', 'payment'],
        num_demo_participants=2,
    )
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.01,
    participation_fee=10.00,
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

    endow_stock='18 -2 10 -6',
    endow_worth=300.0,

    initial_price=14.0,
    bonus_cap=50,
    forecast_thold=2.5,
    forecast_reward=5,
    market_time=4500,
    forecast_time=15,
    summary_time=15,
)

PARTICIPANT_FIELDS = ['PART_ID', 'CONSENT', 'CONSENT_BUTTON_CLICKED']
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True
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
        use_secure_urls=True
    ),
    dict(
        name='market2',
        display_name='Market Experiment (w/o participant labels)'
    )
]
