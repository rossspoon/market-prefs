from otree.api import BaseGroup, BasePlayer, BaseSubsession

import common.SessionConfigFunctions as scf

TOOL_TIPS = {
    'stat_stock_pos': dict(
        text="""Numer of share of STOCK that you currently own.  Each share that you own pays out
         a dividend at the end of each round.""",
        pos_cls='tt-right'
    ),
    'stat_cash_pos': dict(
        text="""The amount of CASH that you currently have.  Your CASH earns interest that is paid out at the 
        end of each period.""",
        pos_cls='tt-right'
    ),
    'stat_buy_back': dict(
        text="""After the last market period each share of STOCK that you own will be bought
                   back at this price ({buy_back}). """,
        pos_cls='tt-right'
    ),
    'stat_dividends': dict(
        text="""<p>The dividend paid out on STOCK.</p>
                   <p>Each share of stock that you own will earn either {dividends} points.
                    Each amount is equally likely.</p>""",
        pos_cls='tt-right'
    ),
    'stat_int_rate': dict(
        text="""<p>Interest on CASH earned at the end of the market period.</p>
                """,
        pos_cls='tt-right'
    ),
    'stat_total_short': dict(
        text="""<p>The amount of shares shorted by all traders in the market.</p>{float_ratio_blurb}""",
        pos_cls='tt-right'
    ),
    'stat_stock_float': dict(
        text="""<p>The amount of shares available to trade in the market.</p>""",
        pos_cls='tt-right'
    ),
    'stat_market_price': dict(
        text="""<p>The current market price.   This is market clearing price for the last round of play.</p>""",
        pos_cls='tt-right'
    ),
    'stat_stock_value': dict(
        text="""<p>The value of your STOCK at the current market value</p>""",
        pos_cls='tt-right'
    ),
    'stat_debt': dict(
        text="""<p>The value of shorted STOCK or borrowed CASH.</p>""",
        pos_cls='tt-right'
    ),
    'stat_limit_none': dict(
        text="""<p>You currently have no debt, and so there is no limit.</p>
                <p>If you decide to short the STOCK or borrow CASH you will be subject to a limit.</p>""",
        pos_cls='tt-right'
    ),
    'stat_limit_cash': dict(
        text="""<p>This is the limit of the amount of CASH that you may borrow.
                The limit is based on the amount of CASH that you borrowed and the value of your
                STOCK.</p>
                If the amount of cash that you have borrowed exceeds this limit, then the system to try to 
                sell your stock automatically to reduce your debt""",
        pos_cls='tt-right'
    ),
    'stat_limit_short': dict(
        text="""<p>The limit of the value of shorted STOCK.  The limit is based on the
               amount of CASH that you hold and the value of your STOCK at the current market price.</p>
               <p>If the value of your shorted stock exceeds this limit, then the system to try to 
                buy your stock automatically to reduce your debt</p>""",
        pos_cls='tt-right'
    ),
    'tip_notes': dict(
        text="""<p>Special actions taken with your orders.</p>
                <ul>
                    <li>Short sell orders may be limited if they can cause the market to be
                         shorted beyond the limit.</li>
                    <li>An entire short sell order can be canceled because of a shorting limit</li>
                    <li>An automatic SELL order will cancel your BUY orders</li>
                    <li>An automatic BUY order will cancel your SELL orders</li>
                </ul>""",
        pos_cls="tt-left"
    ),
    'tip_fill': dict(
        text="""<p>The number of shares actually traded for this order.  This depends on
                market conditions.  You can only buy shares if there is someone willing to sell
                and vise versa.</p>""",
        pos_cls="tt-left"
    ),
}


class Globals:
    ALREADY_CONFIGURED = False


# noinspection PyDictCreation
def get_tool_tip_data(obj):
    if Globals.ALREADY_CONFIGURED:
        return TOOL_TIPS

    variables = {}
    variables['dividends'] = " or ".join(str(d) for d in scf.get_dividend_amounts(obj))
    variables['buy_back'] = scf.get_fundamental_value(obj)
    variables['float'] = ensure_group(obj).float
    float_ratio_cap = scf.get_float_ratio_cap(obj)
    float_ratio_blurb = ''
    if float_ratio_cap:
        float_ratio_blurb = """<p>Short sells will be limited to ensure that no more than {float} shares
                        are shorted.</p>""".format(**variables)
    variables['float_ratio_blurb'] = float_ratio_blurb

    # Loop messages in TOOL_TIPS and perform subs
    for key, data in TOOL_TIPS.items():
        TOOL_TIPS[key]['text'] = TOOL_TIPS[key]['text'].format(**variables)

    Globals.ALREADY_CONFIGURED = True
    return TOOL_TIPS


# noinspection PyUnresolvedReferences
def ensure_group(obj):
    if isinstance(obj, BaseGroup):
        return obj
    elif isinstance(obj, BasePlayer):
        return obj.group
    elif isinstance(obj, BaseSubsession):
        return obj.get_groups()[0]
    return None
