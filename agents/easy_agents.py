import pprint
from typing import List

import torch
from torch import nn

import numpy as np
from game import (ObservableDurakGameState, GameTransition, DurakAction)


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

    def choose_action(self, state: ObservableDurakGameState, actions: List[int]):
        raise NotImplementedError('Player must implement choose_action method')

    def __str__(self):
        return f"{self.__class__.__name__}({str(self.hand)})"

    def __repr__(self):
        return str(self)

    def observe(self, transition: GameTransition):
        pass


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
    player_id = np.array([state.player_id])
    hand_array = cards_to_input_array(state.hand)
    attack_table_array = cards_to_input_array(state.attack_table)
    defend_table_array = cards_to_input_array(state.defend_table)
    graveyard_array = cards_to_input_array(state.graveyard)
    opponents_cards_left_array = np.array(state.num_cards_in_hands)
    cards_left_in_deck_array = np.array([state.num_cards_left_in_deck])
    is_done = np.array([state.is_done])

    return np.concatenate((
        player_id,
        hand_array,
        attack_table_array,
        defend_table_array,
        graveyard_array,
        opponents_cards_left_array,
        cards_left_in_deck_array,
        is_done,
    ))


class DQN(nn.Module):

    def __init__(self, n_input, n_actions, hidden_dims=None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [256, 256, 256]
        hidden_layers = []
        cur_dim = n_input
        for dim in hidden_dims:
            hidden_layers.append(nn.Linear(cur_dim, dim))
            hidden_layers.append(nn.ReLU())
            cur_dim = dim
        self.ff = nn.Sequential(*hidden_layers)
        self.out = nn.Linear(cur_dim, n_actions)

    def forward(self, x):
        y = self.ff(x)
        return self.out(y)


class DQAgent(nn.Module):

    def __init__(self, input_dim, n_actions, hidden_dims=None, memory_size=10000, batch_size=32, gamma=0.99, eps=0.1):
        super().__init__()
        self.dqn = DQN(input_dim, n_actions, hidden_dims)
        self.max_mem = memory_size
        self.state_memory = np.zeros((memory_size, input_dim), dtype=np.float32)
        self.new_state_memory = np.zeros((memory_size, input_dim), dtype=np.float32)
        self.action_memory = np.zeros(memory_size, dtype=np.int32)
        self.reward_memory = np.zeros(memory_size, dtype=np.float32)
        self.terminal_memory = np.zeros(memory_size, dtype=np.bool)
        self.mem_counter = 0
        self.eps = eps

    def forward(self, x):
        return self.dqn(x)

    def store_transition(self, state, action, reward, new_state, done):
        """
        Stores a SARSA transition in memory.
        """
        index = self.mem_counter % self.max_mem
        self.state_memory[index] = state
        self.new_state_memory[index] = new_state
        self.action_memory[index] = action
        self.reward_memory[index] = reward
        self.terminal_memory[index] = done
        self.mem_counter += 1

    def choose_action(self, state, legal_actions):
        if np.random.random() > self.eps:
            state_array = state_to_input_array(state)
            state_tensor = torch.from_numpy(state_array).float()
            q_values = self.forward(state_tensor)  # Gets us all Q-values for even illegal actions
            q_values = q_values[legal_actions]  # Gets us Q-values for legal actions
            action = torch.argmax(q_values).item()
        else:
            action = np.random.choice(legal_actions)
        return action

