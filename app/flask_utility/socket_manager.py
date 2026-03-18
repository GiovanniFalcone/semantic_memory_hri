import threading
import socket
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from util.util import Util

class SocketManager:
    def __init__(self):
        self.server_ip = Util.get_from_json_file("config")['ip']
        self.id_player = -1
        self.experimental_condition = None
        # rl socket connection
        self.rl_agent_socket = None
        self.rl_socket_connected = False
        rl_agent_port = Util.get_from_json_file("config")['agent_port']
        threading.Thread(target=self.create_rl_agent_socket, args=(rl_agent_port,)).start()
        # robot socket connection
        self.robot_socket = None
        self.robot_socket_connected = False
        self.robot_is_speaking = False
        robot_port = Util.get_from_json_file("config")['robot_1_port']
        threading.Thread(target=self.create_robot_socket, args=(robot_port,)).start()

    def update_session_data(self, id_player: int, experimental_condition):
        """Update session data and send to connected sockets if needed."""
        self.id_player = id_player
        self.experimental_condition = experimental_condition

    def create_rl_agent_socket(self, server_port: int):
        """
        Start a socket server to communicate with the RL agent.

        Args:
            server_port (int): The port number for the socket server.
        """
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
            server_socket.bind((self.server_ip, server_port))
            server_socket.listen(1)
            print(f"Agent Socket - Server listening on {self.server_ip}:{server_port}...")
            while True:
                self.rl_agent_socket, addr = server_socket.accept()
                self.rl_socket_connected = True
                Util.formatted_debug_message(f"Connection from {addr} (rl agent) has been established!", level='INFO')
                self.send_to_rl_agent({"id_player": self.id_player, "experimental_condition": self.experimental_condition})
                print(f"{'[INFO] Emitted id_player ({self.id_player}) to':<20}: RL application")
        except OSError as e:
            print(f"Socket error in RL agent socket: {e}")
        except Exception as e:
            print(f"Unexpected error in RL agent socket: {e}")

    def create_robot_socket(self, server_port: int):
        """
        Start a socket server to communicate with the robot.

        Args:
            server_port (int): The port number for the socket server.
        """
        try:
            s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s_socket.bind((self.server_ip, server_port))
            s_socket.listen(1)
            print(f"Robot Socket - Server listening on {self.server_ip}:{server_port}...")
            while True:
                self.robot_socket, addr = s_socket.accept()
                self.robot_socket_connected = True
                Util.formatted_debug_message(f"Connection from {addr} (robot) has been established!", level='INFO')
                self.send_to_robot({"id_player": self.id_player, "experimental_condition": self.experimental_condition})
                print(f"{']INFO] Emitted id_player ({self.id_player}) to':<20}: robot application")
        except OSError as e:
            print(f"Socket error in robot socket: {e}")
        except Exception as e:
            print(f"Unexpected error in robot socket: {e}")

    def send_to_rl_agent(self, data: dict):
        """Public method to send data to RL agent."""
        try:
            if self.rl_socket_connected and self.rl_agent_socket:
                json_data = json.dumps(data)
                self.rl_agent_socket.send(json_data.encode('utf-8'))
        except (ConnectionError, BrokenPipeError, OSError) as e:
            print(f"Error sending to RL agent: {e}")
            self.rl_socket_connected = False  # Mark as disconnected
        except (TypeError, ValueError) as e:
            print(f"JSON encoding error for RL agent: {e}")

    def send_to_robot(self, data: dict):
        """Public method to send data to robot application."""
        try:
            if self.robot_socket_connected and self.robot_socket:
                json_data = json.dumps(data)
                self.robot_socket.send(json_data.encode('utf-8'))
        except (ConnectionError, BrokenPipeError, OSError) as e:
            print(f"Error sending to robot: {e}")
            self.robot_socket_connected = False
        except (TypeError, ValueError) as e:
            print(f"JSON encoding error for robot: {e}")

    @property
    def is_rl_socket_connected(self):
        return self.rl_socket_connected

    @property
    def is_robot_connected(self):
        return self.robot_socket_connected

    def handle_rl_agent_exit(self):
        try:
            if self.rl_agent_socket:
                self.rl_agent_socket.close()
            self.rl_socket_connected = False
            Util.formatted_debug_message("Connection with RL agent closed...", level='INFO')
            # time.sleep(2)
        except Exception as e:
            print(f"Error closing RL agent socket: {e}")

    def handle_robot_exit(self):
        try:
            if self.robot_socket:
                self.robot_socket.close()
            self.robot_socket_connected = False
            Util.formatted_debug_message("Connection with robot closed...", level='INFO')
        except Exception as e:
            print(f"Error closing robot socket: {e}")
