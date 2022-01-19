from otree.models import Session

from bots.scripted_bot import ScriptedBot
from bots.sim_bot import SimulationBot
from otree.bots import Bot


class PlayerBot(Bot):

    def __new__(cls, *args, **kwargs):
        session = Session.objects_get(id=kwargs.get('session_pk'))
        s_name = session.config.get('name')
        if s_name == 'rounds_test':
            return ScriptedBot(**kwargs)

        elif s_name == 'sim_1':
            return SimulationBot(**kwargs)