from typing import Dict, List, Optional, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from util.util import Util

class GameManager:

    def __init__(self):
        self.experimental_condition = -1
        self.deck: Optional[Dict[str, str]] = None
        self.board: Optional[List[str]] = None
        self.board_integer: Optional[List[int]] = None
        self.board_cards_found = [None] * (Util.get_from_json_file("config")['pairs'] * 2)
        self.geography_cards = ["rome", "italy", "paris", "france", "madrid", "spain", "buenos_aires", "argentina"]
        self.math_cards = ["equation_1", "result_1", "equation_2", "result_2", "equation_3", "result_3", "equation_4", "result_4"]
        self.idx: Dict[str, int] = {}
        self.dictionary: Dict[str, Any] = {}
        self.N_ROWS = Util.get_from_json_file("config")['n_rows']
        self.N_COLS = Util.get_from_json_file("config")['n_cols']
        self.N_PAIRS = Util.get_from_json_file("config")['pairs']

    def set_experiemental_condition(self, value):
        self.experimental_condition = value
        
    def build_integer_board(self, shuffle: List[str]) -> List[int]:
        """
        Builds an integer representation of the shuffled board.

        This function creates a mapping from card names to integer indices based on the pairs dictionary,
        then returns the integer indices for the shuffled list of card names.

        Args:
            shuffle (List[str]): List of card names in shuffled order.

        Returns:
            List[int]: List of integer indices corresponding to the shuffled card names.
        """
        pairs = self.deck

        # Put in a list the ordered dictionary
        ordered = []
        for k, v in pairs.items():
            ordered.extend([k, v])

        # Get the index for each card
        idx = {name: i for i, name in enumerate(ordered)}

        # Save the index of each card
        self.idx = idx

        # Return the shuffle array with corresponding index
        return [idx[name] for name in shuffle]

    def print_board_as_matrix(self, game_board_list: List[str]):
        """Print the board as a matrix."""
        import numpy as np

        board = np.zeros((self.N_ROWS, self.N_COLS))
        board = np.reshape(game_board_list, (self.N_ROWS, self.N_COLS))
        board_str = [[str(x) for x in row] for row in board]
        mx = max(len(sub[0]) for sub in board_str) if board_str else 0

        for row in board:
            print(" ".join(["{:<{mx}}".format(ele, mx=mx) for ele in row]))

    def print_game_state(self):
        game_data = self.dictionary.get("game", {})
        subject = game_data.get("robot_subject", "")
        is_robot_turn = game_data.get('is_robot_turn', False)
        
        print(
            f"{'Turn':<20}: {game_data.get('turn', 'N/A')}\n"
            f"{'Token':<20}: {f'robot ({subject})' if is_robot_turn else 'human'}\n"
            f"{'Coordinates clicked':<20}: {game_data.get('position', 'N/A')}\n"
            f"{'Index board':<20}: {game_data.get('index', 'N/A')}\n"
            f"{'Card clicked':<20}: {game_data.get('open_card_name', 'N/A')}\n" 
            f"{'Card value clicked':<20}: {self.idx.get(game_data.get('open_card_name'), 'N/A')}\n"
            f"{'Pairs found':<20}: {game_data.get('pairs', 'N/A')}\n"
            f"{'Match':<20}: {game_data.get('match', 'N/A')}"
        )

        if self.experimental_condition in [1, 2]:
            print(f"{'Wrong card':<20}: {game_data.get('is_wrong_card', 'N/A')}")

    def _is_game_ended(self) -> bool:
        """Check if game is ended."""
        return self.dictionary.get("game", {}).get("pairs", 0) == self.N_PAIRS

    def is_human_turn(self) -> bool:
        """Check if human is playing."""
        return not self.dictionary.get("game", {}).get("is_robot_turn", False)

    def _handle_board_change(self, new_board: List[str]):
        """Handle board change."""
        # Update internal board
        self.board_integer = self.build_integer_board(new_board, self.deck)
        # Debug print
        print("\n" + "*" * 100)
        print("[INFO] BOARD CHANGED:\n")
        self.print_board_as_matrix(new_board)
        print("")
        self.print_board_as_matrix(self.board_integer)
        print("*" * 100, "\n")  

    def update_game_data(self, dictionary: Dict[str, Any]):
        """Update game dictionary."""
        self.dictionary = dictionary
