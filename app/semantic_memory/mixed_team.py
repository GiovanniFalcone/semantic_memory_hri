import numpy as np
import gymnasium as gym
from gymnasium import spaces

import time, json

import rl
from semantic_memory_game import MemoryGame, MemoryGameEnv

# connessione con gioco e server
import signal
import json
import requests
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from util.util import Util

from socket import *
import time
import os

SERVER_IP = Util.get_from_json_file("config")['ip'] 
SERVER_PORT = int(Util.get_from_json_file("config")['port'])
SERVER_URL = f'http://{SERVER_IP}:{SERVER_PORT}'
IS_ROBOT_CONNECTED = Util.get_from_json_file("config")['HRI']

def connect_to_server(server_name, server_port):
    client_socket = socket(AF_INET, SOCK_STREAM) 
    connected = False
    while not connected:
        try:
            # connect socket to remote server at (serverName, serverPort)
            client_socket.connect((server_name, server_port))
            connected = True
        except Exception as e:
            print("catch exception: ", e)
    
    print(f"{'':<16} {'Connected to:':<18} {str(client_socket.getsockname())}")

    return client_socket
   
def receive_data_from_server(client_socket):
    """Receive data from server with timeout handling.
    
    Returns:
        dict: Parsed JSON data from server
        None: If socket timeout occurs (allows CTRL+C to be processed)
    """
    try:
        data = client_socket.recv(4096).decode()
        if data:
            return json.loads(data)
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Socket error: {e}")
        raise

def hamper_competence(card, category, competence, n_cards):
    print(f'[AI] {'':<11}{'Competence:':<18} card: {card} | category: {category} | competence: {competence} | n_cards: {n_cards}')
    if card in category:
        value = np.random.rand()
        print(f"{'':<15} Card in category is True: {value} < {competence}?")
        return card if value < competence else np.random.choice(n_cards)
        #return card if np.random.rand() < competence else np.random.choice(n_cards)
    return card

def map_action(action: int, n_cards: int, game_state) -> int:
    # 0..15 -> scopre una delle 16 carte
    # 16 -> scopre una carta a caso tra quelle non competenti
    # 17 handover
    # totale: 16 + 1 + 1 = 18 azioni

    # 0 .. 7 -> scopre una delle 8 carte in cui l'agente è competente
    # 8 -> scopre una carta tra quelle non competenti (se non viste sceglie random)
    # 9 -> scopre una carta a caso tra tutte le carte
    # 10 handover
    # totale: (16/2 + 1 carte) + 1 + 1 = 11 azioni

    if action == 9: 
        return 17 # handover

    # se l'azione è nei primi 4 indici allora l'azione sta dicendo di scoprire una delle carte in cui l'agente è competente
    if action in [0, 1, 2, 3]:
        return action
    
    # [C, C, C, C, C, C, C, C, NC] 0.. 8
    # [C, C, C, C, NC, NC, NC, NC, NC, NC, NC, NC, C, C, C, C] 0..15
    if action == 4:
        # 16 - 4 = azione 12
        return n_cards - 4
    
    elif action == 5:
        # 16 - 3 = azione 13
        return n_cards - 3
    
    elif action == 6:
        # 16 - 2 = azione 14
        return n_cards - 2
    
    elif action == 7:
        # 16 - 1 = azione 15
        return n_cards - 1
    
    elif action == 8:
        # random unseen
        return 16

class SemanticMemoryGameEnv(MemoryGameEnv):
    """
    Like MemoryGameEnv, but there is also:
    - a trust factor given as observation to the robot (discretized)
    - a second (human) player with a given policy and CTF for a single category (can be dynamically changed)
    - a handover action for both players to switch roles (a=N)
    
    When the human is playing, all their steps are condensed into a single step
    where the rewards are accumulated and given as a single value. If
    the human starts the episode and solves the game, the episode is skipped
    and a new one is started instead, until a non-empty episode is started. 

    This means that using a gamma < 1 will not work as if the agent was
    playing alone: we suggest setting gamma=1 and using a small negative
    reward for each step where no other reward is given, to still optimize
    for the shortest path to the goal.
    """

    @property
    def handover_action(self):
        return self.full_action_space.n-1

    def __init__(self, game: MemoryGame, ai_hampered_competence: float = 0, tf_levels: int = 3, max_steps=None, client_socket=None, human_ctf=None):
        super().__init__(game, max_steps)
        self.memory_game_states = self.observation_space.n
        self.observation_space = spaces.Discrete(self.memory_game_states * tf_levels)
        self.action_space = spaces.Discrete(1 + self.action_space.n)
        self.full_action_space = spaces.Discrete(1 + self.full_action_space.n)
        self.tf_levels = tf_levels
        self.ai_hampered_competence = ai_hampered_competence
        self.human_ctf = 0.2 if human_ctf == "low" else 1
        # debug info
        print(f"[SemanticMemory] {'Action space:':<18} {self.action_space}\n",
              f"                {'Observation space:':<15} {self.observation_space}\n",
              f"                {'Human ctf:':<18} {self.human_ctf}\n")
        ############ 
        # connection
        self.client_socket = client_socket
        self.id_player = -1
        self.experimental_condtion = -1

    def observe(self):
        return MemoryGameEnv.observe(self)

    def human_steps(self):
        print("\n" + "="*100)
        print("[Human] START")
        print("-"*100)
        # return value if human handover is immediate
        s, R, term, trunc, info = self.observe(), -2.0, False, False, {}
        print("")
        while True:
            print(f"[Human] {'':<7} {'Current state:':<18} {self.game_state}")
            print(f"[Human] {'':<7} Waiting...")
            data = receive_data_from_server(self.client_socket)
            print(f"[Human] {'':<7} {'Data:':<18} {data}")

            if "has_board_changed" in data:
                print(f"[Human] {'':<7} {'Board changed':<18} {data}")
                self.game_state.seen[self.game_state.seen == 1] = 0
                self.game_state = MemoryGame.State(
                    seen=self.game_state.seen,
                    face_up=0
                )
                s = self.observe()
                print(f"[Human] {'':<7} New state: {s}")
                continue

            if "id_player" in data:
                self.id_player = data.get('id_player')
                print(f"[Human] {'':<7} {'ID received':<18} {self.id_player}")
                self.experimental_condtion = data.get('experimental_condition')
                print(f"[Human] {'':<7} {'Condition received':<18} {self.experimental_condtion}\n")
                continue
            
            action = int(data.get('human_action'))
            print(f"[Human] {'':<7} {'Action:':<18} {action}")

            if action == self.handover_action:
                self.current_agent_type = data.get('robot_type')
                print(f'[Human] {"":<7} {'Handover to:':<18} AI({self.current_agent_type} type) \n')
                s = self.observe()
                print("="*100 + "\n")

                trunc = self.timed_out
                print("\n" + "="*100)
                print("[AI] START")
                print("-"*100)
                break

            s, r, term, trunc, info, _ = super().step(action, True)
            print("")
            R += r
            if term or trunc:
                print("="*100 + "\n")
                break
        return s, R, term, trunc, info

    def reset(self, seed=None, options=None):
        while True:
            # Reset and pick active player
            s, info = super().reset(seed, options)
            print(f"[SemanticMemoryGameEnv] {'':<10} Resetting done.")
            print("="*100 + "\n")
            human_starts = True
            # If AI starts, we are good
            if not human_starts:
                break
            # If human starts, we need to play their turn
            s, r, term, trunc, info = self.human_steps()
            # If the human didn't solve the game, we are good, otherwise we
            # start over
            if not (term or trunc):
                break
        # We can safely skip the reward that the human accumulated at reset
        # time, since it will provide no learning signal to an RL agent
        return s, info

    def step(self, action):
        print(f"[AI] {'':<10} {'Info:':<18} state: {self.game_state} | action: {action}")
        action = map_action(action, self.game.n_cards, self.game_state)
        print(f"[AI] {'':<10} {'Mapped action:':<18} {action}")

        if self.consecutive_agent_steps == 2:
            action = self.handover_action

        if action == self.handover_action:
            # AI hands over to human
            # wait a bit to simulate thinking time
            time.sleep(1)
            print(f'[AI] {"":<10} handover to Human\n')
            print("="*100 + "\n")

            self.steps += 1
            url = f'{SERVER_URL}/turn_change/{self.id_player}'
            json_data = {"turn": {"is_robot_turn": False, "robot_type": self.current_agent_type}}
            requests.post(url, json=json_data) 

            self.consecutive_agent_steps = 0
            s, *step = self.human_steps()
        else:
            human_competence = []
            if self.current_agent_type == "math":
                # human has geography competence
                human_competence = [5, 4, 7, 6, 9, 8, 10, 11]
            else:
                # human has math competence
                human_competence = [0, 1, 2, 3, 12, 13, 14, 15]

            action = hamper_competence(action, human_competence, self.ai_hampered_competence, self.game.n_cards)
            s, *step, is_card_invalid = super().step(action, False, self.experimental_condtion)

            card = self.game.second_face_up if self.game.second_turn else self.game_state[1]
            print(f"[AI] {'':<10} {'Card face up:':<18} {card} ({self.current_agent_type})")

            if not self.game.card_solved: # if card != 0 and not self.game.card_solved:
                card -= 1
                #card_index = np.where(self.game.shuffled == card)[0][0]
                #print(f"[AI] Index of card {card} of shuffled board is {card_index}")
                url = f'{SERVER_URL}/agent_move/{self.id_player}'
                json_data = {
                    "agent_move": {"action": int(card), 
                                   "robot_type": self.current_agent_type, 
                                   "is_wrong_card": self.game.wrong_card},
                } 
                requests.post(url, json=json_data)

                print(f"[AI] {'':<10} Waiting response...")
                data = receive_data_from_server(self.client_socket)

                print(f"[AI] {'':<10} {'Received data:':<18} {data}")
                if "has_board_changed" in data:
                    if data["has_board_changed"]:
                        print(f"[AI] {'':<10} {'Board changed:':<18} {data}")
                        self.game_state.seen[self.game_state.seen == 1] = 0
                        self.game_state = MemoryGame.State(
                            seen=self.game_state.seen,
                            face_up=0
                        )
                        print(f"[AI] {'':<10} {'New state:':<18} {self.game_state}")

                if IS_ROBOT_CONNECTED:
                    pass
                    # print(f"[AI] {'':<10} Waiting response from Robot...")
                    # data = receive_data_from_server(self.client_socket)
                    # print(f"[AI] {'':<10} {'Received data:':<18} {data}")
                
            step[3]['match'] = 1 if step[0] == 1.0 or step[0] == 100.0 else 0

            if step[0] != 100.0:
                if not is_card_invalid:
                    self.consecutive_agent_steps += 1
                    print(f"[AI] {'':<10} {'Consecutive steps:':<18} {self.consecutive_agent_steps}")
            else:
                self.consecutive_agent_steps = 0
        return s, *step


class TrustAwareSMGEnv(SemanticMemoryGameEnv):
    def __init__(self, game: MemoryGame, client_socket, ai_hampered_competence: float = 0, tf_levels: int = 3, max_steps=None):
        super().__init__(game, ai_hampered_competence, tf_levels, max_steps, client_socket, human_ctf)

    def reset(self, seed=None, options=None):
        s, info = super().reset(seed, options)
        return s, info


def get_make_env(env_id, client_socket, human_ctf):
    game = MemoryGame(np.array([1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14])) # 8 coppie

    if env_id == 'mixed_team_ctf':
        def make_env(client_socket):
            return TrustAwareSMGEnv(game, client_socket, human_ctf)
        return make_env

    raise ValueError(f'Unknown env_id: {env_id}')

def handle_exit(client_socket, id_player, *args):
    """
    Handle CTRL+C gracefully by closing the socket connection and notifying the server.
    
    Args:
        client_socket: The socket connection to the server
        id_player: The player ID to send in the exit request
        *args: Signal handler arguments (sig, frame)
    """
    print("\n" + "="*100)
    print("[INFO] CTRL+C Pressed!")
    print("-"*100)
    try:
        # Notify the server that RL agent is exiting
        url = f'{SERVER_URL}/rl_exit/{id_player}'
        json_data = {"connection": "close"}
        requests.post(url, json=json_data)
        print(f"[INFO] {'Notified server':<20}: RL agent exit")
    except Exception as e:
        print(f"[INFO] {'Error notifying server':<20}: {e}")
    
    try:
        # Close socket connection gracefully
        if client_socket:
            client_socket.close()
            print(f"[INFO] {'Socket closed':<20}: Success")
    except Exception as e:
        print(f"[INFO] {'Error closing socket':<20}: {e}")
    
    print("-"*100)
    print("[INFO] Exiting...\n")
    sys.exit(0)

def main(human_ctf):
    print("\n" + "="*100)
    print("[ENV] START")
    print("-"*100)

    ID_PLAYER = 1
    client_socket = connect_to_server(SERVER_IP, 9001)
    # handle CTRL+C with reference to client_socket and ID_PLAYER
    signal.signal(signal.SIGINT, lambda *args: handle_exit(client_socket, ID_PLAYER, *args))
    env_id = "mixed_team_ctf"
    make_env = get_make_env(env_id, client_socket, human_ctf)
    env = make_env(client_socket)

    n_steps = 400_000
    epsilon_schedule = rl.TabularQLearning.exponential_epsilon_decay(epsilon_start=1.0, epsilon_end=0.01, epsilon_decay=n_steps)
    algo = rl.TabularQLearning(
        alpha=0.2,
        gamma=0.99,
        epsilon_schedule=epsilon_schedule
    )

    for state in algo.run(env):
        pass

    # Notify server that RL agent is closing normally (training finished)
    try:
        url = f'{SERVER_URL}/rl_exit/{ID_PLAYER}'
        json_data = {"connection": "close"}
        requests.post(url, json=json_data)
        print(f"[INFO] {'Notified server':<20}: RL agent exit")
    except Exception as e:
        print(f"[INFO] {'Error notifying server':<20}: {e}")
    
    try:
        client_socket.close()
        print(f"[INFO] {'Socket closed':<20}: Success")
    except Exception as e:
        print(f"[INFO] {'Error closing socket':<20}: {e}")
    
    print("-"*100)
    return 


if __name__ == "__main__":
    import sys
    human_ctf = sys.argv[1] # "low" | "high"
    if human_ctf not in ["low", "high"]:
        print("Parameter must be 'low' or 'high'")
        sys.exit(0)
    main(human_ctf)
    sys.exit(0)

