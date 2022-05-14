from otree.api import *
from datetime import datetime, timedelta

from otree.templating.filters import register

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
        et = self.dt() + timedelta(hours=2)
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


def get_vars_for_confirm_page(player):
    slots = TimeSlot.filter(player=player)
    return {'slots': slots}


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


@register
def te(key):
    """ Take a form fields in the template and use the name of the field to look up the date and return
    a formatted end time that is 2 hours after the time"""
    dt = TIME_SLOTS[key.name] + timedelta(hours=2)
    return datetime.strftime(dt, '%I:%M %p')


def custom_export(players):
    """ Custom export for prescreen app """
    for p in players:
        for ts in TimeSlot.filter(player=p):
            yield [p.participant.label, ts.date]


# PAGES
class Introduction(Page):
    pass


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
