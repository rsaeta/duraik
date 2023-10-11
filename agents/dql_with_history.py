import torch
from torch import nn
from typing import List
import numpy as np

from game import InfoState, GameTransition, DurakAction
from .easy_agents import DurakPlayer
from .dql import state_to_input_array, ExperienceReplay, one_hot

"""
This will use the new info-state created that incorporates a history of information states in the 
current state. We will use some kind of sequence-processing architecture to generate a representation
of the current history, and then generate q-values based on the history representation and the current
state representation. This will hopefully allow the model to remember where cards are and act more 
intelligently. 
"""


class QNet(nn.Module):

    def __init__(self, history_size, state_size, n_actions, hidden_size=64):
        super().__init__()
        self.ff = nn.Sequential(nn.Linear(history_size+state_size, hidden_size),
                                nn.ReLU(),
                                nn.Linear(hidden_size, hidden_size),
                                nn.ReLU(),
                                nn.Linear(hidden_size, hidden_size),
                                nn.ReLU())

        self.out = nn.Linear(hidden_size, n_actions)

    def forward(self, history, state):
        x = torch.cat((history, state), dim=-1)
        x = self.ff(x)
        return self.out(x)


class DQN(nn.Module):
    def __init__(self,
                 history_dim: int,
                 history_rep_size: int,
                 state_rep_size: int,
                 n_actions: int,
                 hidden_size: int = 64,):
        super().__init__()
        self.history = nn.LSTM(history_dim, history_rep_size, num_layers=3)
        self.qnet = QNet(history_rep_size, state_rep_size, n_actions, hidden_size)

    def forward(self, history, state):
        history_rep = self.history(history)
        return self.qnet(history_rep, state)



class DQAgentWithHistory(DurakPlayer, nn.Module):

    def __init__(self,
                 player_id,
                 hand,
                 history_dim: int,
                 history_rep_size: int,
                 state_rep_size: int,
                 n_actions: int,
                 hidden_size: int = 64,
                 eps: float = 0.1):
        DurakPlayer.__init__(self, player_id, hand)
        nn.Module.__init__(self)
        self.net = DQN(history_dim, history_rep_size, state_rep_size, n_actions, hidden_size)
        self.eps = eps
        self.replay_history = ExperienceReplay(10000, state_rep_size*100)
        self.prev_state = None
        self.optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        self.loss = torch.nn.MSELoss()
        self.target_net = DQN(history_dim, history_rep_size, state_rep_size, n_actions, hidden_size)
        self.target_net.load_state_dict(self.net.state_dict())

    def forward(self, history, state):
        return self.net(history, state)

    def choose_action(self, info_state: InfoState, actions: List[int]):
        if self.prev_state is None:
            self.prev_state = info_state.full_state
        if torch.rand() < self.eps:
            return np.random.choice(actions)
        cur_state_rep = torch.from_numpy(state_to_input_array(info_state.current_state))
        history_arrs = torch.stack([torch.from_numpy(state_to_input_array(s)) for s in info_state.full_state])
        q_values = self(history_arrs, cur_state_rep)
        legal_q_values = q_values[actions]
        return actions[torch.argmax(legal_q_values).item()]

    def observe(self, transition: GameTransition):
        if transition.state.current_state.acting_player != self.player_id and transition.reward == 0:
            return
        self.replay_history.add_experience(GameTransition(self.prev_state,
                                                          transition.action,
                                                          transition.reward,
                                                          transition.next_state))
        self.prev_state = transition.next_state

    def update(self):
        running_loss = 0.
        for i in range(100):
            batch = tuple(map(lambda x: torch.from_numpy(x).to(self.device), self.replay_history.sample(32)))
            state, action, reward, new_state, terminal = batch
            state = state.float()
            new_state = new_state.float()
            action = one_hot(action.to(torch.int64), DurakAction.num_actions())
            reward = reward.float()

            with torch.no_grad():
                self.target_net.eval()
                target_q_values = self.target_net(new_state[:, :-1], new_state[:, -1])
