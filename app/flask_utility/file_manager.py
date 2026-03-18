"""
Class used to manage csv file
"""
import sys
import os
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from util.util import Util

class FileManager:

    def __init__(self):
        """
        Initializes a FileManager object.

        Attributes:
        ----------
            id_player (int): ID of the player.
            n_game (int): Number of times that player has played
            CSV_FIELDS (list): List of field names for the CSV data.
            csv_data (dict): Dictionary to store CSV data fields.
            experimental_condition (str): name of experimental condition
        """
        self.id_player = None
        self.n_game = 1
        self.n_rows = Util.get_from_json_file("config")['n_rows']
        self.n_cols = Util.get_from_json_file("config")['n_cols']
        self.n_pairs = Util.get_from_json_file("config")['pairs']
        self.CSV_FIELDS = ['id_player', 'experiment_condition', 'turn_token', 'turn_number', 
                           'position_clicked', 'time_game','time_until_match', 'match', 
                           'game_ended', 'board_changed', 'robot_speech', 'wrong_card']
        self.csv_data = {field: [] for field in self.CSV_FIELDS}
        self.experimental_condition = ''

    def _write_game_data_on_file(self, data):
        """
        Write on file the user's info and update the structure for csv data.
        """
        self._update_csv_data(data)
        self._update_log_file_by_game_data(data)

    def _update_log_file_by_game_data(self, data):
        """
        Write on log file the user's info.
        """
        game_data = data.get("game", {})
        token = 'robot' if game_data.get('is_robot_turn', False) else 'human'
        Util.update_log_file(f"\nTurn: {game_data.get('turn', 'N/A')}\nTurn token: {token}\nPosition_clicked: {game_data.get('position', 'N/A')}\nCard_clicked: {game_data.get('open_card_name', 'N/A')}\nTime_game: {game_data.get('time_game', 'N/A')}\nTime_before_match: {game_data.get('time_until_match', 'N/A')}\nMatch: {game_data.get('match', 'N/A')}\n", self.id_player, self.n_game)

    def _write_board_on_file(self, shuffle_cards, changed=False):
        """
        Print game board as matrix and write it on log-file.

        Args:
            shuffle_cards (list): List of cards.
        """
        output_lines = []
        board = np.zeros((self.n_rows, self.n_cols))
        board = np.reshape(shuffle_cards, (self.n_rows, self.n_cols))
        mx = len(max((sub[0] for sub in board), key=len))
        for row in board:
            output_lines.append(" ".join(["{:<{mx}}".format(ele, mx=mx) for ele in row]))

        # write board on file
        if changed: Util.update_log_file("\nGame board changed!\n\n", self.id_player, self.n_game) # add a new line if game board is changed
        if self.id_player != -1: Util.update_log_file("\n".join(output_lines) + "\n", self.id_player, self.n_game)

    def _clear_csv_struct(self):
        """
        Clear csv structure for other users.
        """
        for field in self.CSV_FIELDS:
            if isinstance(self.csv_data[field], list):
                self.csv_data[field].clear()
            else:
                self.csv_data[field] = ''

    def append_csv_field(self, field_name, value):
        """
        Append a value to a specific field in the csv_data dictionary.

        Args:
            field_name (str): The name of the field to which the value should be appended.
            value: The value to append to the specified field.
        """
        if field_name in self.csv_data:
            self.csv_data[field_name].append(value)
        else:
            raise KeyError(f"Field '{field_name}' does not exist in csv_data.")
    
    def _update_csv_data(self, data):
        """
        Update structure for csv data.
        """

        if 'game' in data:
            game_data = data['game']
            subject = game_data.get("robot_subject", "")
            token = subject if game_data.get('is_robot_turn', False) else 'human'

            self.csv_data["id_player"].append(self.id_player)
            self.csv_data["experiment_condition"].append(self.experimental_condition)

            self.csv_data["turn_token"].append(token)
            self.csv_data["turn_number"].append(game_data.get("turn", 0))
            self.csv_data["position_clicked"].append(game_data.get("position", []))
            self.csv_data["time_game"].append(game_data.get("time_game", "0:0"))
            self.csv_data["time_until_match"].append(game_data.get("time_until_match", "0:0"))
            self.csv_data["match"].append(game_data.get("match", False))
            self.csv_data["board_changed"].append(game_data.get("board_changed", False))
            self.csv_data["robot_speech"].append(game_data.get("robot_speech", False))
            self.csv_data["wrong_card"].append(game_data.get("is_wrong_card", False))
            self.csv_data["game_ended"].append(game_data.get("pairs", 0) == self.n_pairs)

            # if game is finished, write the csv file and clear the csv structure
            if game_data.get("pairs", 0) == self.n_pairs:
                import time
                time.sleep(0.5)
                Util.formatted_debug_message("Saving csv...", level='INFO')
                Util.put_data_in_csv(self.csv_data, self.id_player, self.n_game)
                Util.formatted_debug_message("Data saved on csv file. Clear csv struct...", level='INFO')
                self._clear_csv_struct()