from flask import jsonify

import time
import threading
import json
import numpy as np
import subprocess

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from util.util import Util

from flask_utility.file_manager import FileManager
from flask_utility.socket_manager import SocketManager
from flask_utility.game_manager import GameManager
from typing import List

class UtilityFlask:
    """
    Utility class for Flask application management.

    Attributes:
        IP_ADDRESS (str): IP address of the server.
        HRI (bool): If true enable pop-up: when robot utter an hint, a pop-up will be shown
    """

    # Constants
    IP_ADDRESS = Util.get_from_json_file("config")['ip'] 
    HRI = Util.get_from_json_file("config")['HRI'] 
    N_ROWS = Util.get_from_json_file("config")['n_rows']
    N_COLS = Util.get_from_json_file("config")['n_cols']
    N_PAIRS = Util.get_from_json_file("config")['pairs']
    SHUFFLE = Util.get_from_json_file("config")['shuffle']

    def __init__(self):
        """
        Initializes a UtilityFlask object.

        Attributes:
            id_player (int): ID of the player.
            experimental_condition (Optional[Any]): Current experimental condition.
            isRobotConnected (bool): Flag indicating if the robot is connected.
            received_hint (dict): Dictionary containing received hints.
            csv_data (dict): Dictionary to store CSV data fields.
        """
        self.id_player = -1
        self.experimental_condition = None
        self.experimental_condition_str = ''
        self.n_game = 1
        self.isRobotConnected = UtilityFlask.HRI

        self.file_manager = FileManager()
        self.socket_manager = SocketManager()
        self.game_manager = GameManager()

        # handle speech/clicks
        self.ready_for_next_move = threading.Event()
        self.ready_for_next_move.set()
        self.ready_for_update_dictionary = threading.Event()
        self.ready_for_update_dictionary.set()

    def build_integer_board(self, shuffle: List[str]) -> List[int]:
        return self.game_manager.build_integer_board(shuffle)
    
    def handle_id_player(self, id_session: int, experimental_condition: int, experimental_condition_str: str):
        """
        Handle the player ID received in the request.

        Args:
            id_session (int): The player ID.
            experimental_condition (Any): The experimental condition.

        Returns:
            Response indicating success or failure.
        """
        self.id_player = id_session

        if self.id_player is not None:
            self.file_manager.id_player = id_session
            self.experimental_condition = experimental_condition
            self.experimental_condition_str = experimental_condition_str

            self.socket_manager.update_session_data(self.id_player, self.experimental_condition)
            self.game_manager.set_experiemental_condition(experimental_condition)

            # update experimental condition for csv
            self.file_manager.experimental_condition = self.experimental_condition_str

            # update log file
            Util.update_log_file(f"id_player: {self.id_player}\n", self.id_player, self.n_game)
            Util.formatted_debug_message("Init for player with ID " + str(self.id_player), level='INFO')
        
    def handle_game_board(self, request):
        """
        Receive and handle the game board sent in the request.

        Args:
            request: The request object containing the game board matrix.

        Returns:
            Response indicating success or failure.
        """
        try:
            data = request.get_json()
            # get id from json data
            game_board = data.get('board')

            # handle game board (received from js)
            # we do not send the board shuffled to the RL agent, since it only needs the value of the open card (e.g Rome is 0, Italy is 1, ...)
            if game_board is not None:
                shuffle_board = game_board.get('shuffled_deck')
                self.game_manager.deck = game_board.get('deck')
                self.game_manager.board_integer = self.build_integer_board(shuffle_board)
                print("[INFO] BOARD:\n")

                self.game_manager.print_board_as_matrix(shuffle_board)
                print("")
                self.game_manager.print_board_as_matrix(self.game_manager.board_integer)

                print("*" * 100)
                
                # print game board (if not local) and write it on log file
                self.file_manager._write_board_on_file(shuffle_board)
                return jsonify({'message': 'Game board received'}), 200
            else:
                return jsonify({'error': 'Game board not provided in the request'}), 400
        except Exception as e:
            print(f"Error in handle_game_board: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def handle_player_move(self, request, socketio):
        """
        Receive and handle the player's move (card clicked, position, ...) sent in the request.

        Args:
            request: The request object containing the game data.
            socketio: SocketIO instance for emitting events.

        Returns:
            Response indicating success or failure.
        """
        try:
            # get json data
            data = request.get_json()
            string = json.dumps(data)
            dictionary = json.loads(string)
            # get id from json data
            player_move = data.get('game')

            if player_move is None:
                return jsonify({'error': 'User move not provided in the request'}), 400
            else:
                self.game_manager.dictionary = dictionary
                board_changed = player_move.get('board_changed', False)
                self.is_agent_turn = player_move.get('is_robot_turn', False)
                new_board = player_move.get('new_board') if board_changed else None
                n_pairs = player_move.get('pairs')
                is_turn_even = player_move.get('turn') % 2 == 0

                if not self.socket_manager.is_robot_connected:
                    self.game_manager.dictionary["game"]["robot_speech"] = False

                # debug print
                if not self.socket_manager.is_robot_connected and not self.socket_manager.is_rl_socket_connected: print("")
                self.game_manager.print_game_state() 

                # send info to RL agent and robot
                # it also wait some second before sending the information
                if self.is_agent_turn:
                    return self._send_click_to_agent_robot(player_move.get("open_card_name"), board_changed, new_board, n_pairs)
                    
                if self.socket_manager.is_rl_socket_connected and not board_changed:
                    index_of_card_clicked = self.game_manager.idx.get(player_move.get('open_card_name'), -1)
                    self.socket_manager.send_to_rl_agent({"human_action": index_of_card_clicked})
                    print(f"{'Emitted move to':<20}: RL application")

                if self.socket_manager.is_robot_connected and not board_changed:
                    # wait some seconds before sending info to robot in order to give enough time to the user to memorize the card
                    if self.is_agent_turn or is_turn_even: time.sleep(0.5) 
                    card_name = player_move.get('open_card_name')
                    subject = "geography" if card_name in self.game_manager.geography_cards else "math"
                    self.socket_manager.send_to_robot({"card_clicked": card_name, "subject": subject, "n_pairs": n_pairs})
                    print(f"{'Emitted move to':<20}: robot application")

                # notify robot application in order to save on csv
                # (only when robot send a response the data are saved on csv,
                # this is done in order to save if robot has utter something or not)
                if self.socket_manager.is_robot_connected and board_changed:
                    self.socket_manager.send_to_robot({"board_changed": True})
                    print(f"{'Emitted move to':<20}: robot application")

                # since robot is not connected speech will be always False
                # thus, we can write on log file and update csv file
                if not self.socket_manager.is_robot_connected:
                    self._write_game_state_on_files()
                    print("")
                
                if board_changed:
                    print(f"{'Board changed':<20}: {board_changed}")
                    # notify RL agent that board has changed
                    if self.socket_manager.is_rl_socket_connected:
                        self.socket_manager.send_to_rl_agent({"has_board_changed": True})
                        print(f"{'Emitted changing to':<20}: RL application") 
                    self._handle_board_change(new_board)
                    
                return jsonify({'message': 'User move received'}), 200
        except Exception as e:
            print(f"Error in handle_player_move: {e}")
            return jsonify({'error': 'Internal server error'}), 500
        
    def handle_turn_change(self, request, socketio):
        """
        Handle turn change event and notify the RL agent when it's their turn.
        
        Sends a handover action to the RL agent when the robot is taking over,
        or emits a handover event to the UI when returning to human turn.

        Args:
            request: The HTTP request containing turn change data.
            socketio: SocketIO instance for emitting events to the UI.

        Returns:
            Flask JSON response indicating successful processing.
        """
        data = request.get_json()
        turn_data = data.get("turn", {})
        is_robot_turn = turn_data.get('is_robot_turn', False)
        robot_type = turn_data.get('robot_type', 'unknown')

        if is_robot_turn:
            if self.socket_manager.is_rl_socket_connected:
                # 9: handover action
                handover_action = UtilityFlask.N_PAIRS * 2 + 1
                self.socket_manager.send_to_rl_agent({"human_action": handover_action, "robot_type": robot_type})
                print(f"{'Emitted data to':<20}: RL application (robot turn: True | robot_type: {robot_type})") 
        else:
            # handover from agent
            socketio.emit('AgentHandover', json.dumps({"turn": False}))
            print(f"{'Emitted handover to':<20}: UI") 

        # save hint object (could be used in order to avoid websocket)
        return jsonify({'message': 'Hint agent received'}), 200
    
    def handle_agent_move(self, request, socketio):
        """
        Handle a move (card selection) made by the RL agent/robot.
        
        Validates the agent move data and forwards it to the UI via SocketIO emission.
        Maps the action index to the actual card name before sending to UI.

        Args:
            request: The HTTP request containing the agent's move (action and robot type).
            socketio: SocketIO instance for emitting events to the UI.

        Returns:
            Flask JSON response with success/error message.
        """
        data = request.get_json()
        agent_move = data.get('agent_move') 
        robot_type = agent_move.get('robot_type')
        has_provided_a_wrong_card = agent_move.get('is_wrong_card')

        if agent_move is not None:
            card_action = agent_move.get('action')
            if card_action is not None:
                print(f"{'Received agent move':<20}: {card_action} ({robot_type}) | wrong_card: {has_provided_a_wrong_card}") 
                card_name = list(self.game_manager.idx.keys())[card_action]
                socketio.emit('AgentMove', json.dumps({"card_clicked": card_name, "robot_type": robot_type, "wrong_card": has_provided_a_wrong_card}))
                print(f"{'Emitted action to':<20}: UI") 
                return jsonify({'message': 'Robot move received'}), 200
            else:
                return jsonify({'error': 'Action not provided in agent move'}), 400
        else:
            return jsonify({'error': 'Robot move not provided in the request'}), 400

    def handle_robot_speech(self, request, socketio):
        """
        Handle robot speech/curiosity utterance events.
        
        Manages the speech pop-up display and removal, updates game state,
        and handles synchronization with the UI. Updates CSV/log files when speech occurs.

        Args:
            request: The HTTP request containing speech data and status (uttering/uttered/None).
            socketio: SocketIO instance for emitting pop-up events to the UI.

        Returns:
            Flask JSON response indicating the speech processing result.
        """
        data = request.get_json()
        speech = data.get('speech')
        has_robot_utter_something = data.get('speech_status', None)

        if speech:
            if has_robot_utter_something == "uttering":
                print(f"{'Speech status':<20}: uttering")
                socketio.emit('Speech', json.dumps(data))
                print(f"{'Emitted status to':<20}: UI (show pop-up)")
                self.game_manager.dictionary["game"]["robot_speech"] = True
                self._write_game_state_on_files()
                return jsonify({'message': 'curiosity - uttering'}), 200
            else: 
                # uttered
                print(f"{'Speech status to':<20}: uttered")
                  # wait a bit before removing the pop-up
                socketio.emit('Speech', json.dumps(data))
                print(f"{'Emitted status to':<20}: UI (remove pop-up)")
                if self.is_agent_turn: time.sleep(0.5)
                self.ready_for_next_move.set()
                if self._is_game_ended():
                    self.socket_manager.send_to_robot({"game_ended": True})
                # just to print in clear way
                if self.game_manager.is_human_turn(): print("")
                return jsonify({'message': 'curiosity uttered'}), 200
        else:
            print(f"{'Speech status':<20}: None")
            self.game_manager.dictionary["game"]["robot_speech"] = False
            self._write_game_state_on_files()
            # wait before wake up via event in order to not click too fast the cards (only used when there is no robot)
            if self.is_agent_turn: time.sleep(0.5)
            self.ready_for_next_move.set()
            if self._is_game_ended():
                self.socket_manager.send_to_robot({"game_ended": True})
            # just to print in clear way
            if self.game_manager.is_human_turn(): print("")
                
            return jsonify({'message': 'no speech'}), 200
        
    def _is_game_ended(self):
        return self.game_manager._is_game_ended()
        
    def _write_game_state_on_files(self):
        """
        Write dictionary on csv and a txt file
        """
        # debug
        # print(f"Writing on file: {self.game_manager.dictionary}")
        self.file_manager._write_game_data_on_file(self.game_manager.dictionary)

    def _handle_board_change(self, new_board: List[str]):
        """
        Handle board change by writing to file and updating internal state.

        Args:
            new_board (List[str]): The new shuffled board.
        """
        # write new board on file
        self.file_manager._write_board_on_file(new_board, changed=True)
        # update internal board
        self.board_integer = self.build_integer_board(new_board)
        # debug print
        print("\n" + "*" * 100)
        print("[INFO] BOARD CHANGED:\n")
        self.game_manager.print_board_as_matrix(new_board)
        print("")
        self.game_manager.print_board_as_matrix(self.board_integer)  
        print("*" * 100, "\n")  
        
    def _send_click_to_agent_robot(self, card_name, board_changed, new_board, n_pairs):
        """
        Send player's card click to the robot/agent and handle their response.
        
        Sends card information to the robot and waits for completion signal.
        Handles board changes and communicates with the RL agent.
        Uses threading events for synchronization to avoid blocking.

        Args:
            card_name (str): Name of the card that was clicked.
            board_changed (bool): Whether the board state changed after this move.
            new_board (List[str]): The new board state if changed, None otherwise.
            n_pairs (int): Number of card pairs on the current board.

        Returns:
            Flask JSON response indicating the card click was processed.
        """
        self.ready_for_next_move.clear()

        if self.socket_manager.is_robot_connected and not board_changed:
            # wait some seconds before sending info to robot in order to give enough time to the user to memorize the card
            time.sleep(1.0)
            # send the card's name to the robot application in order to utter a curiosity
            subject = "geography" if card_name in self.game_manager.geography_cards else "math"
            self.socket_manager.send_to_robot({"card_clicked": card_name, "subject": subject, "n_pairs": n_pairs})
            print(f"{'Emitted move to':<20}: robot application")
            # ASPETTA qui: il thread si blocca finché non arriva la notifica "finished"
            # Mettiamo un timeout di sicurezza (es. 10 sec) per evitare blocchi infiniti
            self.ready_for_next_move.wait(timeout=10.0)
        else:
            # wait some seconds before sending info to RL agent in order to not click too fast the cards (only used when there is no robot)
            time.sleep(1.0)
            self.ready_for_next_move.set()

        if self.socket_manager.is_rl_socket_connected:
            self.socket_manager.send_to_rl_agent({"has_robot_clicked_card": True, "has_board_changed": board_changed})
            print(f"{'Emitted move to':<20}: RL application")

        # when board changes, update txt file and csv, and print the new board for debug
        if board_changed:
            self._handle_board_change(new_board)
            time.sleep(0.5)

        # since robot is not connected speech will be always False
        if not self.socket_manager.robot_socket_connected:
            self._write_game_state_on_files()

        print("")
        return jsonify({'message': 'Card clicked from robot on UI'}), 200

    def handle_cheater(self):
        """
        This function will delate the files associated to the user in case they refreshed the page
        without finishing the game.
        Then it restart the Q-learning script.
        """
        Util.formatted_debug_message(f"Deleting csv file of player with ID={self.id_player}...", level='INFO')
        Util.delete_files(self.id_player, self.n_game)
        Util.formatted_debug_message("File deleted...", level='INFO')
        self.file_manager._clear_csv_struct()
        Util.formatted_debug_message("CSV cleaned, restarting...", level='INFO')
        
        # *************************
        # SHOULD RESTART Q-LEARNING
        # *************************

    def handle_rl_agent_exit(self):
        """
        Handle the exit of the RL agent when it closes the connection.
        Writes final game state to files and closes the socket connection.
        """
        try:
            # Close the socket connection via socket manager
            self.socket_manager.handle_rl_agent_exit()
            Util.formatted_debug_message(f"RL agent exit handled for player {self.id_player}", level='INFO')
        except Exception as e:
            Util.formatted_debug_message(f"Error handling RL agent exit: {e}", level='ERROR')

    def handle_robot_exit(self):
        """
        Handle the exit of the robot client when it presses CTRL+C or closes the connection.
        Writes final game state to files and closes the socket connection gracefully.
        """
        try:# Close the socket connection via socket manager
            self.socket_manager.handle_robot_exit()
            Util.formatted_debug_message(f"Robot exit handled for player {self.id_player}", level='INFO')
        except Exception as e:
            Util.formatted_debug_message(f"Error handling robot exit: {e}", level='ERROR')

      