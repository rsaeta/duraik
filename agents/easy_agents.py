import pprint
from typing import List

import numpy as np
from game import (ObservableDurakGameState, GameTransition, DurakAction, InfoState)


class DurakPlayer:

    def __init__(self, player_id, hand=None):
        self.player_id = player_id
        self.hand = [] if hand is None else hand

    def remove_card(self, card):
        if card not in self.hand:
            raise ValueError('Card {} not in hand {}'.format(card, self.hand))
        self.hand.remove(card)

    def add_card(self, card):
        self.hand.append(card)

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

    def choose_action(self, info_state: InfoState, actions: List[int]):
        raise NotImplementedError('Player must implement choose_action method')

    def update(self):
        pass

    def __str__(self):
        return f"{self.__class__.__name__}({str(self.hand)})"

    def __repr__(self):
        return str(self)

    def observe(self, transition: GameTransition):
        pass


class RandomPlayer(DurakPlayer):

    def __init__(self, player_id, hand=None):
        super().__init__(player_id, hand=hand)
        self.np_random = np.random.RandomState()

    def choose_action(self, state, actions):
        return self.np_random.choice(actions)


class HumanPlayer(DurakPlayer):

    def choose_action(self, info_state: InfoState, actions):
        print('State:')
        pprint.pprint(info_state.current_state)
        print('Actions: {}'.format(list(map(DurakAction.action_to_string, actions))))
        action = -1
        while action not in range(len(actions)):
            try:
                action = int(input('Choose action: '))
            except ValueError:
                action = -1
            if action not in range(len(actions)):
                print('Invalid action {}'.format(action))
        return actions[action]

