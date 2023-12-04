"""
This file will hold an implementation of the DQN agent for the heads-up game of Durak.
"""
from typing import List

import torch
from torch import nn

from dataclasses import dataclass

from ..easy_agents import DurakPlayer
from two_game import num_actions, observable_state_shape, ObservableGameState, DurakAction
from .experience_replay import ExperienceReplay


@dataclass
class UpdateArgs:
    optimizer: torch.optim.Optimizer
    scheduler: torch.optim.lr_scheduler._LRScheduler
    loss_fn: nn.Module
    replay: ExperienceReplay
    batch_size: int  # number of updates to do per batch
    gamma: float  # discount factor used for TD error


class LSTMHistoryEncoder(nn.Module):
    """
    This class is responsible for generating a latent belief state from a history of observations using an LSTM
    to read through the history of observations and return the final hidden state of the LSTM as the latent belief.
    """

    def __init__(self, observation_shape: torch.Size, latent_dim: int):
        super().__init__()
        self.lstm = nn.LSTM(input_size=observation_shape[0], hidden_size=latent_dim)

    def forward(self, history: torch.Tensor) -> torch.Tensor:
        """
        This takes in a history of observations and returns the final hidden state of the LSTM.
        :param history: A tensor of shape [seq_len, *observation_shape] where seq_len is the length of the history
        :return: A tensor of shape [latent_dim] representing the latent belief state.
        """
        return self.lstm(history)[0][-1]


class QNetwork(nn.Module):
    """
    This class is responsible for taking a latent belief state and mapping it to Q-values across all actions.
    """

    def __init__(
        self, input_dim: int, n_actions: int, hidden_dim: int = 256, depth: int = 2
    ):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        layers = []
        for _ in range(depth - 2):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
        self.fc2 = nn.Linear(hidden_dim, n_actions)
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
        n_actions: int,
        state_shape: torch.Size,
        max_history_len: int = 512,  # could be used if we want to use a transformer instead of an LSTM
        latent_dim: int = 128,
        history_encoder_type: str = "LSTM",
        q_network_depth: int = 2,
    ):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_actions = n_actions
        self.state_shape = state_shape
        if history_encoder_type == "LSTM":
            self.history_encoder = LSTMHistoryEncoder(state_shape, latent_dim)
        else:
            raise NotImplementedError(f"Encoder type {encoder_type} not implemented")

        self.q_network = QNetwork(latent_dim, n_actions, depth=q_network_depth)

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
        DurakPlayer.__init__(self, player_id)
        nn.Module.__init__(self)

        self.agent = DQAgentWithHistory(
            num_actions(), torch.Size(observable_state_shape()), **agent_kwargs
        )
        self.epsilon = epsilon
        self.loss = nn.MSELoss()

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
        if self.training and torch.rand(1).item() < self.epsilon:  # epsilon greedy
            return actions[torch.randint(len(actions), (1,)).item()]

        arr = torch.stack([torch.from_numpy(state.to_array()).to(torch.float) for state in full_state])
        q_values = self.agent(arr.cuda())
        # we need to filter the q_values for only legal actions provided in the actions argument
        q_values = q_values[actions]
        return actions[q_values.argmax()]

    def update(self, update_args: UpdateArgs):
        """
        This updates the agent using the given experience replay. For stabilization,
        we will create a target network that is an exact copy of the current agent but
        does not propagate gradients. We will then use this target network to compute
        the target Q-values for the TD error.
        """
        optimizer = update_args.optimizer
        scheduler = update_args.scheduler
        experience_replay = update_args.replay
        num_iters = update_args.batch_size
        discount = update_args.gamma
        loss_fn = update_args.loss_fn

        target_dqn_agent = DQAgentWithHistory(
            num_actions(), torch.Size(observable_state_shape())
        )
        target_dqn_agent.load_state_dict(self.agent.state_dict())
        target_dqn_agent.eval().cuda()

        cum_loss = torch.tensor(0., requires_grad=True).cuda()

        optimizer.zero_grad()

        for _ in range(num_iters):

            s, a, r, s_prime = experience_replay.sample()
            s = torch.from_numpy(s).to(torch.float).cuda()
            a = torch.tensor(a).cuda()
            r = torch.tensor(r).cuda()
            s_prime = torch.from_numpy(s_prime).to(torch.float).cuda()

            q_values = self.agent(s)

            with torch.no_grad():
                next_q_values = target_dqn_agent(s_prime)

            q_values_prime_max = torch.max(next_q_values).item()
            td_target = r + discount * q_values_prime_max

            loss = loss_fn(q_values[a], td_target)  # minimize difference between calculated q-values and TD target

            cum_loss = cum_loss + loss
        print(f'Batch loss: {cum_loss.item()}')
        cum_loss.backward()
        optimizer.step()
        scheduler.step()
