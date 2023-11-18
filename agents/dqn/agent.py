"""
This file will hold an implementation of the DQN agent for the heads-up game of Durak.
"""
from typing import List

import torch
from torch import nn

from ..easy_agents import DurakPlayer
from two_game import num_actions, observable_state_shape, ObservableGameState
from .experience_replay import ExperienceReplay


class LSTMHistoryEncoder(nn.Module):
    """
    This class is responsible for generating a latent belief state from a history of observations using an LSTM
    to read through the history of observations and return the final hidden state of the LSTM as the latent belief.
    """

    def __init__(self, observation_shape: torch.Size, latent_dim: int):
        super().__init__()
        self.lstm = nn.LSTM(input_size=observation_shape, hidden_size=latent_dim)

    def forward(self, history: torch.Tensor) -> torch.Tensor:
        """
        This takes in a history of observations and returns the final hidden state of the LSTM.
        :param history: A tensor of shape [seq_len, *observation_shape] where seq_len is the length of the history
        :return: A tensor of shape [latent_dim] representing the latent belief state.
        """
        return self.lstm(history)


class QNetwork(nn.Module):
    """
    This class is responsible for taking a latent belief state and mapping it to Q-values across all actions.
    """

    def __init__(
        self, input_dim: int, num_actions: int, hidden_dim: int = 256, depth: int = 2
    ):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        layers = []
        for _ in range(depth - 2):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
        self.fc2 = nn.Linear(hidden_dim, num_actions)
        self.network = nn.Sequential(self.fc1, nn.ReLU(), *layers, self.fc2)

    def forward(self, inpt: torch.Tensor) -> torch.Tensor:
        """
        This takes in a latent belief state and returns Q-values for all actions.
        :param inpt: A tensor of shape [latent_dim] representing the latent belief state.
        :return: A tensor of shape [num_actions] representing the Q-values for all actions.
        """
        return self.network(inpt)


class DQAgentWithHistory(nn.Module):

    """
    This class implements a DQN agent that encodes a history of observations into a latent belief state,
    from which it then maps to Q-values for all actions.
    """

    def __init__(
        self,
        num_actions: int,
        state_shape: torch.Size,
        max_history_len: int = 512,  # could be used if we want to use a transformer instead of an LSTM
        latent_dim: int = 128,
        history_encoder_type: str = "LSTM",
        q_network_depth: int = 2,
    ):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_actions = num_actions
        self.state_shape = state_shape
        if history_encoder_type == "LSTM":
            self.history_encoder = LSTMHistoryEncoder(state_shape, latent_dim)
        else:
            raise NotImplementedError(f"Encoder type {encoder_type} not implemented")

        self.q_network = QNetwork(latent_dim, num_actions, depth=q_network_depth)

    def forward(self, observation_history: torch.Tensor) -> torch.Tensor:
        """
        This takes in a history of observations and returns Q-values for all actions.
        :param observation_history: A tensor of shape [seq_len, *observation_shape] where seq_len is the length of the
        history.

        :return: A tensor of shape [num_actions] representing the Q-values for all actions.
        """
        latent_belief = self.history_encoder(observation_history)
        return self.q_network(latent_belief)


class DQNPlayer(DurakPlayer, nn.Module):
    """
    This is the class wrapping the above agent in a DurakPlayer implementation. It is epsilon greedy.
    """

    def __init__(self, player_id, epsilon: float = 0.1, **agent_kwargs):
        super(DurakPlayer, self).__init__(player_id)
        super(nn.Module, self).__init__()

        self.agent = DQAgentWithHistory(
            num_actions(), torch.Size(observable_state_shape()), **agent_kwargs
        )
        self.epsilon = epsilon

    def choose_action(
        self,
        current_state: ObservableGameState,
        actions: List[DurakAction],
        full_state: List[ObservableGameState] = None,
    ) -> DurakAction:
        """
        This takes in a history of states and a list of actions and returns the action to take.

        :param current_state: The current state of the game.
        :param actions: The list of actions to choose from.
        :param full_state: The full state history of the game.
        :return: The action to take.
        """
        if self.training and torch.rand() < self.epsilon:  # epsilon greedy
            return actions[torch.randint(len(actions), (1,)).item()]

        arr = torch.stack([state.to_array() for state in full_state])
        q_values = self.agent(arr)
        # we need to filter the q_values for only legal actions provided in the actions argument
        q_values = q_values[actions]
        return actions[q_values.argmax()]
