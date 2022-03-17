import rounds
from common.ParticipantFuctions import generate_participant_ids
from practice.models import *
from rounds import OrderType
from rounds.data_structs import DataForOrder, DataForPlayer

doc = """
Practice Rounds
"""


class C(BaseConstants):
    NAME_IN_URL = 'practice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3


prices = [-1, 3000, 2500, 1400]
volumes = [-1, 12, 18, 8]
dividends = [-1, 40, 100, 40]


def creating_session(subsession):
    round_number = subsession.round_number

    # Stuff for all rounds
    for g in subsession.get_groups():
        g.float = 10
        g.short = 5
        g.price = prices[round_number]
        g.volume = volumes[round_number]
        g.dividend = dividends[round_number]

    # only set up endowments in the first round
    if round_number != 1:
        return

    generate_participant_ids(subsession)
    for p in subsession.get_players():
        p.cash = 10000
        p.shares = 2


def practice_round_results_vars(player: Player):
    ret = rounds.vars_for_round_results_template(player)
    filled_amount = ret.get('filled_amount')
    orders = rounds.get_orders_for_player(player, o_cls=Order)

    # All transaction types should be the same for a given player
    trans_type = 0
    if filled_amount > 0:
        # get the order type
        o_types = list(set(o.order_type for o in orders if o.quantity_final > 0))

        if len(o_types) != 1:
            trans_type = 0
        else:
            trans_type = o_types[0]

    ret['trans_type'] = trans_type
    return ret


def f0_choices(player: Player):
    return rounds.get_forecasters_choices(player, 'f0')


def f1_choices(player: Player):
    return rounds.get_forecasters_choices(player, 'f1')


def f2_choices(player: Player):
    return rounds.get_forecasters_choices(player, 'f2')


def practice_market_page_live_method(player, d):
    return rounds.market_page_live_method(player, d, o_cls=Order)


# PAGES
class PracticeMarketPage(Page):
    template_name = 'rounds/Market.html'
    form_model = Player
    form_fields = ['type', 'price', 'quantity']
    get_timeout_seconds = scf.get_market_time

    # method bindings
    js_vars = rounds.get_js_vars_not_current
    live_method = practice_market_page_live_method

    @staticmethod
    def vars_for_template(player: Player):
        ret = rounds.vars_for_market_template(player)
        ret['is_practice'] = True
        return ret


class PracticeForecastPage(Page):
    template_name = 'rounds/ForecastPage.html'
    form_model = 'player'
    get_timeout_seconds = scf.get_forecast_time
    js_vars = rounds.get_js_vars_not_current

    @staticmethod
    def vars_for_template(player: Player):
        return rounds.vars_for_forecast_template(player, num_rounds=C.NUM_ROUNDS)

    @staticmethod
    def get_form_fields(player):
        round_number = player.round_number
        if round_number == C.NUM_ROUNDS:
            return ['f0']
        elif round_number == C.NUM_ROUNDS - 1:
            return ['f0', 'f1']
        else:
            return ['f0', 'f1', 'f2']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        g = player.group  # price, volume, and dividend are already set on the group

        orders = [DataForOrder(o) for o in Order.filter(player=player)]
        # "fill" orders
        for o in orders:
            if o.order_type == OrderType.BID.value and o.price >= g.price:
                o.quantity_final = min(4, o.quantity)
            elif o.order_type == OrderType.OFFER.value and o.price <= g.price:
                o.quantity_final = min(2, o.quantity)

        d4p = DataForPlayer(player)
        d4p.get_new_player_position(orders, g.dividend, 0.05, g.price)
        d4p.update_player()
        for o in orders:
            o.update_order()

        player.determine_forecast_reward(g.price)


class PracticeRoundResultsPage(Page):
    template_name = 'rounds/RoundResultsPage.html'
    form_model = 'player'
    js_vars = rounds.get_js_vars
    get_timeout_seconds = scf.get_summary_time

    vars_for_template = practice_round_results_vars

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        next_player = player.in_round_or_null(player.round_number + 1)
        if next_player:
            next_player.shares = player.shares_result
            next_player.cash = player.cash_result


class PracticeEndPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [PracticeMarketPage, PracticeForecastPage, PracticeRoundResultsPage, PracticeEndPage]
