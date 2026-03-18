from dataclasses import dataclass, field
from functools import reduce
from typing import Callable, Iterable, Iterator, NamedTuple, TypeVar

import numpy as np
import math, random, pickle
import gymnasium as gym
from gymnasium import spaces

# General MDP utilities

class TimeStep(NamedTuple):
    state: object
    action: object
    next_state: object
    reward: float
    term: bool
    trunc: bool
    info: dict
    next_info: dict

    @property
    def done(self):
        return self.term or self.trunc

def steps(env: gym.Env, policy: Callable[[object], object]):
    term = True
    trunc = False
    i = 0
    while True:
        if term or trunc:
            print("\n" + "="*100)
            print("[RL] RESET")
            print("-"*100)
            state, info = env.reset()

        policy_state = policy.__self__
        policy_state.current_agent = env.current_agent_type
        print(f"[RL] {'':<10} {'Current agent:':<18} {policy_state.current_agent}")
        action = policy(state)
        print(f"[RL] {'':<10} {'Chosen action:':<18} {action} (0..7 C cards | 8 Random unseen | 9 Handover)")
        next_state, reward, term, trunc, next_info = env.step(action)
        i += 1
        yield TimeStep(state, action, next_state, reward, term, trunc, info, next_info)
        state = next_state
        info = next_info


@dataclass
class TabularQLearning:
    alpha: float = 0.1
    gamma: float = 0.9
    epsilon_schedule: Callable[[int], float] = lambda i: 0.1

    @staticmethod
    def decay_schedule(initial: float= 0.1, decay: float = 0.999):
        return lambda i: initial * decay**i
    
    @staticmethod
    def exponential_epsilon_decay(epsilon_start=1, epsilon_end=0.01, epsilon_decay=5000):
        return lambda i: epsilon_end + (epsilon_start - epsilon_end) * math.exp(-1. * i / epsilon_decay)

    @staticmethod
    def linear_schedule(initial: float = 0.1, final: float = 0.01, n: int = 10000):
        return lambda i: max(final, initial - i * (initial - final) / n)

    @dataclass
    class State:
        Q: dict                 # {"math": q_math, "geo": q_geo}
        steps: int
        algo: 'TabularQLearning'
        counter: int
        old_state: int
        old_action: int
        current_agent: str      # "math" | "geo"

        @property
        def q(self):
            return self.Q[self.current_agent]

        @property
        def epsilon(self):
            return self.algo.epsilon_schedule(self.steps)

        def best_action(self, s):
            print(f"[Q] {'':<11} {'Current agent:':<18} {self.current_agent}")

            # se viene visitato uno stato mai esplorato durante l'addestramento esegue handover
            if s not in self.q:
                first_key_of_q = next(iter(self.q))
                handover = len(self.q[first_key_of_q]) - 1
                print(f"[Q] {'':<11} {'State not in Q:':<18} {s} | Choosing action -> handover")
                return handover
                
            # sceglie casualmente una delle migliori azioni 
            best_action = np.random.choice(np.flatnonzero(self.q[s] == self.q[s].max()))
            print(f"[Q] {'':<11} {'State in Q:':<18} {s} | Best action: {best_action}")
            print(f"[Q] {'':11} {'Info (old):':<18} {self.counter} | {self.old_state} | {self.old_action}")

            if best_action == len(self.q[s]) - 1: # handover (dict)
            # if best_action == self.q.shape[1] - 1: # handover
                self.counter = 0
                return best_action
  
            if self.old_state == s and self.old_action == best_action:
                self.counter += 1
            
            self.old_state, self.old_action = s, best_action

            if self.counter == 3:
                best_action = len(self.q[s]) - 1 # handover (dict)
                # best_action = self.q.shape[1] - 1 # handover
                print(f"[Q] {'':<11} Detected loop, forcing handover action.")
                self.counter = 0
                self.old_state, self.old_action = None, None

            return best_action

        def epsilon_greedy_action(self, s):
            if np.random.rand() < self.epsilon:
                return np.random.choice(len(self.q[s]))
                # return np.random.choice(self.q.shape[1])
            return self.best_action(s)

    def run(self, env: gym.Env, q: np.ndarray | None = None) -> Iterator[State]:
        print(f"[Q] {'':<12} Initializing Q...")
        assert isinstance(env.observation_space, spaces.Discrete)
        assert isinstance(env.action_space, spaces.Discrete)

        # prende la matrice salvata
        if q is None:
            with open("q_math.pkl", "rb") as f:
                q_math = pickle.load(f)

            with open("q_geo.pkl", "rb") as f:
                q_geo = pickle.load(f)

        print(f"[Q] {'':<12} {'Loaded Q-math:':<18} {len(q_math.keys())}")
        print(f"[Q] {'':<12} {'Loaded Q-geo:':<18} {len(q_geo.keys())}")

        Q = {
            "math": q_math,
            "geography": q_geo
        }

        # inizializza lo stato dell'algoritmo (math: default - ma è irrilevante poichè l'utente può scegliere il tipo di agente all'inizio)
        algo_state = TabularQLearning.State(Q, 0, self, 0, None, None, 'math')
        
        # esegue l'algoritmo fino alla fine di un singolo episodio (i.e., la partita è finita)
        print(f"[Q] {'':<12} Running...")
        for i, ts in enumerate(steps(env, algo_state.best_action)):
            algo_state.steps = i

            algo_state.current_agent = env.current_agent_type
            print(f"[Q] {'':<11} {'Step:':<18} {i} | Agent: {algo_state.current_agent}\n")

            yield TabularQLearning.State(algo_state.Q.copy(), i, self, 0, None, None, algo_state.current_agent)

            if ts.done:
                print(f"[Q] {'':<11} Episode finished after {i+1} steps.")
                break
