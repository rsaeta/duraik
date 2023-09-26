import torch
from torch import nn
from typing import Collection, Tuple
import numpy as np
from game import DurakAction, ObservableDurakGameState, GameTransition
from .easy_agents import DurakPlayer


def cards_to_input_array(cards: Collection[tuple]):
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
    """
    Predictive module mapping state representations to Q-values for each action.
    """
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


class ExperienceReplay:
    """
    Class to hold experiences of SARS tuples in an efficient and easily retrievable manner to be used by the DQ Agent.
    """
    def __init__(self, memory_size, input_dim, n_actions):
        self.memory_size = memory_size
        self.memory_counter = 0
        self.states = np.zeros((memory_size, input_dim), dtype=np.int32)
        # Need to store the legal actions available for us to properly mask the predicted q-values in our update step
        self.legal_actions = np.zeros((memory_size, n_actions), dtype=np.bool_)
        self.new_states = np.zeros((memory_size, input_dim), dtype=np.int32)
        self.actions = np.zeros(memory_size, dtype=np.int32)
        self.rewards = np.zeros(memory_size, dtype=np.float32)
        self.terminal = np.zeros(memory_size, dtype=np.bool_)

    def add_experience(self, transition: GameTransition):
        i = self.memory_counter % self.memory_size
        self.states[i] = state_to_input_array(transition.state)
        self.new_states[i] = state_to_input_array(transition.next_state)
        self.actions[i] = transition.action
        self.rewards[i] = transition.reward
        self.terminal[i] = transition.next_state.is_done
        self.legal_actions[i, transition.state.available_actions] = True
        self.memory_counter += 1

    def sample(self) -> Tuple[np.array, np.array, np.array, np.array, np.array, np.array]:
        i = np.random.choice(self.memory_counter) % self.memory_size
        return (self.states[i],
                self.legal_actions[i],
                self.actions[i],
                self.rewards[i],
                self.new_states[i],
                self.terminal[i])


class DQAgent(nn.Module, DurakPlayer):
    """
    The actual agent using experience replay and a deep q network to learn how to play any game (?).
    """
    def __init__(self, input_dim, n_actions, hidden_dims=None, memory_size=10000, batch_size=32, gamma=0.99, eps=0.1):
        super().__init__()
        self.dqn = DQN(input_dim, n_actions, hidden_dims)

        self.target_dqn = DQN(input_dim, n_actions, hidden_dims)
        self.target_dqn.load_state_dict(self.dqn.state_dict())

        self.memory = ExperienceReplay(memory_size, input_dim, n_actions)
        self.eps = eps
        self.gamma = gamma

        self.loss = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.dqn.parameters())

    def forward(self, x):
        return self.dqn(x)

    def observe(self, transition: GameTransition):
        self.memory.add_experience(transition)

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

    @staticmethod
    def calc_target_params(target_sd, source_sd, eps):
        """
        Calculates an exponential moving average of the target network parameters.
        """
        return {k: eps * source_sd[k] + (1 - eps) * target_sd[k] for k in target_sd.keys()}

    def update(self):
        """
        Performs optimization through experience replay. We will sample our memory for a batch of experiences,
        and optimize according to the loss function:
        """
        experience = tuple(map(lambda x: torch.from_numpy(x), self.memory.sample()))
        state, legal_actions, action, reward, new_state, terminal = experience
        # Use target network to get target q-values without computing or storing gradients
        with torch.no_grad():
            self.target_dqn.eval()
            target_q_value = self.target_dqn(new_state)
            max_q_value = target_q_value.max(dim=1)[0]
        true_q_values = reward + self.gamma * max_q_value

        # Use main network to get predicted q-values and mask out illegal actions
        self.dqn.train()
        predicted_q_values = self.dqn(state)
        predicted_q_values = torch.gather(predicted_q_values, 1, action.unsqueeze(1)).squeeze(1)

        # Gradient calculation and propagation
        loss = self.loss(predicted_q_values, true_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update target network
        new_dqn_sd = self.dqn.state_dict()
        target_sd = self.target_dqn.state_dict()
        self.target_dqn.load_state_dict(self.calc_target_params(target_sd, new_dqn_sd, self.eps))
        