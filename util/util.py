import json
import os
import shutil
import numpy as np
import csv

from socket import *
from pathlib import Path

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class Util:
     
    @staticmethod
    def get_from_json_file(filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename + ".json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{filename}.json file not found at: {file_path}")
        
        with open(file_path, "r") as configfile:
            data_file = json.load(configfile)
            
        return data_file

    @staticmethod
    def put_data_in_csv(csv_data, id_player, n_game):
        file_path = Path("../app/data/user_" + str(id_player) + "/game_data_" + str(n_game) + ".csv")
        keys = csv_data.keys()

        if file_path.is_file() is False:
            # add header
            with open(file_path, "a+", newline='') as outfile:
                writer = csv.writer(outfile, delimiter = ";")
                # write header only if file doesn't exists
                writer.writerow(keys)
                writer.writerows(list(zip(*[csv_data[key] for key in keys])))
        else:
            # if it does exists do not add the header
            with open(file_path, "a+", newline='') as outfile:
                writer = csv.writer(outfile, delimiter = ";")
                writer.writerows(list(zip(*[csv_data[key] for key in keys])))

    @staticmethod
    def update_log_file(data, id_player, n_game):
        if id_player == -1:
            return 
        
        file_path = Path("../app/data/user_" + str(id_player) + "/log_file_" + str(n_game) + ".txt")
        try:
            with open(file_path, "a+", newline='') as outfile:
                outfile.write(data)
        except Exception as e:
            print(f"Error: {e}\n {os.getcwd()}")

    @staticmethod
    def delete_files(id_player, n_game):
        """
        This function delete the log file and csv associated to the user.
        It is used in case the user has reloaded the page without finishing the game.
        """
        file_path = Path("../app/data/user_" + str(id_player) + "/log_file_" + str(n_game) + ".txt")
        os.remove(file_path)
        file_path = Path("../app/data/user_" + str(id_player) + "/game_data_" + str(n_game) + ".csv")
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error during the deletion of the '/game_data_{n_game}.csv' file: {e}")
    
    @staticmethod
    def create_dir_for_current_user(player_id):
        """
        This function will create a directory for the user who has to play the game.
        """
        # Check if the 'data' directory exists
        data_dir = "../app/data"
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                Util.formatted_debug_message("The 'data' directory has been created!", level='INFO')
            except OSError as e:
                print(f"Error during the creation of the 'data' directory: {e}")

        # path for the current user
        user_path = "../app/data/user_" + str(player_id)
        # create the directory
        try:
            if not os.path.exists(user_path):
                os.makedirs(user_path)
            else:
                print("The directory already exists!")
        except OSError as e:
            print(f"Error during the creation of directory: {e}")

    @staticmethod
    def check_if_dir_with_id_already_exists(player_id):
        user_path = "../app/data/user_" + str(player_id)
        if os.path.exists(user_path):
            answer = input(f"Directory with ID={player_id} already exists. Do you want to delete it? y/n: ")
            if answer in ['yes', 'Y', 'Yes', 'y']:
                shutil.rmtree(user_path)
            else:
                raise ValueError("Restart application with another id!")
    
    @staticmethod
    def formatted_debug_message(message, level='INFO'):
        """
        Formats a debug message with visual delimiters and log level labels.

        Args:
            - message (str): The message to format.
            - level (str): The log level of the message (default: 'INFO').
        """
        delimiter = "*" * 100
        print(f"{delimiter}\n[{level}] {message}\n{delimiter}")