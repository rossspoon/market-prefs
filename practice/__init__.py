from otree.api import *

import rounds
from rounds import OrderType
from rounds.data_structs import DataForOrder, DataForPlayer
import common.SessionConfigFunctions as scf

doc = """
Practice Rounds
"""


class C(BaseConstants):
    NAME_IN_URL = 'practice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3


Subsession = rounds.Subsession
Group = rounds.Group
Player = rounds.Player
Order = rounds.Order


def practice_market_page_live_method(player, d):
    return rounds.market_page_live_method(player, d, is_practice=True)


# PAGES
class PracticeMarketPage(Page):
    template_name = 'rounds/Market.html'
    form_model = Player
    form_fields = ['type', 'price', 'quantity']
    get_timeout_seconds = scf.get_market_time

    # method bindings
    js_vars = rounds.get_js_vars_not_current
    vars_for_template = rounds.vars_for_market_template
    live_method = practice_market_page_live_method


class PracticeForecastPage(Page):
    template_name = 'rounds/ForecastPage.html'
    form_model = 'player'

    js_vars = rounds.get_js_vars_not_current
    vars_for_template = rounds.vars_for_forecast_template

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
    vars_for_template = rounds.vars_for_round_results_template

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
