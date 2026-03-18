"""
This module contains the implementation of the Furhat robot interface.
It provides methods to connect to the Furhat robot, send speech, listen for user input,
perform facial expressions, and control the robot's LED lights.

The Furhat class inherits from the RobotInterface class and implements the necessary methods 
to interact with the Furhat robot.

The class is designed to work in both demo mode and SDK mode. In demo mode, it uses the FurhatRemoteAPI
to connect to the robot and perform actions. In SDK mode, it sends HTTP requests to the robot's API
to perform actions.
    - if demo (config.json) is set to True, the functions will simply do nothing.
    - if sdk (config.json) is set to True, the robot will use the HTTP API to communicate with the Furhat robot.
    - if sdk is set to False, the robot will use the FurhatRemoteAPI to communicate with the Furhat robot (in this case, the robot 
      ip should be 'localhost' or the one of the phisical robot).
"""

# furhat API
from furhat_remote_api import FurhatRemoteAPI

# furhat movements
from model.concrete.furhat.automatic_movements import AutomaticMovements
# interface
from model.interface.robot_interface import RobotInterface

import requests
import socket
# to access to config file
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from util.util import Util

# create a separate thread to run automatic movements of furhat's head
import threading
# load custom gestures
import json

class Furhat(RobotInterface):
    def __init__(self, IP, PORT):
        self.robot = None
        self._gestures_api = None
        self._HRI = Util.get_from_json_file("config")['HRI']
        self._sdk = Util.get_from_json_file("config")['robot_sdk']
        self.furhat_ip = IP
        self.furhat_port = PORT
        language = Util.get_from_json_file("config")['language'] 
        self.language = 'it-IT' if language == "ita" else "en-US"

    def _get_session(self):
        """
        Returns a connection to furhat robot if session is not established yet, otherwise it will return the old session. 
        """
        session = None

        try:
            session = FurhatRemoteAPI(self.furhat_ip)
        except Exception as e:
            print("Unable to connect to Furhat:", e)
            os._exit(1)
                
        return session

    def connect(self):
        # do not connect to the robot if HRI is set to False
        if not self._HRI:
            return
        
        # check if sdk is running
        if self._sdk:   
            # check if sdk is started
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                try:
                    s.connect((self.furhat_ip, self.furhat_port))
                    print("Ok, sdk is running!")
                    return
                except (ConnectionRefusedError, socket.timeout):
                    print("Connection refused. Did you run Furhat SDK first?")
                    sys.exit(1)
            return
        
        self.robot = self._get_session()
        # load built-in gestures 
        expressions = self.robot.get_gestures()
        self._gestures_api = [expression.name for expression in  expressions]

    def say(self, sentence, **kwargs):
        # if sdk is set to True, then send an http request to robot sdk to make it speak the sentence
        if self._sdk:
            data = {"sentence": sentence}
            if 'emotion' in kwargs:
                data.update(kwargs)
                self._send_http_request(route="feedback", data=data)
            else:
                # generic furhat.say(something)
                self._send_http_request(route="speech", data=data)
            return 

        # if HRI is True, the robot (remote api) can speak
        if self._HRI:
            self.robot.say(text=sentence, blocking=True)

    def listen(self):
        # send and http request to sdk 
        # returns what robot heard
        if self._sdk:
            response = self._send_http_request(route="listen", data=None)
            return response.text

        # if HRI is set to True, then call listen method using current language
        if self._HRI:
            answer = self.robot.listen(language=self.language)
            return answer.message

    def user_detection(self):
        # if HRI is set to True, use remote python api, while in other cases return a string
        if self._HRI and not self._sdk:
            users = self.robot.get_users()
            # Attend the user closest to the robot
            self.robot.attend(user="CLOSEST")
            return users
        else:
            # used for demo (without connecting to the robot)
            return 'other'

    def random_head_movements(self):
        # do nothing if you are using robot sdk 
        if self._sdk: return 

        # when HRI is set to True run another thread to perform random gesture
        if self._HRI:
            # create a separate thread to run automatic movements of furhat's head
            threading.Thread(target=AutomaticMovements.random_head_movements, args=(self.robot, )).start()

    def do_facial_expression(self, expression):
        # if sdk is set to True,  send an http request to robot sdk in order to perform the gesture
        if self._sdk:
            self._send_http_request(route="gesture", data={"gesture": expression})
            return
        
        # if HRI is set to False, do nothing
        if not self._HRI: return
        
        # else, check if the expression is a built-in gesture or a custom one
        if expression in self._gestures_api:
            self.robot.gesture(name=expression)
        else:
            # custom
            raise ValueError(f"Gesture '{expression}' not defined!")

    def set_color_led(self, red, green, blue):
        # if sdk is set to True, send an http request to robot sdk in order to set the led
        if self._sdk:
            res = self._send_http_request(route="led", data={"r": red, "g": green, "b": blue})
            return
        
        # if HRI is set to False, do nothing
        if not self._HRI:
            return
        
        # else, set color of the led using python remote api
        self.robot.set_led(red=red, green=green, blue=blue)

    def _send_http_request(self, route, data):
        """
        Send an HTTP request to the Furhat robot.
        """
        url = f"http://{self.furhat_ip}:{self.furhat_port}/{route}"
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error sending HTTP request: {e}")
        
    