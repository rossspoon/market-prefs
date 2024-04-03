from otree.api import *
from common.ParticipantFuctions import generate_participant_ids
import time
from datetime import date
doc = ''

class C(BaseConstants):
    NAME_IN_URL = 'wait'
    PLAYERS_PER_GROUP = None
    MIN_PLAYERS_PER_GROUP = 3 #should be 25
    NUM_ROUNDS = 1
    WAIT_TIMEOUT = 1200 #20min max for waiting room
    INST_TIMEOUT = 720 #12min max for instructions 
    SURVEY1_TIMEOUT = 900 #15min max for instructions 
    CONSENT_TIMEOUT = 900 #2min max for consent
    START_TIMEOUT = 120 #2min for start the game
    QUIZ_TIMEOUT = 600
    

class Subsession(BaseSubsession):
    pass

def creating_session(subsession: Subsession):
    session = subsession.session
    
    #Set the date as the label
    today = date.today().strftime("%Y-%m-%d")
    session.label=today
    session.comment = "Landing Page"
    
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
    
    quiz_1 = models.StringField(blank=True,
                label="During order entry you want to input a BUY order at price of 8.52 and a SELL order at a price of 7.89. What will happen to your orders for that period?",
                choices=[["1", "They'll be entered as usual"],
                         ["2", "The SELL order will not go through"]]
                )
    quiz_2 = models.StringField(blank=True,
                label="During order entry the highest price at which you submit a BUY order is 16.78 and the lowest price at which others SELL is 16.22. The market price is 16.56 for that period. You will:",
                choices=[["1", "BUY one unit at 16.78"],
                         ["2", "BUY one unit at 16.56"],
                         ["3", "SELL one unit at 16.56"],
                         ["4", "SELL one unit at 17.22"],
                         ["5", "Not Trade"],
                    ]
                )
    quiz_3 = models.StringField(blank=True,
                label="You have 200 units of CASH at the start of a trading period and no STOCK. You do not trade that period. How much CASH do you have at the beginning of the next period?",
                choices=["200", "210", "205", "190"]
                )

    quiz_4 = models.StringField(blank=True,
                label = "Your account has 5 STOCK and 100 CASH at the start of a trading period, and you do not BUY or SELL during that period. The dividend for that round is 1.00. How much CASH do you have at the start of the next round?",
                choices = ["105", "110", "100", "114"]
                )
    
    quiz_5 = models.StringField(blank=True,
                 label = "After the final trading period, you have 4 remaining units of STOCK. The market price in the final period is 29. How many units of experiment CASH do you receive in exchange for your STOCK?",
                 choices=["4", "29", "56", "116"]
                )
    
    quiz_1_init = models.StringField(blank=True)
    quiz_2_init = models.StringField(blank=True)
    quiz_3_init = models.StringField(blank=True)
    quiz_4_init = models.StringField(blank=True)
    quiz_5_init = models.StringField(blank=True)
    


def get_exp_link(player: Player):
    config = player.session.config
    is_local = config['experiment_link_is_local']
    if is_local:
        exp_link = config['experiment_link_local']
    else:
        exp_link = config['experiment_link']
        
    return exp_link


def template_vars_commom(player: Player):        
    ret = player.session.config.copy()
    ret['prolific_completion_url'] = player.session.vars.get('prolific_completion_url', 'http://www.prolific.com')
    return ret



class Consent(Page):
     timeout_seconds = C.CONSENT_TIMEOUT
     timer_text = "Time Left to Complete the Consent: "
     form_model = 'player'
     form_fields = ['consent_given']
         
    
     @staticmethod 
     def vars_for_template(player: Player):
         config = player.session.config
         return config
    
     
     @staticmethod
     def js_vars(player: Player):
         config = player.session.config
         consent_pg_cnt = config.get('consent_pg_cnt')
         return dict(
             consent_pg_cnt=consent_pg_cnt
             )
     
     @staticmethod
     def before_next_page(player: Player, timeout_happened):
         if timeout_happened:
             player.consent_given = False
             

             
class NoConsent(Page):
    vars_for_template = template_vars_commom
        

def is_displayed_common(player: Player):
    return player.consent_given


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
    
    is_displayed = is_displayed_common
    

def quiz_grade_vars(player: Player, data:dict):
        ## Grade the quiz
        q1_score = 1 if data.get('quiz_1') == '2' else 0
        q2_score = 1 if data.get('quiz_2') == '2' else 0
        q3_score = 1 if data.get('quiz_3') == '210' else 0
        q4_score = 1 if data.get('quiz_4') == '110' else 0
        q5_score = 1 if data.get('quiz_5') == '56' else 0
        total_score = q1_score + q2_score + q3_score + q4_score + q5_score
        
        return {
                    1: q1_score,
                    2: q2_score,
                    3: q3_score,
                    4: q4_score,
                    5: q5_score,
                    'total_score': total_score,
                    }   

    
def quiz_live_method(player, data):
    func = data['func']
    

  
    ###
    ##
    ## Gade the quiz
    ##
    ###
    if func == 'grade_it':
    
        
        form_data = data['data']
        
        # record initial responses
        q1_i = player.field_maybe_none('quiz_1_init')
        q2_i = player.field_maybe_none('quiz_2_init')
        q3_i = player.field_maybe_none('quiz_3_init')
        q4_i = player.field_maybe_none('quiz_4_init')
        q5_i = player.field_maybe_none('quiz_5_init')
        
        if not q1_i and not q2_i and not q3_i and not q4_i and not q5_i:
            player.quiz_1_init = form_data['quiz_1']
            player.quiz_2_init = form_data['quiz_2']
            player.quiz_3_init = form_data['quiz_3']
            player.quiz_4_init = form_data['quiz_4']
            player.quiz_5_init = form_data['quiz_5']
            
        
            
        grades = quiz_grade_vars(player, form_data)
        show_next = grades['total_score'] == 5
        ret = {player.id_in_group: dict(func = "graded",
                                         grades = grades,
                                         show_next = show_next
                                         )}
        
        # Save form data to the player object for persistance
        player.quiz_1 = form_data['quiz_1']
        player.quiz_2 = form_data['quiz_2']
        player.quiz_3 = form_data['quiz_3']
        player.quiz_4 = form_data['quiz_4']
        player.quiz_5 = form_data['quiz_5']
        
        return ret

    
    ###
    ##
    ## Initial Load - This persists current form entries across page loads
    ##
    ###
    elif func == 'load':
        ## Initial page load
        ret = dict(func="load",
                   id_quiz_1 = player.field_maybe_none('quiz_1'),
                   id_quiz_2 = player.field_maybe_none('quiz_2'),
                   id_quiz_3 = player.field_maybe_none('quiz_3'),
                   id_quiz_4 = player.field_maybe_none('quiz_4'),
                   id_quiz_5 = player.field_maybe_none('quiz_5'),
                   )
        return {player.id_in_group: ret}
 
    
 
class Quiz(Page):
    form_model = 'player'
    form_fields = ['quiz_1', 'quiz_2', 'quiz_3', 'quiz_4', 'quiz_5']
    timeout_seconds = C.QUIZ_TIMEOUT

    live_method = quiz_live_method
    is_displayed = is_displayed_common
    


    
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
    
    is_displayed = is_displayed_common
     
             
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


    vars_for_template = template_vars_commom
    is_displayed = is_displayed_common
        

class ReadyToStart(Page):
    timeout_seconds = C.START_TIMEOUT
    timer_text = "Time Left to Enroll in the Game: "
    is_displayed = is_displayed_common
    
    @staticmethod
    def vars_for_template(player: Player):
        exp_link = get_exp_link(player)
            
        return dict(exp_link = exp_link)
    
    

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

page_sequence = [Consent,  Instructions, Quiz, Survey1,  WaitForPlayers, ReadyToStart, NoConsent, ]