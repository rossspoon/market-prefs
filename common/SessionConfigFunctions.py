from otree.api import Currency as cu
from otree.models import Session
import numpy as np

SK_INTEREST_RATE = 'interest_rate'
SK_DIV_AMOUNT = 'div_amount'
SK_DIV_DIST = 'div_dist'
SK_MARGIN_RATIO = 'margin_ratio'
SK_MARGIN_PREMIUM = 'margin_premium'
SK_MARGIN_TARGET_RATIO = 'margin_target_ratio'
SK_INITIAL_PRICE = 'initial_price'
SK_SESSION_NAME = 'name'
SK_RANDOMIZE_HISTORY = 'random_hist'
SK_BONUS_CAP = 'bonus_cap'
SK_AUTO_TRANS_DELAY = 'auto_trans_delay'
SK_FLOAT_RATIO_CAP = 'float_ratio_cap'
SK_FORECAST_THOLD = 'forecast_thold'
SK_FORECAST_REWARD = 'forecast_reward'
SK_MARKET_TIME = 'market_time'
SK_FORECAST_TIME = 'forecast_time'
SK_SUMMARY_TIME = 'summary_time'
SK_ENDOW_STOCK = 'endow_stock'
SK_ENDOW_WORTH = 'endow_worth'
SK_SHOW_NEXT = 'show_next'
SK_CONVERSION_RATE = 'real_world_currency_per_point'
SK_IS_ONLINE = 'is_online'

WHOLE_NUMBER_PERCENT = "{:.0%}"


def ensure_config(obj):
    if type(obj) == dict:
        return obj
    elif type(obj) == Session:
        return obj.config
    else:
        return obj.session.config


def get_item_as_int(config, key, default=0, return_none=False):
    raw_value = config.get(key)
    if raw_value:
        return int(raw_value)
    elif raw_value is None and return_none:
        return None
    else:
        return default


def get_item_as_float(config, key, default=0.0, return_none=False):
    raw_value = config.get(key)
    if raw_value:
        return float(raw_value)
    elif raw_value is None and return_none:
        return None
    else:
        return default


def get_item_as_currency(config, key, default=0):
    raw_value = config.get(key)
    if raw_value:
        return cu(raw_value)
    else:
        return cu(default)


def get_item_as_bool(config, key, default=False):
    raw_value = config.get(key)
    if raw_value:
        return bool(raw_value)
    else:
        return default


def get_init_price(obj):
    config = ensure_config(obj)
    return get_item_as_float(config, SK_INITIAL_PRICE, return_none=True)


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
    return np.array([float(x) for x in get_dividend_amount(obj).split()])


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

    return cu(exp / r)


def is_random_hist(obj):
    config = ensure_config(obj)
    return get_item_as_bool(config, SK_RANDOMIZE_HISTORY)


def get_bonus_cap(obj):
    config = ensure_config(obj)
    return get_item_as_currency(config, SK_BONUS_CAP, default=9999999999)


def get_auto_trans_delay(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_AUTO_TRANS_DELAY)


def get_float_ratio_cap(obj):
    """
    Return the short cap ratio if set, otherwise None.
    @param obj:
    @return: the short cap ratio if set, otherwise None.
    """
    config = ensure_config(obj)
    return get_item_as_float(config, SK_FLOAT_RATIO_CAP, return_none=True)


def get_forecast_thold(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_FORECAST_THOLD)


def get_forecast_reward(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_FORECAST_REWARD)


def get_market_time(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_MARKET_TIME, return_none=True)


def get_forecast_time(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_FORECAST_TIME, return_none=True)


def get_summary_time(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_SUMMARY_TIME, return_none=True)


def get_endow_stock(obj):
    config = ensure_config(obj)
    return config.get(SK_ENDOW_STOCK)


def get_endow_stocks(obj):
    return [int(x) for x in get_endow_stock(obj).split()]


def get_endow_worth(obj):
    config = ensure_config(obj)
    return get_item_as_int(config, SK_ENDOW_WORTH)


def show_next_button(obj):
    config = ensure_config(obj)
    return get_item_as_bool(config, SK_SHOW_NEXT)


def get_conversion_rate(obj):
    config = ensure_config(obj)
    return get_item_as_float(config, SK_CONVERSION_RATE)


def is_online(obj):
    config = ensure_config(obj)
    return get_item_as_bool(config, SK_IS_ONLINE)
