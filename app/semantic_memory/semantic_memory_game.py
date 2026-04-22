from dataclasses import dataclass, field
from enum import IntEnum
from functools import reduce
from logging import warning
from typing import Iterable, Iterator, NamedTuple

import numpy as np
import pygame
import gymnasium as gym
from gymnasium import spaces



@dataclass
class MemoryGame:
    class CardState(IntEnum):
        UNSEEN = 0 # card was never seen (position is unknown)
        SEEN = 1 # card was seen (position is known)
        SOLVED = 2 # card is solved (face up and matched correctly)

    class State(NamedTuple):
        seen: np.ndarray[int] # one CardState per card
        face_up: int # 0 for no card face up, 1..N for card i-1 face up temporarily

        def copy(self):
            return MemoryGame.State(seen=self.seen.copy(), face_up=self.face_up)

        def __eq__(self, other: 'MemoryGame.State') -> bool:
            return (self.seen == other.seen).all() and self.face_up == other.face_up

        @property
        def n_solved(self) -> int:
            return np.sum(self.seen == MemoryGame.CardState.SOLVED)

        @property
        def solved(self) -> bool:
            return (self.seen == MemoryGame.CardState.SOLVED).all()
   
    oracle: np.ndarray[int] # for each card, the card it matches with

    @property
    def n_cards(self) -> int:
        return len(self.oracle)

    def __post_init__(self):
        if len(self.oracle.shape) != 1:
            raise ValueError("Oracle must be a 1D array")
        if len(np.unique(self.oracle)) != len(self.oracle):
            raise ValueError("Each card must have a unique match")

    def reset(self, seed=None) -> State:
        print(f"[MemoryGame] {'':<21} Resetting game")
        return MemoryGame.State(np.full(self.n_cards, MemoryGame.CardState.UNSEEN), 0)

    def step(self, state: State, action: int, human_action: bool = False, experimental_condition: int = 0) -> State:
        flag_random_action = 0

        seen, face_up = state
        # var aggiunta per capire se è il turno in cui si sta scoprendo la seconda carta (serve solo per il robot)
        self.second_turn = False

        if state.solved:
            # Game is over (all cards are solved)
            print(f'[MemoryGame] All cards are solved\n')
            return state.copy(), True
        
        # se è l'umano a giocatore l'azione 8 (scegli una carta a caso) è inutile
        # nel caso reale, l'umano sceglie la carta coperta dal tabellone già a caso (almeno inizialmente)
        # non ci sono controlli perchè nell'ui se clicca una carta scoperta non succede nulla
        if human_action:
            return self.turn_face_up(state, action), None

        # se il tabellone è composto solo da carte seen l'azione random diventa valida (scoprirà carte seen)
        if action == self.n_cards and np.all((seen == MemoryGame.CardState.SOLVED) | (seen == MemoryGame.CardState.SEEN)):
            print(f'[MemoryGame] {'':<2} All cards have been seen o solved')
            flag_random_action = 1
        elif action == (face_up-1) or action < self.n_cards and seen[action] in {MemoryGame.CardState.SOLVED, MemoryGame.CardState.UNSEEN}:
            # Do nothing (invalid action)
            print(f'[MemoryGame] {'':<2} Card {action} is unseen or solved')
            self.card_solved = True
            return state.copy(), True
        
        # se la condizione sperimentale non è quella in cui il robot è competente
        # allora deve sbagliare la carta qualora non sia stata scoperta randomicamente
        flag_condition = None
        if experimental_condition == 0 or action == self.n_cards:
            flag_condition = 0
        else:
            flag_condition = 1

        # Action is valid: turn card face up
        self.card_solved = False
        if action == self.n_cards and flag_random_action == 0:
            # Choose a random unseen card
            unseen_cards = np.where(seen == MemoryGame.CardState.UNSEEN)[0]
            if len(unseen_cards) == 0:
                # No unseen cards left, invalid action
                print(f'[MemoryGame] {'':<2} No unseen cards left to turn face up')
                return state.copy(), True
            action = np.random.choice(unseen_cards)
            print(f'[MemoryGame] {'':<2} {'Choosing random:':<18} {action} (unseen card)')
        elif action == self.n_cards and flag_random_action == 1:
            # Choose a random seen card
            seen_cards = np.where(seen == MemoryGame.CardState.SEEN)[0]
            if len(seen_cards) == 0:
                # No unseen cards left, invalid action
                print(f'[MemoryGame] {'':<2} No seen cards left to turn face up')
                return state.copy(), True
            action = np.random.choice(seen_cards)
            print(f'[MemoryGame] {'':<2} {'Choosing random:':<18} {action} (seen card)')

        return self.turn_face_up(state, action, flag_condition), False

    def get_random_card(self, state: State, current_card, matching_card):
        seen, _ = state
        print(f'[MemoryGame] {'':<2} {'Pair is:':<18} {matching_card} | {current_card}')
        # sceglie una qualsiasi carta non risolta
        available_cards = np.where(seen != MemoryGame.CardState.SOLVED)[0]
        # rimuove la carta attualmente scoperta e quella che fa match, in modo da sbagliare sicuramenet
        filtered = list(set(available_cards) - {current_card, matching_card})
        print(f'[MemoryGame] {'':<2} {'Available cards:':<18} {filtered}')

        # sceglie una a caso
        return np.random.choice(filtered)

    def turn_face_up(self, state: State, card: int, flag_condition: int = 0) -> State:
        seen, face_up = state
        assert seen[card] != MemoryGame.CardState.SOLVED

        self.wrong_card = False

        next_seen, next_face_up = state.copy()
        # Mark the card to be turned face up as seen
        # print(f'[Game] Turning card {card} face up')
        next_seen[card] = MemoryGame.CardState.SEEN

        # If there is no face up card, turn this card face up
        if face_up == 0:
            # print(f'[Game] No other card face up, turning card {card} face up')
            next_face_up = card + 1
            return MemoryGame.State(next_seen, next_face_up)

        # If there are two face up cards, check if they match
        assert seen[face_up-1] == MemoryGame.CardState.SEEN
        print(f"[MemoryGame] {'':<3}{'Comparing:':<18} {face_up-1} and {card}...")
        self.second_turn = True
        # in modo da memorizzare l'ultima carta scoperta -> senza di essa face_up = 0 perchè la coppia è stata coperta
        self.second_face_up = card + 1
        if self.oracle[face_up-1] == card:
            print(f'[MemoryGame] {'':<3}Cards {face_up-1} and {card} match')
            if flag_condition == 0:
                next_seen[face_up-1] = next_seen[card] = MemoryGame.CardState.SOLVED
                print(f"[MemoryGame] {'':<3}Match found!")
            else:
                # scegli random fra una delle carte viste o non viste
                wrong_card = self.get_random_card(state, card, face_up - 1)
                print(f"[MemoryGame] {'':<3}Provide wrong card (card: {wrong_card})!")
                self.second_face_up = wrong_card + 1
                self.wrong_card = True
        next_face_up = 0
        return MemoryGame.State(next_seen, next_face_up)

    def have_new_match(self, state: State, next_state: State) -> bool:
        # number of solved cards increased
        return next_state.n_solved > state.n_solved


class MemoryGameEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, game: MemoryGame, max_steps=None):
        self.game = game
        max_consecutive = 2 # 0 gioca, 1 potrebbe giocare, 2 deve passare
        N = self.game.n_cards

        n_competent = N // 2
        self.max_steps = max_steps if max_steps is not None else 2**(n_competent) # or n_competent + 1
        # Nuovo: aggrego anche le competenti -> al posto di 8 valori, ne abbiamo 4, ossia le coppie e non le singole carte 
        # Ogni coppia può essere in 4 stati: [Sconosciuta, 1 Vista, 2 Viste, Risolta]
        n_pairs = n_competent // 2 # 4 coppie
        state_combination = (4**n_pairs) * 2 # 2 è lo stato della NC (0 o 1)
        face_up = N//2 + 1 + 1 # 0 nessuna, 1..N//2 carte competenti, N//2+1 almeno una non competente = 16/2 + 1 + 1 = 10
        self.observation_space = spaces.Discrete(face_up * state_combination * max_consecutive)
        self.action_space = spaces.Discrete(1 + n_competent)

        # per mappare l'handover
        self.full_action_space = spaces.Discrete(1 + N)
        self.game_state = None
        self.steps = None
        self.consecutive_agent_steps = 0
        self.current_player = None # 0 = agent, 1 = opponent
        self.current_agent_type = 'math'  # "math" | "geo"

        print(f"[MemoryGameEnv]  {'N_cards:':<18} {N}\n",
              f"                {'Space:':<18} {self.observation_space}\n",
              f"                {'Actions:':<18} {self.action_space}\n",
              f"                {'Max steps:':<18} {self.max_steps}\n",
              f"                {'Actions (human):':<18} 0..15 (cards) | 16 (not used) | 17 (handover)\n")
        

    def map_face_up(self, face_up, competent_indices, non_competent_indices):
        if face_up - 1 in competent_indices:
            return competent_indices.index(face_up - 1) + 1
        elif face_up - 1 in non_competent_indices:
            N = self.game.n_cards
            return N//2 + 1
        else:
            return 0  # nessuna carta scoperta
    
    def observe(self):
        N = self.game.n_cards
        my_n = N//2 + 1
        
        competent_indices = []
        non_competent_indices = []

        if self.current_agent_type == 'math':
            # agent competence
            competent_indices = [0, 1, 2, 3, 12, 13, 14, 15]
            # human competence
            non_competent_indices = [4, 5, 6, 7, 8, 9, 10]
        else:
            # agent competence
            competent_indices = [4, 5, 6, 7, 8, 9, 10, 11]
            non_competent_indices = [0, 1, 2, 3, 12, 13, 14, 15] 

        N = self.game.n_cards
        # my_n = N // 2 + 1
        # adesso ho [C1, C2, C3, C4, NC] dove C1..C4 sono le coppie di carte competenti (0-1, 2-3, 12-13, 14-15) e NC è l'aggregazione delle non competenti
        n_pairs = (N // 2) // 2 # 16/2 = 8 carte competenti -> 8/2 = 4 coppie
        my_n = n_pairs + 1  # 14 coppie + 1 aggregazione non competenti = 5 
        seen = np.zeros(my_n, dtype=int)

        pair_status = []
        for i in range(0, N//2, 2): # N // 2 = 8 carte competenti
            # prendo le coppie (0, 1), (2, 3), (12, 13), (14, 15) 
            a, b = competent_indices[i], competent_indices[i+1]
            # vedo se sono sconosciute (0), una vista (1), entrambe viste (2) o risolte (3)
            s_a, s_b = self.game_state.seen[a], self.game_state.seen[b]
            if s_a == 2 and s_b == 2:   val = 3         # Risolta
            elif s_a >= 1 and s_b >= 1: val = 2         # Entrambe viste
            elif s_a >= 1 or s_b >= 1:  val = 1         # Una vista
            else:                       val = 0         # Ignote
            pair_status.append(val)

        # 4 coppie competenti  
        seen[:my_n - 1] = pair_status

        # 5 carta aggregata per le non competenti 
        # - 0 se c'è almeno una carta mai vista (stato 0)
        # - 1 se tutte sono state almeno viste (stato 1) o risolte (stato 2)
        any_unknown_non_comp = np.any(self.game_state.seen[non_competent_indices] == 0)
        seen[my_n - 1] = 1 if not any_unknown_non_comp else 0 

        # 0 -> nessuna carta scoperta
        # 1 .. 8 -> carte competenti scoperte
        # 9 -> almeno una carta non competente scoperta
        face_up = self.map_face_up(self.game_state.face_up, competent_indices, non_competent_indices)
        
        # 1. Calcolo il valore delle 4 coppie di carte competenti in base 4 (0, 1, 2, 3)
        competent_part = (4**np.arange(n_pairs) * pair_status).sum()

        # 2. Aggiungo il valore della carta aggregata delle non competenti (0 o 1)
        cards_state = (competent_part * 2) + seen[my_n - 1]

        # 3. Aggiungo il valore di face_up (0..9)
        state_combination = (4**n_pairs) * 2
        old_state = face_up * (state_combination) + cards_state 

        # Infine aggiungiamo la variabile 'consecutive' (0, 1, 2)
        # Moltiplichiamo old_state per 3 (stati di consecutive) e aggiungiamo il valore
        consecutive = min(self.consecutive_agent_steps, 2)
        new_state = (old_state * 2) + consecutive

        # debug
        print(f"[MemoryGameEnv] {'Agent type:':<18} {self.current_agent_type}")
        print(f"[MemoryGameEnv] {'My seen:':<18} {seen} | face up = {face_up}")
        print(f"[MemoryGameEnv] {'State:':<18} {new_state}")
        
        return new_state

    def reward(self, s, s1):
        if s1.solved:
            # print("SOLVED")
            return 100.0
        if self.game.have_new_match(s, s1):
            # print("MATCH")
            return 1.0
        # print("NO MATCH")
        return -1.0

    @property
    def timed_out(self):
        return self.steps >= self.max_steps

    def reset(self, seed=None, options=None):
        # print(f'[env] reset')
        self.game_state = self.game.reset()
        self.steps = 0
        self.n_matches = 0
        # print(f'[GAME] END RESET')
        return self.observe(), {}

    def step(self, action, human_action: bool = False, experimental_condition: int = 0):
        # print("[MemoryGameEnv] Taking action:", action)
        last_state = self.game_state
        # print(f'[env] last_state is None: {last_state is None}')
        self.game_state, is_card_invalid = self.game.step(self.game_state, action, human_action, experimental_condition)
        self.steps += 1
        term = self.game_state.solved
        if self.game.have_new_match(last_state, self.game_state):
            self.n_matches += 1
        assert not term or self.n_matches == self.game.n_cards // 2
        return self.observe(), self.reward(last_state, self.game_state), term, self.timed_out, {}, is_card_invalid


