from enum import Enum

from otree.api import *
from otree.common import InvalidRoundError

import common.SessionConfigFunctions as scf


class OrderType(Enum):
    """
        Enumeration representing the order type BID/OFFER
    """
    BID = -1
    OFFER = 1


class OrderField(Enum):
    """
        Enumeration representing fields on the order form
    """
    PRICE = 1
    QUANTITY = 2
    TYPE = 3


class OrderErrorCode(Enum):
    """
        Enumeration representing error codes for order submission
    """

    def __new__(cls, val, field, desc):
        obj = object.__new__(cls)
        obj._value_ = val
        obj.field = field
        obj.desc = desc
        return obj

    PRICE_NEGATIVE = (1, OrderField.PRICE, 'Must be greater than zero')
    PRICE_NOT_NUM = (2, OrderField.PRICE, 'Must be a number')
    QUANT_NEGATIVE = (4, OrderField.QUANTITY, 'Must be greater than zero')
    QUANT_NOT_NUM = (8, OrderField.QUANTITY, 'Must be an integer number')
    BAD_TYPE = (16, OrderField.TYPE, 'Select a type')
    BID_GREATER_THAN_ASK = (32, OrderField.PRICE, 'Buy price must be less than all sell orders')
    ASK_LESS_THAN_BID = (64, OrderField.PRICE, 'Sell price must be greater than all buy orders')
    BORROWING_TOO_MUCH = (128, OrderField.QUANTITY, 'The cost of this order will increase your debt beyond your'
                                                    ' limit. \u000D\u000A '
                                                    'Either lower the price or reduce the number of shares.')
    PRICE_CEIL = (256, OrderField.PRICE, 'The price to less than 10,000.')
    QUANT_CEIL = (512, OrderField.QUANTITY, 'The quantity should be less than 100.')
    PRICE_LEN_RAW = (1024, OrderField.PRICE, 'This input is too long.  Please provide a shorter input.')
    QUANT_LEN_RAW = (2048, OrderField.QUANTITY, 'This input is too long.  Please provide a shorter input.')
    SHORTING =  (4096, OrderField.QUANTITY, 'You are attempting to sell more shares that you have.  Please reduce the quantity.')
    MARGIN =  (8192, OrderField.PRICE, 'The total cost of your combined BUYs exceeds your current amount of CASH. Please reduce either the price or quantity of this order.')

    def combine(self, code):
        if type(code) is OrderErrorCode:
            code = code.value
        return self.value | code

    def to_dict(self):
        return dict(value=self.value,
                    field=self.field.value,
                    desc=self.desc)


class Subsession(BaseSubsession):
    pass


NO_SHORT_LIMIT = -199


class Group(BaseGroup):
    price = models.CurrencyField()
    volume = models.IntegerField()
    dividend = models.CurrencyField(initial=0)

    float = models.IntegerField()
    short = models.IntegerField()

    def in_round_or_none(self, round_number):
        try:
            return self.in_round(round_number)
        except InvalidRoundError:
            return None

    def get_last_period_price(self):
        # Get the market Price of the last period
        round_number = self.round_number
        last_group = self.in_round_or_none(round_number - 1)

        if last_group:
            return last_group.price
        else:
            init_price = scf.get_init_price(self)
            if init_price is not None:
                return init_price
            else:
                return scf.get_fundamental_value(self)

    def get_short_limit(self):
        """
        Determine the number of shorted shares allowed this round.  This is the limit of the
        combined number of shares this round.   All sell order made this round that will be a
        short sale for the player, when combined must be equal to or below this amount.
        @return: int number of shares.
        """
        cap_ratio = scf.get_float_ratio_cap(self)
        if not cap_ratio:
            return NO_SHORT_LIMIT

        max_short_shares = int(cap_ratio * self.float)
        allowable = max_short_shares - self.short
        return max(allowable, 0)

    def determine_float(self):
        total_shares = sum(p.shares for p in self.get_players() if p.did_give_consent())
        self.float = total_shares


NO_AUTO_TRANS = -99

def make_type_select():
    return models.IntegerField(
        choices=[
            [-1, 'Buy'],
            [0, 'Hold'],
            [1, 'Sell'],
        ],
        blank=True
    )

# noinspection DuplicatedCode
class Player(BasePlayer):
    cash = models.CurrencyField()
    shares = models.IntegerField()

    #TODO:  Gravestone these
    periods_until_auto_buy = models.IntegerField(initial=NO_AUTO_TRANS)
    periods_until_auto_sell = models.IntegerField(initial=NO_AUTO_TRANS)

    # Market Movement
    shares_transacted = models.IntegerField(initial=0)
    trans_cost = models.CurrencyField(initial=0)
    cash_after_trade = models.CurrencyField()
    interest_earned = models.CurrencyField()
    dividend_earned = models.CurrencyField()

    # Results
    cash_result = models.CurrencyField()
    shares_result = models.IntegerField()

    # Forecasting Item
    f0 = models.CurrencyField(blank=True)
    forecast_error = models.CurrencyField()
    forecast_reward = models.CurrencyField(initial=0)

    # Risk Elicitation
    risk = models.IntegerField(blank=True)
    risk_1 = models.IntegerField(blank=True)
    risk_2 = models.IntegerField(blank=True)
    risk_3 = models.IntegerField(blank=True)
    risk_4 = models.IntegerField(blank=True)

    # Per-round Survey
    # emotion = models.IntegerField(
    #    label='How do you feel about these results?',
    #    choices=[
    #        [1, '<img src="/static/rounds/img/angry.png" style="width:50px;height:50px;"/>'],
    #        [2, '<img src="/static/rounds/img/annoyed.jpeg" style="width:50px;height:50px;"/>'],
    #        [3, '<img src="/static/rounds/img/meh.jpeg" style="width:50px;height:50px;"/>'],
    #        [4, '<img src="/static/rounds/img/happy.png" style="width:50px;height:50px;"/>'],
    #        [5, '<img src="/static/rounds/img/big_grin.jpeg" style="width:50px;height:50px;"/>']],
    #    widget=widgets.RadioSelectHorizontal
    # )

    def to_dict(self):
        d = {'cash': self.field_maybe_none('cash'),
             'shares': self.field_maybe_none('shares'),
             'periods_until_auto_buy': self.field_maybe_none('periods_until_auto_buy'),
             'periods_until_auto_sell': self.field_maybe_none('periods_until_auto_sell'),
             'shares_transacted': self.field_maybe_none('shares_transacted'),
             'trans_cost': self.field_maybe_none('trans_cost'),
             'cash_after_trade': self.field_maybe_none('cash_after_trade'),
             'interest_earned': self.field_maybe_none('interest_earned'),
             'dividend_earned': self.field_maybe_none('dividend_earned'),
             'cash_result': self.field_maybe_none('cash_result'),
             'shares_result': self.field_maybe_none('shares_result')}
        return d

    def update_from_dict(self, d):
        self.shares_result = d.get('shares_result')
        self.shares_transacted = d.get('shares_transacted')
        self.trans_cost = d.get('trans_cost')
        self.cash_after_trade = d.get('cash_after_trade')
        self.dividend_earned = d.get('dividend_earned')
        self.interest_earned = d.get('interest_earned')
        self.cash_result = d.get('cash_result')
        self.periods_until_auto_buy = d.get('periods_until_auto_buy')
        self.periods_until_auto_sell = d.get('periods_until_auto_sell')

    def is_short(self):
        return self.shares < 0

    def is_debt(self):
        return self.cash < 0

    def is_bankrupt(self, results=False):
        price = self.group.get_last_period_price()
        if results:
            price = self.group.price

        _, equity, _, _, _ = self.get_holding_details(price, results=results)
        return equity <= 0

    def in_round_or_null(self, round_number):
        try:
            return self.in_round(round_number)
        except InvalidRoundError:
            return None

    def get_holding_details(self, market_price, results=False):
        s = self.shares_result if results else self.shares
        c = self.cash_result if results else self.cash
        mr = scf.get_margin_ratio(self)
        mtr = scf.get_margin_target_ratio(self)
        value_of_stock = cu(market_price * s)

        limit = None
        close_lim = None
        if s < 0:  # Shorting
            limit = -1 * cu(c / (1+mr))
            close_lim = -1 * cu(c / (1 + mtr))
        elif c < 0:  # Borrowing
            limit = -1 * cu(value_of_stock / (1+mr))
            close_lim = -1 * cu(value_of_stock / (1 + mtr))

        equity = value_of_stock + c
        debt = cu(min(c, 0) + min(value_of_stock, cu(0)))

        return value_of_stock, equity, debt, limit, close_lim

    def is_short_margin_violation(self):
        if self.is_bankrupt() or not self.is_short():
            return False

        price = self.group.get_last_period_price()
        _, _, debt, limit, _ = self.get_holding_details(price)

        return abs(debt) >= abs(limit)

    def is_debt_margin_violation(self):
        if self.is_bankrupt() or not self.is_debt():
            return False

        price = self.group.get_last_period_price()
        _, _, debt, limit, _ = self.get_holding_details(price)

        return abs(debt) >= abs(limit)

    def copy_results_from_previous_round(self):
        r_num = self.round_number
        past_player = self.in_round_or_null(r_num - 1)
        if past_player:
            self.cash = past_player.cash_result
            self.shares = past_player.shares_result

    def determine_forecast_reward(self, price):
        f0 = self.field_maybe_none('f0')
        if f0 is not None:
            forecast_error = abs(price - self.f0)
            reward = scf.get_forecast_reward(self)
            threshold = scf.get_forecast_thold(self)
            forecast_reward = reward if forecast_error <= threshold else 0
            self.forecast_error = forecast_error
            self.forecast_reward = forecast_reward

    @staticmethod
    def calculate_delay(current_delay, base):
        if current_delay == NO_AUTO_TRANS:
            return base
        return max(current_delay - 1, 0)

    def determine_auto_trans_status(self):
        prev_player = self.in_round_or_null(self.round_number - 1)
        auto_trans_delay = scf.get_auto_trans_delay(self)

        if not prev_player:
            buy_delay = auto_trans_delay
            sell_delay = auto_trans_delay
        else:
            prev_delay = prev_player.field_maybe_none('periods_until_auto_buy')
            buy_delay = self.calculate_delay(prev_delay, auto_trans_delay)
            prev_delay = prev_player.field_maybe_none('periods_until_auto_sell')
            sell_delay = self.calculate_delay(prev_delay, auto_trans_delay)

        short_mv = self.is_short_margin_violation()
        debt_mv = self.is_debt_margin_violation()

        # Skip out for bankrupt players
        if self.is_bankrupt():
            self.periods_until_auto_buy = NO_AUTO_TRANS
            self.periods_until_auto_sell = NO_AUTO_TRANS
            return

        # Short buy-in status / delay
        if short_mv:
            self.periods_until_auto_buy = buy_delay
        else:
            self.periods_until_auto_buy = NO_AUTO_TRANS

        # debt buy-in status / delay
        if debt_mv:
            self.periods_until_auto_sell = sell_delay
        else:
            self.periods_until_auto_sell = NO_AUTO_TRANS

    def is_auto_buy(self):
        return self.periods_until_auto_buy == 0

    def is_auto_sell(self):
        return self.periods_until_auto_sell == 0

    def did_give_consent(self):
        part = self.participant
        consent = part.vars.get('CONSENT')
        return consent

    def __str__(self):
        c = self.field_maybe_none('cash')
        p = self.field_maybe_none('shares')
        return f"Player: {self.id_in_group}; Cash: {c}; Shares: {p}"

    def __repr__(self):
        return self.__str__()


class Order(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)
    # uuid = models.StringField()
    order_type = models.IntegerField()
    price = models.CurrencyField()
    quantity = models.IntegerField()
    quantity_final = models.IntegerField(initial=0)
    original_quantity = models.IntegerField()
    is_buy_in = models.BooleanField(initial=False)  # is this order an automatic buy-in?

    def to_dict(self):
        requested_quant = self.original_quantity if self.original_quantity else self.quantity
        return dict(
            oid=self.id,
            p_id=self.player.id_in_group,
            group_id=self.group.id,
            type=self.order_type,
            price=self.price,
            quantity=self.quantity,
            original_quantity=self.original_quantity,
            quantity_final=self.quantity_final,
            requested_quant=requested_quant,
            is_buy_in=self.is_buy_in
        )

    def __str__(self):
        t = "BUY" if self.order_type == -1 else "SELL"
        a = "(AUTO)" if self.is_buy_in else ""
        return f"{t} {self.quantity} @ {self.price} {a}"

    def __repr__(self):
        return self.__str__()
