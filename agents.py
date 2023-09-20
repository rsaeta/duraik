import pprint
from typing import List

import numpy as np

from main import ObservableDurakGameState
from actions import DurakAction


class DurakPlayer:

    def __init__(self, hand=None, np_random=None):
        self.hand = [] if hand is None else hand
        if np_random is None:
            self.np_random = np.random.RandomState()
        else:
            self.np_random = np_random

    def remove_card(self, card):
        if card not in self.hand:
            raise ValueError('Card {} not in hand {}'.format(card, self.hand))
        self.hand.remove(card)

    def add_card(self, card):
        self.hand.append(card)

    def can_defend_with(self, card, trump_suit):
        suit, rank = card
        defendable_cards = []
        for s, r in self.hand:
            if s == suit and r > rank:
                defendable_cards.append((s, r))
            if s == trump_suit and suit != trump_suit:
                defendable_cards.append((s, r))
        return defendable_cards

    def can_pass_with(self, card):
        suit, rank = card
        passable_cards = []
        for s, r in self.hand:
            if r == rank:
                passable_cards.append((s, r))
        return passable_cards

    def choose_action(self, state: ObservableDurakGameState, actions: List[int]):
        raise NotImplementedError('Player must implement choose_action method')

    def __str__(self):
        return f"{self.__class__.__name__}({str(self.hand)})"

    def __repr__(self):
        return str(self)


class RandomPlayer(DurakPlayer):

    def choose_action(self, state, actions):
        return self.np_random.choice(actions)


class HumanPlayer(DurakPlayer):

    def choose_action(self, state, actions):
        print('State:')
        pprint.pprint(state)
        print('Actions: {}'.format(list(map(DurakAction.action_to_string, actions))))
        action = int(input('Choose action: '))
        while action not in range(len(actions)):
            print('Invalid action {}'.format(action))
            action = int(input('Choose action: '))
        return actions[action]
