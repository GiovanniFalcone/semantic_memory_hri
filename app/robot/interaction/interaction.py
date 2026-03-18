"""
Flow of the interaction module:
    1. The robot greets the user. 
    2. The robot explains the rules of the game.
    3. The robot interacts with the user during the game, providing curiosity about the argoment in which the robot is competent.
    4. The robot ends the interaction with a goodbye message.   
"""

import os
import random
import time
import json
import sys

# to access to config file
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from util.util import Util

# robot
from model.interface.robot_interface import RobotInterface

class InteractionModule:
    SKIP_INTRO = Util.get_from_json_file("config")['skip_intro']

    def __init__(self, robot: RobotInterface, competence: str, language='ita'):
        # initialize variable
        self.robot = robot
        self.language = language
        self.player_name = Util.get_from_json_file("config")['player_name']
        # do randomic movement with robot's head in order to look more natural
        self.robot.random_head_movements()
        # get sentences from interaction file (greetings, rules, goodbye)
        self.speech = self.load_interaction_sentences("interaction.json")
        # get sentences based on robot competence
        self.geo_competence = self.load_interaction_sentences("geography_competence.json")
        self.math_competence = self.load_interaction_sentences("math_competence.json")
        # incompetence
        self.geo_incompetence = self.load_interaction_sentences("geography_incompetence.json")
        self.math_incompetence = self.load_interaction_sentences("math_incompetence.json")
        

    ###############################################################################################################
    #                                                   SETTINGS                                                  #
    ###############################################################################################################

    def load_interaction_sentences(self, filename):
        """Get sentences from interaction file."""
        filename = os.path.join(os.path.dirname(__file__), '../sentences', self.language, filename)
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"File {filename} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON file {filename}.")
            return {}

    ###############################################################################################################
    #                                                INTERACTION                                                  #
    ###############################################################################################################

    def start_interaction(self):
        """BEGIN state"""
        print(f"[Start] User detected, starting interaction...")
        # if skip_intro is True, the robot will not greet the user 
        if not InteractionModule.SKIP_INTRO:
            self.greetings()
            self.rules()

    def greetings(self):
        """The robot will start the interaction."""
        print("[Greetings] ...")
        sentences = self.speech["greetings"]
        sentence = random.choice(sentences)
        self.speak(sentence)

    def rules(self):
        """Robot explain the rules to the user."""
        print("[Before rules] Robot talking...")
        sentences = self.speech["before_rules"]
        sentence = random.choice(sentences)
        self.speak(sentence)

        print("[Rules] Robot uttering rules...")
        sentences = self.speech["rules"]
        sentence = random.choice(sentences)
        self.speak(sentence)

    def goodbye(self):
        """Ending state of the interaction."""
        print(f"[Goodbye] Waiting a moment before saying goodbye...")
        time.sleep(1.0)
        print("[Goodbye] Speaking ...")
        sentences = self.speech["end"]
        sentence = random.choice(sentences)
        self.speak(sentence)

    def get_curiosity(self, card_name, subject, condition):
        if condition in [0, 1]:
            # C or SC
            if subject == "geography":
                return random.choice(self.geo_competence[card_name])
            elif subject == "math":
                return random.choice(self.math_competence["math"])
            else:
                return None
        else:
            # NC
            if subject == "geography":
                return random.choice(self.geo_incompetence[card_name])
            elif subject == "math":
                return random.choice(self.math_incompetence["math"])
            else:
                return None

    def speak(self, sentence, **kwargs):
        self.robot.say(sentence, **kwargs)