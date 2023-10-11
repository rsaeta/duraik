import torch
from numpy import ndarray
from torch import nn
from typing import Collection, Tuple
import numpy as np
from game import DurakAction, ObservableDurakGameState, GameTransition, InfoState
from .easy_agents import DurakPlayer


def cards_to_input_array(cards: Collection[tuple]):
    """
    Converts a list of cards to a 1D array input for the neural network.
    To do so, it uses a many-hot encoding of the cards.
    :param cards: The cards to convert.
    :return: A 1D array of the cards.
    """
    card_ids = np.array([DurakAction.ext_from_card(card) for card in cards], dtype=np.int32)
    num_cards = DurakAction.n(4)
    card_array = np.zeros(num_cards)
    card_array[card_ids] = 1
    return card_array


def one_hot(num_classes, idx):
    arr = np.zeros(num_classes)
    arr[idx] = 1
    return arr


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
    num_players = len(state.num_cards_in_hands)
    player_id_arr = one_hot(num_players, state.player_id)
    hand_array = cards_to_input_array(state.hand)
    attack_table_array = cards_to_input_array(state.attack_table)
    defend_table_array = cards_to_input_array(state.defend_table)
    graveyard_array = cards_to_input_array(state.graveyard)
    opponents_cards_left_array = np.array(state.num_cards_in_hands)
    cards_left_in_deck_array = np.array([state.num_cards_left_in_deck])
    is_done = np.array([state.is_done])
    acting_player = one_hot(num_players, state.acting_player)
    arr = np.concatenate((
        player_id_arr,
        hand_array,
        attack_table_array,
        defend_table_array,
        graveyard_array,
        opponents_cards_left_array,
        cards_left_in_deck_array,
        is_done,
        acting_player,
    ))
    return arr


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
            hidden_layers.append(nn.LayerNorm(dim))
            cur_dim = dim
        self.ff = nn.Sequential(*hidden_layers)
        self.out = nn.Linear(cur_dim, n_actions)
        self.sm = nn.Softmax(dim=-1)

    def forward(self, x):
        y = self.ff(x)
        return self.sm(self.out(y))


class ExperienceReplay:
    """
    Class to hold experiences of SARS tuples in an efficient and easily retrievable manner to be used by the DQ Agent.
    """

    def __init__(self, memory_size, input_dim):
        self.memory_size = memory_size
        self.memory_counter = 0
        self.states = np.zeros((memory_size, input_dim), dtype=np.int32)
        # Need to store the legal actions available for us to properly mask the predicted q-values in our update step
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
        self.memory_counter += 1

    def save(self):
        np.savez_compressed("experience_replay.npz",
                            self.states,
                            self.actions,
                            self.rewards,
                            self.new_states,
                            self.terminal,
                            self.memory_counter)

    @classmethod
    def load(cls, path):
        data = np.load(path)
        inst = cls(memory_size=data["arr_0"].shape[0],
                   input_dim=data["arr_0"].shape[1])
        inst.states = data["arr_0"]
        inst.legal_actions = data["arr_1"]
        inst.actions = data["arr_2"]
        inst.rewards = data["arr_3"]
        inst.new_states = data["arr_4"]
        inst.terminal = data["arr_5"]
        inst.memory_counter = data["arr_6"]
        return inst

    def sample(self, batch_size=10) -> Tuple[ndarray, ...]:
        i = np.random.choice(self.memory_counter, batch_size) % self.memory_size
        return tuple(map(np.array, (self.states[i],
                                    self.actions[i],
                                    self.rewards[i],
                                    self.new_states[i],
                                    self.terminal[i])))


class DQAgent(nn.Module, DurakPlayer):
    """
    The actual agent using experience replay and a deep q network to learn how to play any game (?).
    """

    def __init__(
            self,
            input_dim,
            n_actions,
            player_id,
            hand,
            hidden_dims=None,
            memory_size=100000,
            batch_size=32,
            gamma=0.99,
            eps=0.1,
            device=None):
        nn.Module.__init__(self)
        DurakPlayer.__init__(self, player_id, hand=hand)
        self.dqn = DQN(input_dim, n_actions, hidden_dims)
        self.batch_size = batch_size

        self.target_dqn = DQN(input_dim, n_actions, hidden_dims)
        self.target_dqn.load_state_dict(self.dqn.state_dict())

        self.memory = ExperienceReplay(memory_size, input_dim)
        self.eps = eps
        self.gamma = gamma

        self.loss = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.dqn.parameters())
        self.scheduler = torch.optim.lr_scheduler.StepLR(self.optimizer, step_size=100, gamma=0.9)

        self.device = device if device is not None \
            else torch.device('cuda') if torch.cuda.is_available() \
            else torch.device('cpu')
        self.prev_state = None
        self.prev_action = None
        self.to(self.device)

    def forward(self, x):
        return self.dqn(x)

    def observe(self, transition: GameTransition):
        if transition.reward != 0:
            print('Transition')
        if transition.state.current_state.acting_player == self.player_id and self.prev_state is None:
            self.prev_state = transition.state
            self.prev_action = transition.action
        if transition.next_state.current_state.acting_player == self.player_id or transition.next_state.current_state.is_done:
            if self.prev_state is None:
                self.prev_state = transition.next_state
                self.prev_action = -1
            else:
                reward = 100 if transition.reward == 1 else transition.reward * len(self.hand)
                self.memory.add_experience(GameTransition(
                    self.prev_state, self.prev_action, reward, transition.next_state
                ))
                self.prev_state = transition.state

    def choose_action(self, state: InfoState, legal_actions):
        if not self.training or np.random.random() > self.eps:
            state_array = state_to_input_array(state.current_state)
            state_tensor = torch.from_numpy(state_array).float().to(self.device)
            q_values = self(state_tensor)  # Gets us all Q-values for even illegal actions
            q_values = q_values[legal_actions]  # Gets us Q-values for legal actions
            action_idx = torch.argmax(q_values).item()
            action = legal_actions[action_idx]
        else:
            action = np.random.choice(legal_actions)
        self.prev_action = action
        print(f"Action: {DurakAction.action_to_string(action)}")
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
        running_loss = 0.0
        for i in range(100):
            experience = tuple(map(lambda x: torch.from_numpy(x).to(self.device), self.memory.sample()))
            state, action, reward, new_state, terminal = experience
            state = state.float()
            new_state = new_state.float()
            action = action.to(torch.int64)

            # Use target network to get target q-values without computing or storing gradients
            with torch.no_grad():
                self.target_dqn.eval()
                target_q_value = self.target_dqn(new_state)
                max_q_value = target_q_value.max(dim=-1).values
                true_q_values = reward + self.gamma * max_q_value

            # Use main network to get predicted q-values and select only actions we took
            self.dqn.train()
            predicted_q_values = self.dqn(state)
            predicted_q_values = torch.gather(predicted_q_values, 1, action[None]).squeeze()

            # Gradient calculation and propagation
            loss = self.loss(predicted_q_values, true_q_values)
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.parameters(), 1)
            running_loss += loss.item()
            self.optimizer.step()
            self.scheduler.step()

            # Update target network
        new_dqn_sd = self.dqn.state_dict()
        target_sd = self.target_dqn.state_dict()
        self.target_dqn.load_state_dict(self.calc_target_params(target_sd, new_dqn_sd, self.eps))
        print(f"Loss: {running_loss / 500}")

    def __repr__(self):
        return DurakPlayer.__repr__(self)

    def load(self, path="dqn_agent.pt"):
        self.load_state_dict(torch.load(path))
        self.memory = ExperienceReplay.load("experience_replay.npz")
        self.target_dqn.load_state_dict(torch.load("target_dqn_agent.pt"))
        self.optimizer.load_state_dict(torch.load("optimizer.pt"))
        self.scheduler.load_state_dict(torch.load("scheduler.pt"))

    def save(self):
        torch.save(self.state_dict(), "dqn_agent.pt")
        torch.save(self.target_dqn.state_dict(), "target_dqn_agent.pt")
        torch.save(self.optimizer.state_dict(), "optimizer.pt")
        torch.save(self.scheduler.state_dict(), "scheduler.pt")
        self.memory.save()
