import mcts_simple
from .easy_agents import RandomPlayer
from three_game import DurakGame, DurakAction

from typing import List


class MCTSGame(DurakGame, mcts_simple.Game):

    def __init__(self):
        super().__init__()
        self.configure({
            'game_num_players': 2,
            'lowest_card': 6,
            'agents': [RandomPlayer]*3,
        })
        self.init_game()

    def current_player(self) -> int:
        return self.player_taking_action

    def get_state(self):
        return self.get_whole_state()

    def get_actions(self):
        return self.get_legal_actions(self.current_player())

    def render(self):
        return self.get_whole_state()

    def number_of_players(self) -> int:
        return self.num_players

    def take_action(self, action_id: int) -> None:
        player_id = self.player_taking_action
        print(f'Player {player_id} taking action {DurakAction.action_to_string(action_id)}')
        transition = self._do_step(player_id, action_id)
        print(transition)

    def has_outcome(self) -> bool:
        return self.is_done

    def winner(self) -> List[int]:
        return [i for i in range(self.num_players) if len(self.players[i].hand) == 0]

    def possible_actions(self) -> List[int]:
        return self.get_legal_actions(self.current_player())
