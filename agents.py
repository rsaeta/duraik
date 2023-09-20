import pprint
from typing import List

import numpy as np

from game_state import ObservableDurakGameState
from actions import DurakAction


class DurakPlayer:

    def __init__(self, hand=None):
        self.hand = [] if hand is None else hand

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
        passable_cards = set()
        for s, r in self.hand:
            if r == rank:
                passable_cards.add((s, r))
        return passable_cards

    def choose_action(self, state: ObservableDurakGameState, actions: List[int]):
        raise NotImplementedError('Player must implement choose_action method')

    def __str__(self):
        return f"{self.__class__.__name__}({str(self.hand)})"

    def __repr__(self):
        return str(self)


class RandomPlayer(DurakPlayer):

    def __init__(self, hand=None):
        super().__init__(hand)
        self.np_random = np.random.RandomState()

    def choose_action(self, state, actions):
        return self.np_random.choice(actions)


class HumanPlayer(DurakPlayer):

    def choose_action(self, state, actions):
        print('State:')
        pprint.pprint(state)
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


def cards_to_input_array(cards: List[tuple]):
    """
    Converts a list of cards to a 1D array input for the neural network.
    To do so, it uses a many-hot encoding of the cards.
    :param cards: The cards to convert.
    :return: A 1D array of the cards.
    """
    card_ids = np.array([DurakAction.ext_from_card(card) for card in cards])
    num_cards = DurakAction.n(4)
    card_array = np.zeros(num_cards)
    card_array[card_ids] = 1
    return card_array


def state_to_input_array(state: ObservableDurakGameState):
    """
    Converts a state to a 1D array input for the neural network and saving for history.
    To do so,
    0-35: many-hot encoding of the hand
    36-71: many-hot encoding of the attack table
    72-107: many-hot encoding of the defend table
    108-143: many-hot encoding of the graveyard
    144-145: number of cards left in each opponent's hand
    146: number of cards left in the deck

    :param state: The state to convert.
    :return: A 1D array of the state.
    """
    hand_array = cards_to_input_array(state.hand)
    attack_table_array = cards_to_input_array(state.attack_table)
    defend_table_array = cards_to_input_array(state.defend_table)
    graveyard_array = cards_to_input_array(state.graveyard)
    opponents_cards_left_array = np.array(state.num_cards_left_in_opponent_hands)
    cards_left_in_deck_array = np.array([state.num_cards_left_in_deck])
    is_done = np.array([state.is_done])

    return np.concatenate((
        hand_array,
        attack_table_array,
        defend_table_array,
        graveyard_array,
        opponents_cards_left_array,
        cards_left_in_deck_array
    ))
