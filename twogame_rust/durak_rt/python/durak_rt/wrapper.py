"""
This file is a wrapper around the raw output from py03 to add type hints 
and whatnot to the classes
"""
from typing import List
from durak_rt.rust import Card, GameEnv as _GameEnv, ObservableGameState


class GamePlayer:
    def choose_action(self, state: ObservableGameState, actions: List[str], history: List[ObservableGameState]) -> int:
        raise NotImplementedError("choose_action not implemented")


class GameEnv():
    def __init__(self, player: GamePlayer):
        self.env = _GameEnv(player)

    def play(self) -> (float, float):
        return self.env.play()

