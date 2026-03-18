import os
import json
import requests
import sys
import random
import signal
import time
from socket import *

# to access to config file
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from util.util import Util

# robot
from model.interface.robot_interface import RobotInterface
from model.robot_factory import RobotFactory
# interaction functions
from interaction.interaction import InteractionModule

class ManagerNode:
    IP_ADDRESS = Util.get_from_json_file("config")['ip']
    LANGUAGE = Util.get_from_json_file("config")['language']

    def __init__(self, robot_1: RobotInterface, robot_2: RobotInterface, language='ita'):
        # Initialize variables
        self.robot_1 = robot_1                            # Robot object
        self.language = ManagerNode.LANGUAGE              # Language used by the robot                      
        self.interaction_1 = InteractionModule(robot_1, language)
        self.robot_1 = robot_2                            # Robot object                  
        self.interaction_2 = InteractionModule(robot_2, language)
        self.player_id = -1                               # Player id used for Flask route      
        self.experimental_condition = None    
        self.n_pairs = Util.get_from_json_file("config")['pairs']
        self.client_socket = None                         # Socket connection to Flask server

    def get_player_id(self):
        return self.player_id

    def _send_to_flask(self, route, json_data):
        try:
            requests.post("http://" + ManagerNode.IP_ADDRESS + ":5000/" + route, json=json_data)
        except requests.exceptions.RequestException as e:
            print(f"[Manager] HTTP error request: {e}")    
    
    def detect_person(self):
        """
        If this callback is triggered, it means that the user is in the robot's field of view, so the robot can initiate the interaction. 
        After finishing the conversation, it enters the game_state (by setting the corresponding variable).
        """
        print("[Manager] Waiting for user...")
        users = self.robot_1.user_detection()
        if len(users) > 0:
            print("[Manager] User detected, starting interaction...")
            self.interaction_1.start_interaction()

    def handle_game(self, client_socket):
        """
        Robot receive the action and eventually it will say something about the card/action clicked.
        Once the robot has uttered the curiosity an http request is sent to the server in order to remove the pop-up.
        This functions works wheater the condition is emotional or not.
        """
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                print("[Manager] Server closed connection.")
                return 1
            json_data = json.loads(data)
        except Exception as e:
            print(f"[Manager] Socket error or connection closed: {e}")
            return 1

        # Handle special control messages first
        if "id_player" in json_data:
            self.player_id = json_data["id_player"]
            self.experimental_condition = json_data.get("experimental_condition")
            print(f"\n[Manager] {'Received ID:':<20} {self.player_id}")
            print(f"[Manager] {'Received condition:':<20} {self.experimental_condition}\n")
            return 0

        if "game_ended" in json_data:
            self.interaction_1.goodbye()
            print("")
            res = input("Close server? y/n ")
            if res == 'y':
                return 1
            return 0

        if "board_changed" in json_data:
            print(f"{'[Manager] Uttering curiosity':<30}: 'No' (cause board is changed)\n")
            # Robot will not utter anything when board changed
            self._send_robot_speech(self.player_id, speech=False)
            return 0

        # Otherwise, treat the message as a card-click/game event
        return self._handle_card_click(json_data)

    def _send_robot_speech(self, player_id, speech, subject=None, status=None):
        payload = {"speech": speech}
        if subject is not None:
            payload["subject"] = subject
        if status is not None:
            payload["speech_status"] = status
        self._send_to_flask(route=f"robot_speech/{player_id}", json_data=payload)

    def _handle_card_click(self, json_data):
        card_name = json_data.get("card_clicked", "")
        subject = json_data.get("subject")
        n_pairs = json_data.get("n_pairs")

        print(f"[Manager] {'Received game data':<20}: card '{card_name}' | subject '{subject}' | pairs '{n_pairs}'")

        # Decide randomly whether the robot will utter a curiosity
        speak = random.choices([0, 1], weights=[0.7, 0.3])[0]
        if not speak:
            print(f"{'[Manager] Uttering curiosity':<30}: 'No'\n")
            self._send_robot_speech(self.player_id, speech=False)
            return

        # Do not speak if the game is already finished
        if n_pairs == self.n_pairs:
            return

        # If there's a valid card, prepare and utter the curiosity
        if card_name:
            print(f"{'[Manager] Uttering curiosity':<30}: 'Yes'")
            self._send_robot_speech(self.player_id, speech=True, subject=subject, status="uttering")

            sentence = self.interaction_1.get_curiosity(card_name, subject, self.experimental_condition)
            time.sleep(1.0)
            if subject == "math":
                print(f"{'[Manager] Robot speaking':<30}: 1\n")
                self.interaction_1.speak(sentence)
            else:
                print(f"{'[Manager] Robot speaking':<30}: 2\n")
                self.interaction_2.speak(sentence)

            self._send_robot_speech(self.player_id, speech=True, subject=subject, status="uttered")

    def run(self):
        # connection with server flask using socket
        SERVER_IP = Util.get_from_json_file("config")['ip'] 
        SERVER_PORT = int(Util.get_from_json_file("config")['robot_1_port'])
        
        # detect person
        self.detect_person()
        # connect to Flask in order to receive the actions from rl agent
        self.client_socket = self.connect_to_server(SERVER_IP, SERVER_PORT)
        # once the person is detected handle the game with that person
        while True:
            res = self.handle_game(self.client_socket)
            if res: break

        # close connection
        self._send_to_flask(route="robot_speech", json_data={"close": True})
        sys.exit(1)
    
    def close_socket(self):
        """Close the socket connection gracefully."""
        if self.client_socket:
            try:
                self.client_socket.close()
                print("[Manager] Socket connection closed.")
                sys.exit(1)
            except Exception as e:
                print(f"[Manager] Error closing socket: {e}")

    def connect_to_server(self, server_name, server_port):
        client_socket = socket(AF_INET, SOCK_STREAM) 
        connected = False
        while not connected:
            try:
                # connect socket to remote server at (serverName, serverPort)
                client_socket.connect((server_name, server_port))
                connected = True
            except Exception as e:
                print("catch exception: ", e)
        print("Connected to: " + str(client_socket.getsockname()))

        return client_socket

def handle_exit(manager_node, *args):
    # id = manager_node.get_player_id()
    # manager_node._send_to_flask(route=f"robot_exit/{id}", json_data={"close_connection": True})
    print("**********************************************")
    print("[Manager] CTRL+C pressed. Exit from program...")
    print("**********************************************")
    # Close socket connection gracefully
    manager_node.close_socket()
    sys.exit(0)

if __name__ == '__main__':
    # get robot from configuration file and create the instance 
    robot_type = Util.get_from_json_file("config")['robot_type']

    furhat_1_ip = Util.get_from_json_file("config")['robot_1_ip'] 
    furhat_1_port = Util.get_from_json_file("config")['robot_1_port'] # only for sdk
    
    furhat_2_ip = Util.get_from_json_file("config")['robot_2_ip'] 
    furhat_2_port = Util.get_from_json_file("config")['robot_2_port'] # only for sdk
    
    robot_1 = RobotFactory.create_robot(robot_type, furhat_1_ip, furhat_1_port)
    robot_2 = RobotFactory.create_robot(robot_type, furhat_2_ip, furhat_2_port)

    # connect to robot 
    robot_1.connect()
    robot_2.connect()

    # debug
    robot_sdk = Util.get_from_json_file("config")['robot_sdk']
    if not robot_sdk:
        print(f"[Manager] Connection with '{robot_type}' successfully established!")
    else:
        print(f"[Manager] '{robot_type}' will use SDK.")
            
    # if connection is ok than start
    manager_node = ManagerNode(robot_1, robot_2)
    
    # handle CTRL+C with reference to manager_node
    signal.signal(signal.SIGINT, lambda *args: handle_exit(manager_node, *args))
    
    manager_node.run()