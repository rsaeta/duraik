import copy
from typing import List

import numpy as np

from agents.easy_agents import DurakPlayer, RandomPlayer
from three_game.game_state import ObservableDurakGameState
from three_game import DurakGame, DurakDeck


def simulate(state, action: int, ret_first_obs: bool = False):
    game = random_game_from_observation_state(state)
    game._do_step(state.player_id, action)
    while not game.is_done:
        game.step()
    if ret_first_obs:
        return observation.reward, first_observation
    return observation.reward


class MCTSNode:

    def __init__(self,
                 state: ObservableDurakGameState,
                 actions: List[int] = None,
                 parent: 'MCTSNode' = None):
        self.state = state
        self.parent = parent
        self.actions = actions
        # Children are indexed by action id
        self.children = {}
        self.visits = 0 if parent is not None else 1
        self.value = 0

    def is_leaf(self):
        return len(self.children) == 0

    def is_root(self):
        return self.parent is None

    def is_terminal(self):
        return self.state.is_done

    def get_value(self):
        return self.value / self.visits

    def get_ucb(self, c=1.414):
        return self.get_value() + c * np.sqrt(np.log(self.parent.visits) / (self.visits + 1e-6))

    def get_best_action(self):
        return max(self.children.items(), key=lambda x: x[1].get_value())[0]

    def get_best_child(self):
        return max(self.children.values(), key=lambda x: x.get_ucb())

    def get_random_child(self):
        return np.random.choice(list(self.children.values()))

    def get_child(self, action):
        return self.children[action]

    def add_child(self, action, child):
        self.children[action] = child

    def update(self, value):
        self.value += value
        self.visits += 1

    def fully_expanded(self):
        return len(self.children) == len(self.actions)


class MCTSPlayer(DurakPlayer):
    """
    Monte-Carlo Tree-search player that guesses the best move based on
    randomized rollouts of the three_game. To do so, it must reconstruct a random three_game
    from the observational state and run many randomized rollouts for each possible
    action, picking the one with the best randomized rollouts in terms of expectation.
    """
    def __init__(self, player_id: int, hand: List[tuple], num_simulations: int = 25):
        super().__init__(player_id, hand)
        self.num_simulations = num_simulations
        self.node_cache = {}

    @staticmethod
    def get_rollout_node(root: MCTSNode) -> MCTSNode:
        node = root
        while not node.is_leaf():
            if node.fully_expanded():
                node = node.get_best_child()
            else:
                return node
        return node

    @staticmethod
    def rollout(node: MCTSNode) -> MCTSNode:
        state = node.state
        action = np.random.choice(node.actions)
        reward, obs = simulate(state, action, ret_first_obs=True)
        if action not in node.children:
            next_rand_game = random_game_from_observation_state(copy.deepcopy(obs.next_state))
            next_actions = next_rand_game.get_legal_actions(obs.next_state.player_id)
            node.add_child(action, MCTSNode(obs.next_state, next_actions, node))
        update_node = node.get_child(action)
        while not update_node.is_root():
            update_node.update(reward)
            update_node = update_node.parent
        return node.get_child(action)

    def get_node(self, state: ObservableDurakGameState) -> MCTSNode:
        if state in self.node_cache:
            return self.node_cache[state]
        rand_game = random_game_from_observation_state(copy.deepcopy(state))
        actions = rand_game.get_legal_actions(self.player_id)
        node = MCTSNode(state, actions)
        self.node_cache[state] = node
        return node

    def choose_action(self, state: ObservableDurakGameState, actions: List[int]):
        """
        Chooses an action based on the state and possible actions.
        :param state: The state of the three_game.
        :param actions: The possible actions.
        :return: The chosen action.
        """
        if len(actions) == 1:
            return actions[0]
        root = self.get_node(state)
        for i in range(self.num_simulations):
            node = self.get_rollout_node(root)
            child_node = self.rollout(node)
            self.add_node_to_cache(node)
            self.add_node_to_cache(child_node)
        """
        sim_scores = np.zeros(len(actions))
        sim_counts = np.zeros(len(actions))
        for i in range(self.num_simulations):
            rand_act = np.random.choice(len(actions))
            sim_scores[rand_act] += simulate(state, actions[rand_act])
            sim_counts[rand_act] += 1
        sim_scores /= (sim_counts+1e-6)
        return actions[np.argmax(sim_scores)]
        """
        return root.get_best_action()

    def add_node_to_cache(self, node: MCTSNode):
        if node.state not in self.node_cache:
            self.node_cache[node.state] = node


def shuffle_for_random_deck(deck, visible_card):
    if len(deck):
        deck.remove(visible_card)
        np.random.shuffle(deck)
        deck.insert(0, visible_card)
    return deck


def get_deck_and_hands_from_state(state: ObservableDurakGameState):
    """
    Get randomized deck and hands from observable state
    """
    hands = []
    deck = DurakDeck(6, np.random.RandomState())
    for card in state.graveyard:
        deck.deck.remove(card)
    for card in state.hand:
        deck.deck.remove(card)
    for card in state.attack_table:
        deck.deck.remove(card)
    for card in state.defend_table:
        deck.deck.remove(card)
    for i in range(len(state.num_cards_in_hands)):
        if i == state.player_id:
            hands.append(list(state.hand))
            continue
        hand = []
        for _ in range(state.num_cards_in_hands[i]):
            hand.append(deck.deck.pop())
        hands.append(hand)
    return deck, hands


def random_game_from_observation_state(state: ObservableDurakGameState) -> DurakGame:
    """
    Create a three_game from an observable state of the three_game according to a player's
    perspective. This will be helpful for MCTS agent. The idea here is public
    knowledge must stay the same (attack board, defend board, graveyard, visible
    card) and private knowledge to the player must be the same (hand, number of
    cards in other players' hands). The deck and the other players' hands will be
    randomized.
    """
    game = DurakGame()
    game.configure({
        'game_num_players': len(state.num_cards_in_hands),
        'lowest_card': state.lowest_rank,
        'agents': [RandomPlayer for _ in range(len(state.num_cards_in_hands))],
    })
    game.init_game()
    deck, hands = get_deck_and_hands_from_state(state)

    for i, hand in enumerate(hands):
        game.players[i].hand = hand

    # State management
    game.attack_table = list(state.attack_table)
    game.defend_table = list(state.defend_table)
    game.graveyard = list(state.graveyard)
    game.visible_card = state.visible_card
    game.attackers = list(state.attackers)
    game.defender = state.defender
    game.player_taking_action = state.acting_player
    game.defender_has_taken = state.defender_has_taken
    game.stopped_attacking = list(state.stopped_attacking)

    # Replace deck
    game.deck = deck

    return game
