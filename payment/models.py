from base64 import b64encode
from datetime import datetime

from jinja2 import Template
from otree.api import (
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer, cu,
)
from pdflatex import pdflatex

import common.SessionConfigFunctions as scf
import rounds
from common.ParticipantFuctions import generate_participant_ids, is_button_click

doc = """
This application handles the final pay off
"""

KEEP = False


def set_payoffs(subsession):
    for player in subsession.get_players():
        payoff = max(min(player.payoff, scf.get_bonus_cap(subsession)), 0)
        player.payoff = payoff


class Constants(BaseConstants):
    name_in_url = 'payment'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    @staticmethod
    def creating_session(subsession: BaseSubsession):
        generate_participant_ids(subsession)
        set_payoffs(subsession)

    @staticmethod
    def vars_for_admin_report(subsession: BaseSubsession):
        clickers = list(filter(lambda x: is_button_click(x), subsession.get_players()))
        player_data = [to_variable_dict(p) for p in clickers]
        total = sum(d['total'] for d in player_data)
        if len(clickers) > 0:
            average = total / len(clickers)
        else:
            average = 'N/A'

        ## Generate PDF data
        now = datetime.now()
        date_str = now.strftime('%A  %m/%d/%Y')

        # Read in the receipt template
        with open('payment/receipt_temp.tex', 'r') as f:
            template_str = f.read()

        # Render the latex with the player data
        t = Template(template_str)
        tex = t.render(data=player_data, date=date_str)

        # Compile the latex into a PDF
        try:
            pdfl = pdflatex.PDFLaTeX.from_binarystring(tex.encode(), 'pdfs')
            pdf, log, cp = pdfl.create_pdf(keep_pdf_file=KEEP, keep_log_file=False)
            show_pdf = cp.returncode == 0
            pdf = b64encode(pdf).decode('UTF-8')
        except FileNotFoundError as e:
            print(e)
            show_pdf = False
            pdf = ""

        return {'players': player_data, 'total': total, 'average': average, 'show_pdf': show_pdf, 'pdf': pdf}


def to_variable_dict(player: BasePlayer):
    part = player.participant
    session = player.session

    return dict(label=part.label,
                consent=part.vars.get('CONSENT'),
                show_up=session.participation_fee,
                bonus=part.payoff.to_real_world_currency(session),
                total=part.payoff_plus_participation_fee()
                )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


def custom_export(players):
    yield (['session', 'participant', 'part_label', 'clicked_button', 'round_number', 'final_cash', 'bonus',
            'show-up', 'cash_plus_show', 'bonus_plus_show'])

    for p in players:
        participant = p.participant
        session = p.session
        round_players = list(rounds.Player.objects_filter(participant=participant).order_by('round_number'))
        if not round_players or len(round_players) == 0:
            continue

        last_player: rounds.Player = round_players[-1]
        cash_result = last_player.field_maybe_none('cash_result')
        cash_result = cash_result if cash_result is not None else 0
        cash_result = cu(max(0, cash_result))
        cash = cu(cash_result).to_real_world_currency(session)
        bonus = participant.payoff.to_real_world_currency(session)
        show_up = cu(session.config['participation_fee'])
        clicked = is_button_click(p)
        yield(session.code, participant.code, participant.label, clicked, last_player.round_number,
              cash, bonus, show_up, cash + show_up, bonus + show_up)