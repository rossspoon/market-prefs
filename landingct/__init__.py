from otree.api import *
from common.ParticipantFuctions import generate_participant_ids
import time
doc = ''

class C(BaseConstants):
    NAME_IN_URL = 'wait'
    PLAYERS_PER_GROUP = 40 #should be 25+15
    WAITING_PLAYERS_PER_GROUP = 26 #should be 25+2
    MIN_PLAYERS_PER_GROUP = 3 #should be 25
    NUM_ROUNDS = 1
    WAIT_TIMEOUT = 1500 #25min max for waiting room
    INST_TIMEOUT = 1200 #20min max for instructions 
    SURVEY1_TIMEOUT = 900 #15min max for instructions 
    CONSENT_TIMEOUT = 120 #2min max for consent
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
    session.prolific_completion_url = 'https://app.prolific.co/submissions/complete?cc=C1I28ND3'
    #session.incomplete_code = 'C1KGSHEV'
    
    generate_participant_ids(subsession)
    for p in subsession.get_players():
        p.participant.survey_1_click = False

class Group(BaseGroup):
    pass
    

class Player(BasePlayer):
    timeout = models.FloatField(initial=0.0)
    quiz1 = models.IntegerField(
        label='1. On the left hand side of the decision screen, everyone sees _____ simulated weather forecasts',
        choices=[
            [1, 'the same'],
            [2, 'different']
        ]
    )
    quiz2 = models.IntegerField(
        label='2. You can click on a prediction  _____ times during each 10 second decision trial',
        choices=[
            [1, '1'],
            [2, '2'],
            [3, 'as many as you want']
        ]
    )
    quiz3 = models.IntegerField(
        label='3. Your payoff for the trial is determined by  _____',
        choices=[
            [1, 'the amount of time you maintain a correct prediction'],
            [2, 'the correctness of your last decision'],
            [3, 'All of the above']
        ]
    )
    quiz4 = models.IntegerField(
        label='4. If the right side of your screen shows you information from 3 neighbors, 2 of which depict Rain and 1 of which is empty, this means that _____',
        choices=[
            [1, 'A majority of your neighbors are predicting Rain'],
            [2, 'None of your neighbors are prediction Sun'],
            [3, 'One of your neighbors has not made a choice yet'],
            [4, 'All of the above']
        ]
    )
    # quiz5 = models.IntegerField(
    #     label='5. Your neighbors will be _____ on every round',
    #     choices=[
    #         [1, 'the same'],
    #         [2, 'different']
    #     ]
    # )

    

class Consent(Page):
    timeout_seconds = C.CONSENT_TIMEOUT
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.participant.consent = 0
        else:
            player.participant.consent = 1

    @staticmethod
    def app_after_this_page(player, upcoming_apps):
        if player.participant.consent == 0:
            return upcoming_apps[-1]

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
        
    
class Survey1(Page):
     #timeout_seconds = C.SURVEY1_TIMEOUT
     timer_text = "Time Left to Complete the Instructions: "
     form_model = 'player'
     
     @staticmethod
     def before_next_page(player: Player, timeout_happened):
         pass
         
     @staticmethod
     def vars_for_template(player: Player):
         config = player.session.config
         print(config)
         survey_link = config.get('survey_1_link')
         print(survey_link)
         return dict(
             survey_link = survey_link,
             )
     
     @staticmethod
     def js_vars(player: Player):
         config = player.session.config
         survey_1_pg_cnt = config.get('survey_1_pg_cnt')
         return dict(
             survey_pg_cnt=survey_1_pg_cnt
             )

     
             
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
    
        # if data['out']==0:
        #     session.arrived_ids[group-1].add(player.id_in_group)
        # elif data['out']==1:
        #     session.arrived_ids[group-1].remove(player.id_in_group)
        # if data['enrolled'] ==1:
        #     session.enrolled_ids[group-1].add(player.id_in_group)
        # return {0: dict({'arrived': len(session.arrived_ids[group-1]),
        #              'enrolled': len(session.enrolled_ids[group-1])})}
    
        

class Calibration(Page):  
    pass

class ReadyToStart(Page):
    timeout_seconds = C.START_TIMEOUT
    timer_text = "Time Left to Enroll in the Game: "
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

page_sequence = [Consent, Survey1, Instructions, WaitForPlayers, ReadyToStart]