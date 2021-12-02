from os import environ

SESSION_CONFIGS = [
     dict(
        name='rounds',
        app_sequence=['rounds'],
        num_demo_participants=2,
        interest_rate = 0.05,
        div_amount ='40 100',
        div_dist = '.5 .5',
        margin_ratio = .5,
        margin_premium = 0.1,
        margin_target_ratio = .3,

        fraction_of_short_starts = .5,
        cash_endowment_control = 5000,
        shares_endowment_control = 12,
        cash_endowment_treatment = 10000,
        shares_endowment_treatment = -2
        )
     , dict(
        name='rounds_test',
        app_sequence=['rounds'],
        num_demo_participants=3,
        interest_rate = 0,
        div_amount ='0 0',
        div_dist = '.5 .5',
        margin_ratio = .5,
        margin_premium = 0.1,
        margin_target_ratio = .3,

        treated_ids= '1 0 0',
        cash_endowment_control = 500,
        shares_endowment_control = 10,
        cash_endowment_treatment = 1000,
        shares_endowment_treatment = -10,
        )
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=10000.00, participation_fee=0.00, doc=""
    , use_browser_bots=False
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '7763949237284'
