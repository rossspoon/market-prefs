from otree.api import *
from enum import Enum


class OrderType(Enum):
    """
        Enumeration representing the order type BID/OFFER
    """
    BID = -1
    OFFER = 1


class OrderField(Enum):
    """
        Enumeration resprenting fields on the order form
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

    PRICE_NEGATIVE = (1, OrderField.PRICE, 'Price must be greater than zero')
    PRICE_NOT_NUM = (2, OrderField.PRICE, 'Price must be an integer number')
    QUANT_NEGATIVE = (4, OrderField.QUANTITY, 'Quantity must be greater than zero')
    QUANT_NOT_NUM = (8, OrderField.QUANTITY, 'Quantity must be an integer number')
    BAD_TYPE = (16, OrderField.TYPE, 'Select a type')

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


class Group(BaseGroup):
    price = models.CurrencyField()
    volume = models.IntegerField()
    dividend = models.IntegerField(initial=0)

    float = models.IntegerField()
    short = models.IntegerField()


class Player(BasePlayer):
    cash = models.CurrencyField(initial=1000)
    shares = models.IntegerField(initial=50)

    #  These items just exist to drive the form on the page.
    # The actual price and quantity are stored in the Order model
    type = models.IntegerField(
        choices=[
            [-1, 'Buy'],
            [1, 'Sell'],
        ]
        , blank=True
    )
    price = models.IntegerField(blank=True)
    quantity = models.IntegerField(blank=True)

    margin_violation = models.BooleanField(initial=False)  # Margin Warning this round?

    # Market Movement
    shares_transacted = models.IntegerField(initial=0)
    trans_cost = models.IntegerField(initial=0)
    cash_after_trade = models.IntegerField()
    interest_earned = models.IntegerField()
    dividend_earned = models.IntegerField()

    # Results
    cash_result = models.IntegerField()
    shares_result = models.IntegerField()

    # Per-round Survey
    emotion = models.IntegerField(
        label='How do you feel about these results?'
        , choices=[
            [1, '<img src="/static/rounds/img/angry.png" style="width:50px;height:50px;"/>'],
            [2, '<img src="/static/rounds/img/annoyed.jpeg" style="width:50px;height:50px;"/>'],
            [3, '<img src="/static/rounds/img/meh.jpeg" style="width:50px;height:50px;"/>'],
            [4, '<img src="/static/rounds/img/happy.png" style="width:50px;height:50px;"/>'],
            [5, '<img src="/static/rounds/img/big_grin.jpeg" style="width:50px;height:50px;"/>']]
        , widget=widgets.RadioSelectHorizontal
    )

    def to_dict(this):
        d = {}
        d['cash'] = this.field_maybe_none('cash')
        d['shares'] = this.field_maybe_none('shares')
        d['margin_violation'] = this.field_maybe_none('margin_violation')
        d['shares_transacted'] = this.field_maybe_none('shares_transacted')
        d['trans_cost'] = this.field_maybe_none('trans_cost')
        d['cash_after_trade'] = this.field_maybe_none('cash_after_trade')
        d['interest_earned'] = this.field_maybe_none('interest_earned')
        d['dividend_earned'] = this.field_maybe_none('dividend_earned')
        d['cash_result'] = this.field_maybe_none('cash_result')
        d['shares_result'] = this.field_maybe_none('shares_result')
        return d

    def update_from_dict(this, d):
        this.shares_result = d.get('shares_result')
        this.shares_transacted = d.get('shares_transacted')
        this.trans_cost = d.get('trans_cost')
        this.cash_after_trade = d.get('cash_after_trade')
        this.dividend_earned = d.get('dividend_earned')
        this.interest_earned = d.get('interest_earned')
        this.cash_result = d.get('cash_result')
        this.margin_violation = d.get('margin_violation')


class Order(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)
    # uuid = models.StringField()
    order_type = models.IntegerField()
    price = models.CurrencyField()
    quantity = models.IntegerField()
    quantity_final = models.IntegerField(initial=0)
    is_buy_in = models.BooleanField(initial=False)  # is this order an automatic buy-in?

    def to_dict(self):
        return dict(
            oid=self.id
            , p_id=self.player.id_in_group
            , group_id=self.group.id
            , type=self.order_type
            , price=self.price
            , quantity=self.quantity)
