from otree.api import *
from datetime import datetime, timedelta

from otree.templating.filters import register
import common.SessionConfigFunctions as scf

doc = """
Pre-screen app for scheduling participants for the on-line version.
"""


class C(BaseConstants):
    NAME_IN_URL = 'prescreen'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    slot_01 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_02 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_03 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_04 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_05 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_06 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_07 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_08 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_09 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')
    slot_10 = models.BooleanField(widget=widgets.CheckboxInput, blank=True, label='')


class TimeSlot(ExtraModel):
    player = models.Link(Player)
    date = models.StringField()

    def dt(self):
        return datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')

    def to_date(self):
        return datetime.strftime(self.dt(), '%A %B %d, %Y')

    def to_time(self):
        return datetime.strftime(self.dt(), '%I:%M %p')

    def to_end_time(self):
        delta = scf.get_expected_time(self.player)
        et = self.dt() + timedelta(hours=delta)
        return datetime.strftime(et, '%I:%M %p')


def get_form_fields_for_schedule(player):
    config = player.session.config
    slots = []
    for i in range(11):
        field_name = f"slot_{i:02}"
        if config.get(field_name):
            slots.append(field_name)

    return slots


def get_date_times(player):
    fields = get_form_fields_for_schedule(player)
    config = player.session.config
    ret = {}
    for field in fields:
        dt_str = config.get(field)
        dt = datetime.strptime(dt_str, '%Y%m%d%H%M')
        ret[field] = dt
    return ret


TIME_SLOTS = {}


def creating_session(subsession):
    TIME_SLOTS.update(get_date_times(subsession))


def get_vars_for_temp_schedule(player):
    if len(TIME_SLOTS) == 0:
        creating_session(player)

    exp_t = scf.get_expected_time(player)
    is_prolific = scf.is_prolific(player)
    is_mturk = scf.is_mturk(player)
    return {'exp_t': exp_t,
            'is_prolific': is_prolific,
            'is_mturk': is_mturk}


def get_vars_for_confirm_page(player):
    ret = scf.ensure_config(player)
    ret['slots'] = TimeSlot.filter(player=player)
    ret['prolific_completion_url'] = player.session.vars.get('prolific_completion_url', 'http://www.vt.edu')
    return ret


@register
def d(key):
    """ Take a form fields in the template and use the name of the field to look up the date and return
    a formatted string"""
    dt = TIME_SLOTS[key.name]
    return datetime.strftime(dt, '%A %B %d, %Y')


@register
def t(key):
    """ Take a form fields in the template and use the name of the field to look up the date and return
    a formatted time"""
    dt = TIME_SLOTS[key.name]
    return datetime.strftime(dt, '%I:%M %p')


def te(key, delta):
    """ Take a form fields in the template and use the name of the field to look up the date and return
    a formatted end time that is the given number hours after the time"""
    dt = TIME_SLOTS[key.name] + timedelta(hours=delta)
    return datetime.strftime(dt, '%I:%M %p')


@register
def te1(key):
    return te(key, 1)


@register
def te2(key):
    return te(key, 2)


def custom_export(players):
    """ Custom export for prescreen app """
    yield ['session', 'participant', 'timeslot', 'finished']

    for p in players:
        finished = p.participant.vars.get('finished')
        for ts in TimeSlot.filter(player=p):
            yield [p.session.code, p.participant.label, ts.date, finished]


def vars_for_admin_report(subsession):
    slots = get_date_times(subsession)
    comp_url = subsession.session.vars.get('prolific_completion_url', 'none')
    return {'slots': slots.values(),
            'comp_url': comp_url}


# PAGES
class Introduction(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return scf.ensure_config(player)


class Schedule(Page):
    form_model = 'player'
    get_form_fields = get_form_fields_for_schedule
    vars_for_template = get_vars_for_temp_schedule

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        for field, dt in get_date_times(player).items():
            selected = player.field_maybe_none(field)
            if selected:
                TimeSlot.create(player=player, date=dt)

        player.participant.finished = True


class Confirm(Page):
    vars_for_template = get_vars_for_confirm_page


page_sequence = [Introduction, Schedule, Confirm]
