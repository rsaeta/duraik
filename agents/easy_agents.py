import pprint
from typing import List

import torch
from torch import nn

import numpy as np
from three_game import (ObservableDurakGameState, GameTransition, DurakAction)


class DurakPlayer:

    def __init__(self, player_id):
        self.player_id = player_id

    """
    def can_defend_with(self, card, trump_suit):
        suit, rank = card
        defensible_cards = []
        for s, r in self.hand:
            if s == suit and r > rank:
                defensible_cards.append((s, r))
            if s == trump_suit and suit != trump_suit:
                defensible_cards.append((s, r))
        return defensible_cards

    def can_pass_with(self, card):
        suit, rank = card
        passable_cards = set()
        for s, r in self.hand:
            if r == rank:
                passable_cards.add((s, r))
        return passable_cards
    """

    def choose_action(self, state: ObservableDurakGameState, actions: List[int]):
        raise NotImplementedError('Player must implement choose_action method')

    def update(self):
        pass

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return str(self)

    def observe(self, transition: GameTransition):
        pass


class RandomPlayer(DurakPlayer):

    def __init__(self, player_id):
        super().__init__(player_id)
        self.np_random = np.random.RandomState()

    def choose_action(self, state, actions):
        return actions[self.np_random.choice(len(actions))]


class HumanPlayer(DurakPlayer):

    def choose_action(self, state, actions):
        print('State:')
        pprint.pprint(state[-1])
        actions = sorted(actions)
        print('Actions: {}'.format(actions))
        action = -1
        while action not in range(len(actions)):
            try:
                action = int(input('Choose action: '))
            except ValueError:
                action = -1
            if action not in range(len(actions)):
                print('Invalid action {}'.format(action))
        return actions[action]

