from otree.models import Session
import numpy as np

SK_INTEREST_RATE = 'interest_rate'
SK_DIV_AMOUNT = 'div_amount'
SK_DIV_DIST = 'div_dist'
SK_MARGIN_RATIO = 'margin_ratio'
SK_MARGIN_PREMIUM = 'margin_premium'
SK_MARGIN_TARGET_RATIO = 'margin_target_ratio'
SK_FRACTION_OF_SHORT_STARTS = 'fraction_of_short_starts'
SK_CASH_ENDOWMENT_CONTROL = 'cash_endowment_control'
SK_SHARES_ENDOWMENT_CONTROL = 'shares_endowment_control'
SK_CASH_ENDOWMENT_TREATMENT = 'cash_endowment_treatment'
SK_SHARES_ENDOWMENT_TREATMENT = 'shares_endowment_treatment'
SK_INITIAL_PRICE = 'initial_price'
SK_SESSION_NAME = 'name'
SK_RANDOMIZE_HISTORY = 'random_hist'

WHOLE_NUMBER_PERCENT = "{:.0%}"


def ensure_config(obj):
    if type(obj) == dict:
        return obj
    elif type(obj) == Session:
        return obj.config
    else:
        return obj.session.config


def get_item_as_int(config, key):
    raw_value = config.get(key)
    if raw_value:
        return int(raw_value)
    else:
        return 0


def get_item_as_float(config, key):
    raw_value = config.get(key)
    if raw_value:
        return float(raw_value)
    else:
        return 0


def get_item_as_bool(config, key):
    raw_value = config.get(key)
    if raw_value:
        return bool(raw_value)
    else:
        return False


def get_fundamental_value(obj):
    config = ensure_config(obj)

    dist = np.array([float(x) for x in config[SK_DIV_DIST].split()])
    div_amounts = np.array([int(x) for x in config[SK_DIV_AMOUNT].split()])
    exp = dist.dot(div_amounts)
    r = config[SK_INTEREST_RATE]

    if r == 0:
        return 0

    return int(exp / r)


def get_init_price(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_INITIAL_PRICE)


def get_session_name(obj):
    config = ensure_config(obj)
    return config.get(SK_SESSION_NAME)


def as_wnp(x):
    return WHOLE_NUMBER_PERCENT.format(x)


def get_margin_ratio(obj, wnp=False):
    config = ensure_config(obj)
    if wnp:
        return as_wnp(config.get(SK_MARGIN_RATIO))
    else:
        return get_item_as_float(config, SK_MARGIN_RATIO)


def get_margin_target_ratio(obj, wnp=False):
    config = ensure_config(obj)
    if wnp:
        return as_wnp(config.get(SK_MARGIN_TARGET_RATIO))
    else:
        return get_item_as_float(config, SK_MARGIN_TARGET_RATIO)


def get_margin_premium(obj, wnp=False):
    config = ensure_config(obj)
    if wnp:
        return as_wnp(config.get(SK_MARGIN_PREMIUM))
    else:
        return get_item_as_float(config, SK_MARGIN_PREMIUM)


def get_dividend_dist(obj):
    config = ensure_config(obj)
    return config.get(SK_DIV_DIST)


def get_dividend_probabilities(obj):
    return np.array([float(x) for x in get_dividend_dist(obj).split()])


def get_dividend_amount(obj):
    config = ensure_config(obj)
    return config.get(SK_DIV_AMOUNT)


def get_dividend_amounts(obj):
    return np.array([int(x) for x in get_dividend_amount(obj).split()])


def get_interest_rate(obj):
    config = ensure_config(obj)
    return get_item_as_float(config, SK_INTEREST_RATE)


def get_fundamental_value(obj):
    config = ensure_config(obj)

    dist = get_dividend_probabilities(config)
    div_amounts = get_dividend_amounts(config)
    exp = dist.dot(div_amounts)
    r = get_interest_rate(config)

    if r == 0:
        return 0

    return int(exp / r)


def is_random_hist(obj):
    config = ensure_config(obj)
    return get_item_as_bool(config, SK_RANDOMIZE_HISTORY)
