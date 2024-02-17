from otree.api import *
from common.ParticipantFuctions import generate_participant_ids
import time
doc = ''

class C(BaseConstants):
    NAME_IN_URL = 'wait'
    PLAYERS_PER_GROUP = None
    MIN_PLAYERS_PER_GROUP = 3 #should be 25
    NUM_ROUNDS = 1
    WAIT_TIMEOUT = 1200 #20min max for waiting room
    INST_TIMEOUT = 1200 #20min max for instructions 
    SURVEY1_TIMEOUT = 900 #15min max for instructions 
    CONSENT_TIMEOUT = 900 #2min max for consent
    START_TIMEOUT = 120 #2min for start the game
    

class Subsession(BaseSubsession):
    pass

def creating_session(subsession: Subsession):
    session = subsession.session
    #for each group in session, create an empty set
    for player in subsession.get_players():
        player.participant.inactive=False
        player.participant.is_single=0
    session.arrived_ids = set()
    session.enrolled_ids = 0

    
    generate_participant_ids(subsession)
    for p in subsession.get_players():
        p.participant.survey_1_click = False

class Group(BaseGroup):
    pass
    

class Player(BasePlayer):
    timeout = models.FloatField(initial=0.0)
    consent_given = models.BooleanField(blank=True)



def get_exp_link(player: Player):
    config = player.session.config
    is_local = config['experiment_link_is_local']
    if is_local:
        exp_link = config['experiment_link_local']
    else:
        exp_link = config['experiment_link']
        
    return exp_link



class Consent(Page):
     timeout_seconds = C.CONSENT_TIMEOUT
     timer_text = "Time Left to Complete the Consent: "
     form_model = 'player'
     form_fields = ['consent_given']
         
    
     @staticmethod 
     def vars_for_template(player: Player):
         config = player.session.config
         print(config)
         return config
    
     
     @staticmethod
     def js_vars(player: Player):
         config = player.session.config
         consent_pg_cnt = config.get('consent_pg_cnt')
         return dict(
             survey_pg_cnt=consent_pg_cnt
             )
     
     @staticmethod
     def before_next_page(player: Player, timeout_happened):
         if timeout_happened:
             player.consent_given = False
             

             
class NoConsent(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not player.consent_given

             


class Instructions(Page):
    timeout_seconds = C.INST_TIMEOUT
    timer_text = "Time Left to Complete the Instructions: "
    form_model = 'player'
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.participant.inactive = True
            # app_after_this_page = "questionnaires"
        player.participant.inactive = False

    @staticmethod
    def app_after_this_page(player, upcoming_apps):
        if player.participant.inactive == True:
            return upcoming_apps[-1]
        
    @staticmethod
    def js_vars(player: Player):
        config = player.session.config
        inst_id = config.get('instruction_id')
        return dict(inst_id=inst_id, show_next=config['show_next'])
    
    @staticmethod 
    def vars_for_template(player: Player):
        config = player.session.config
        return config
    
    
    
class Survey1(Page):
     timeout_seconds = C.SURVEY1_TIMEOUT
     timer_text = "Time Left to Complete the Survey: "
     form_model = 'player'
         
     @staticmethod
     def vars_for_template(player: Player):
         config = player.session.config
         return config
     
     @staticmethod
     def js_vars(player: Player):
         config = player.session.config
         return config

     
             
class WaitForPlayers(Page):
    @staticmethod
    def live_method(player: Player, data):
        session = player.session
        group = player.group.id_in_subsession
        if data['out']==0:
            session.arrived_ids.add(player.id_in_group)
        elif data['out']==1:
            session.arrived_ids.remove(player.id_in_group)

        return {0: {'arrived': len(session.arrived_ids)}}

    
    
    @staticmethod
    def vars_for_template(player: Player):        
        ret = player.session.config.copy()
        ret['prolific_completion_url'] = player.session.vars.get('prolific_completion_url', 'http://www.vt.edu')
        return ret
        

class Calibration(Page):  
    pass

class ReadyToStart(Page):
    timeout_seconds = C.START_TIMEOUT
    timer_text = "Time Left to Enroll in the Game: "
    
    @staticmethod
    def vars_for_template(player: Player):
        exp_link = get_exp_link(player)
            
        return dict(exp_link = exp_link)
    

    @staticmethod
    def live_method(player: Player, data):
        session = player.session
        if data['enrolled'] == 1:
            player.participant.wait_page_arrival = time.time() #record enroll time
            session.enrolled_ids += 1
        return {0: {'num_enrolled': session.enrolled_ids}}
    

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.wait_page_arrival = time.time()
        # session = player.session
        if timeout_happened:
            # if session.enrolled_ids >= {{C.MIN_PLAYERS_PER_GROUP}}:
            #     app_after_this_page = "questionnaires"
            player.participant.inactive = True

    # @staticmethod
    # def app_after_this_page(player, upcoming_apps):
    #     if player.session.enrolled_ids >= {{C.MIN_PLAYERS_PER_GROUP}}:
    #         return upcoming_apps[-1]

page_sequence = [Consent, NoConsent,  Instructions,  Survey1,  WaitForPlayers, ReadyToStart]