"""
An implementation of the game engine for heads-up Durak
"""
import numpy as np
from typing import Tuple, NamedTuple, Literal, Collection, List, Set
import torch
from pathlib import Path
import os
from three_game import DurakAction


class Card(NamedTuple):
    suit: Literal["S", "H", "D", "C"]
    rank: int

    def __str__(self):
        return f"{self.suit}{self.rank}"

    def __repr__(self):
        return str(self)


Deck = Collection[Card]


def num_actions() -> int:
    """
    Returns the number of actions
    """
    ncards = 9 * 4
    n_actions = (
        ncards * 3
    )  # Each card can be played as either an attack, a defend, or a pass
    n_actions += 1  # +1 for the stop attacking action
    n_actions += 1  # +1 for the take action
    return n_actions


def observable_state_shape() -> Tuple[int, ...]:
    """
    Returns the dimensions of the state space.
    """
    return new_state(0).observable(0).to_array().shape


def many_hot(total: int, idxs: List[int]):
    """
    Creates a many-hot encoding of the idxs.
    """
    zeros = np.zeros(total)
    zeros[idxs] = 1
    return zeros


def new_deck(
    rand: np.random.RandomState, lowest_rank: int = 6, shuffle: bool = True
) -> List[Card]:
    """
    Creates a deck of cards
    """
    suits = ["S", "H", "D", "C"]
    ranks = range(lowest_rank, 15)
    d = [Card(suit, rank) for suit in suits for rank in ranks]
    if shuffle:
        rand.shuffle(d)
    return d


def cards_to_input_array(cards: Collection[Tuple[Card, ...]]):
    """
    Converts a list of cards to a 1D array input for the neural network.
    To do so, it uses a many-hot encoding of the cards.
    :param cards: The cards to convert.
    :return: A 1D array of the cards.
    """
    card_ids = np.array(
        [DurakAction.ext_from_card(card) for card in cards], dtype=np.int32
    )
    num_cards = DurakAction.n(4)
    return many_hot(num_cards, card_ids)


def input_array_to_cards(array: np.array) -> Tuple[Card, ...]:
    """
    This is the reverse of cards_to_input_array where given a many-hot
    encoding of cards as an np.array, this will reconstruct a collection
    of cards that that represents.
    """
    return tuple(DurakAction.card_from_ext(ext) for ext in np.where(array)[0])


class ObservableGameState(NamedTuple):
    cards_in_deck: int
    hand: Tuple[Card, ...]
    visible_card: Card
    attack_table: Tuple[Card, ...]
    defend_table: Tuple[Card, ...]
    graveyard: Tuple[Card, ...]
    is_done: bool
    player_taking_action: int
    defender: int
    defender_has_taken: bool
    cards_in_opponent: int
    player_id: int

    def to_array(self) -> np.array:
        """
        Transforms the observable game state into a 1-D numpy array.
        For elements defender_arr and acting_arr, we use a many-hot
        encoding since these sparse inputs make it easier for the
        network to differentiate between players, rather than providing
        the index as a single integer. Similarly, the one_hot acting_arr
        and defender_arr are used to encode the player taking action and
        the defender where the first element is 1 if the current player
        is those things, otherwise the second element is 1. This reduces
        some redundancy in the state space and keeps things relative
        to the current player rather than dependent on player_id.
        """
        hand_arr = cards_to_input_array(self.hand)
        attack_table_arr = cards_to_input_array(self.attack_table)
        defend_table_arr = cards_to_input_array(self.defend_table)
        graveyard_arr = cards_to_input_array(self.graveyard)
        defender_idx = 0 if self.defender == self.player_id else 1
        acting_idx = 0 if self.player_taking_action == self.player_id else 1
        defender_arr = np.array([0, 0])
        defender_arr[defender_idx] = 1
        acting_arr = np.array([0, 0])
        acting_arr[acting_idx] = 1
        player_id_arr = many_hot(2, [self.player_id])
        return np.concatenate(
            [
                player_id_arr,
                np.array([self.cards_in_deck]),
                hand_arr,
                cards_to_input_array([self.visible_card]),
                attack_table_arr,
                defend_table_arr,
                graveyard_arr,
                np.array([self.is_done]),
                acting_arr,
                defender_arr,
                np.array([self.defender_has_taken]),
                np.array([self.cards_in_opponent]),
            ]
        )

    @classmethod
    def from_array(cls, array: np.array) -> "ObservableGameState":
        """
        This is the reverse of to_array. Given an array, the output of which
        is the input to to_array, this will return the original observable
        state.
        """
        player_id = int(np.where(array[:2])[0][0])
        array = array[2:]
        cards_in_deck = int(array[0])
        array = array[1:]
        hand = input_array_to_cards(array[: DurakAction.n(4)])
        array = array[DurakAction.n(4) :]
        visible_card = input_array_to_cards(array[: DurakAction.n(4)])[0]
        array = array[DurakAction.n(4) :]
        attack_table = input_array_to_cards(array[: DurakAction.n(4)])
        array = array[DurakAction.n(4) :]
        defend_table = input_array_to_cards(array[: DurakAction.n(4)])
        array = array[DurakAction.n(4) :]
        graveyard = input_array_to_cards(array[: DurakAction.n(4)])
        array = array[DurakAction.n(4) :]
        is_done = bool(array[0])
        array = array[1:]
        player_taking_action = int(player_id if array[0] else (player_id + 1) % 2)
        array = array[2:]
        defender = int(player_id if array[0] else (player_id + 1) % 2)
        array = array[2:]
        defender_has_taken = bool(array[0])
        array = array[1:]
        cards_in_opponent = int(array[0])
        return cls(
            cards_in_deck=cards_in_deck,
            hand=hand,
            visible_card=visible_card,
            attack_table=attack_table,
            defend_table=defend_table,
            graveyard=graveyard,
            is_done=is_done,
            player_taking_action=player_taking_action,
            defender=defender,
            defender_has_taken=defender_has_taken,
            cards_in_opponent=cards_in_opponent,
            player_id=player_id,
        )


class GameState(NamedTuple):
    """
    DurakGameState is an immutable data structure that stores the state of the game.
    Because it uses immutable data structures, it should be hashable easily.
    """

    deck: Tuple[Card, ...]
    hands: Tuple[Tuple[Card, ...], Tuple[Card, ...]]  # list of cards in hand
    visible_card: Card  # the visible card on the table determining the trump suit
    attack_table: Tuple[Card, ...]  # list of attacking cards on the table
    defend_table: Tuple[Card, ...]  # list of defending cards on the table
    graveyard: Tuple[Card, ...]  # list of cards in the graveyard
    is_done: bool  # whether the game is done
    player_taking_action: int  # player taking action
    defender: int  # defender
    defender_has_taken: bool  # whether defender has taken and attacker can add more cards

    def num_undefended(self):
        return len(self.attack_table) - len(self.defend_table)

    def observable(self, player_id) -> ObservableGameState:
        """
        Returns what is observable only to player_id
        """
        opponent = (player_id + 1) % 2
        return ObservableGameState(
            player_id=player_id,
            cards_in_deck=len(self.deck),
            hand=self.hands[player_id],
            visible_card=self.visible_card,
            attack_table=self.attack_table,
            defend_table=self.defend_table,
            graveyard=self.graveyard,
            is_done=self.is_done,
            player_taking_action=self.player_taking_action,
            defender=self.defender,
            defender_has_taken=self.defender_has_taken,
            cards_in_opponent=len(self.hands[opponent]),
        )


def _initial_attacker(
    hands: Tuple[Card, ...], trump_suit: Card.suit, rand: np.random.RandomState
) -> int:
    min_trump = 20
    min_player = -1
    for i, hand in enumerate(hands):
        for card in hand:
            if card.suit == trump_suit and card.rank < min_trump:
                min_trump = card.rank
                min_player = i
    if min_player < 0:
        return rand.choice(2)
    return min_player


def new_state(seed: int = 0, lowest_rank: int = 9):
    """
    Creates a new game state
    """
    rand = np.random.RandomState(seed)
    d = new_deck(rand, lowest_rank)
    hands = tuple([[d.pop() for _ in range(6)] for _ in range(2)])
    visible_card = d[0]
    attack_table = ()
    defend_table = ()
    graveyard = ()
    is_done = False
    init_attacker = _initial_attacker(hands, visible_card.suit, rand)
    player_taking_action = init_attacker
    defender = (init_attacker + 1) % 2
    defender_has_taken = False
    return GameState(
        deck=d,
        hands=tuple(map(tuple, hands)),
        visible_card=visible_card,
        attack_table=attack_table,
        defend_table=defend_table,
        graveyard=graveyard,
        is_done=is_done,
        player_taking_action=player_taking_action,
        defender=defender,
        defender_has_taken=defender_has_taken,
    )


def _refill_player_hands(state: GameState) -> GameState:
    """
    Refills the players' hands after the end of a round if needed
    and possible
    """
    deck = list(state.deck)
    attacker = (state.defender + 1) % 2
    refill_queue = [attacker, state.defender]
    hands = list(map(list, state.hands))
    for pid in refill_queue:
        while len(hands[pid]) < 6 and len(deck):
            hands[pid].append(deck.pop())
    return state._replace(
        deck=tuple(deck),
        hands=tuple(map(tuple, hands)),
    )


def _step_attack(state: GameState, action: DurakAction) -> GameState:
    """
    Adds a card to the attack table. If the attack table is full, then the player
    taking action is changed to the defender. If the player's hand is empty, then
    also change the player taking action to the defender. Otherwise, acting player
    stays the same.
    """
    card = Card(*DurakAction.card_from_attack_id(action))
    assert card in state.hands[state.player_taking_action]
    new_attack_table = tuple([*state.attack_table, card])
    new_player_hand = tuple(
        c for c in state.hands[state.player_taking_action] if c != card
    )
    new_state = state._replace(
        hands=tuple(
            new_player_hand if i == state.player_taking_action else hand
            for i, hand in enumerate(state.hands)
        ),
        attack_table=new_attack_table,
    )
    # Now need to check to see if the current attacker stays the player taking action
    if len(new_player_hand) == 0 or len(new_attack_table) == 6:
        new_state = new_state._replace(player_taking_action=state.defender)
    return new_state


def _step_stop_attacking(state: GameState) -> GameState:
    """
    In heads up, as soon as a player stops attacking, the defender must defend.
    """
    if (
        state.defender_has_taken
    ):  # Here the attacker has added all the cards they want and the defender takes
        new_state = _give_defender_cards(state)
        new_state = new_state._replace(defender_has_taken=False)
    elif state.num_undefended():
        new_state = state._replace(player_taking_action=state.defender)
    else:
        new_state = _clear_table(state)._replace(defender_has_taken=False)
        new_state = _refill_player_hands(new_state)
        new_state = new_state._replace(defender=(state.defender + 1) % 2)
        new_state = _swap_acting_player(new_state)
    return new_state


def rewards(state: GameState) -> Tuple[float, float]:
    """
    Returns the rewards for the two players
    """
    if not state.is_done:
        return 0, 0
    return tuple(-1 if len(hand) else 1 for hand in state.hands)


def _clear_table(state: GameState) -> GameState:
    """
    Clears the table after successful defense. It adds all cards in play to the
    graveyard and resets the attack and defend tables to empty.
    """
    graveyard = state.graveyard + state.attack_table + state.defend_table
    new_state = state._replace(
        attack_table=(),
        defend_table=(),
        graveyard=graveyard,
    )
    return new_state


def _give_defender_cards(state: GameState) -> GameState:
    """
    Gives the defender cards after an unsuccessful defense and player has stopped attacking
    """
    new_defender_hand = (
        state.hands[state.defender] + state.attack_table + state.defend_table
    )
    new_state = state._replace(
        hands=tuple(
            new_defender_hand if i == state.defender else hand
            for i, hand in enumerate(state.hands)
        ),
        attack_table=(),
        defend_table=(),
    )
    return new_state


def _swap_acting_player(state: GameState) -> GameState:
    """
    Swaps acting player to other player
    """
    acting_player = (state.player_taking_action + 1) % 2
    return state._replace(player_taking_action=acting_player)


def _step_defend(state: GameState, action: DurakAction) -> GameState:
    """
    First it adds card to the defense table. If all cards are defended and there are less than
    6 cards on the table, and the defender/attacker still have cards in their hands, then the
    acting player becomes the attacker.
    """
    card = Card(*DurakAction.card_from_defend_id(action))
    assert card in state.hands[state.player_taking_action]
    new_defend_table = tuple([*state.defend_table, card])
    new_player_hand = tuple(
        c for c in state.hands[state.player_taking_action] if c != card
    )
    new_state = state._replace(
        hands=tuple(
            new_player_hand if i == state.player_taking_action else hand
            for i, hand in enumerate(state.hands)
        ),
        defend_table=new_defend_table,
    )
    if len(new_state.attack_table) == len(new_state.defend_table):
        if len(new_state.attack_table) == 6 or 0 in set(
            len(h) for h in state.hands
        ):  # Max attack reached and successfully defended
            new_state = _clear_table(new_state)
            acting_player = state.defender  # defender becomes attacker
            defender = (state.defender + 1) % 2  # other player becomes defender
            return new_state._replace(
                player_taking_action=acting_player, defender=defender
            )
        else:
            return _swap_acting_player(new_state)
    return new_state


def _step_take(state: GameState) -> GameState:
    """
    Here, if there is still more cards to be added, all we have to do is mark that defender has taken and swap
    the active player. Otherwise, we need to give the defender the cards and swap active player.
    """
    if len(state.attack_table) < 6 and 0 not in set(len(h) for h in state.hands):
        new_state = state._replace(defender_has_taken=True)
        return _swap_acting_player(new_state)
    new_state = _give_defender_cards(state)
    new_state = _refill_player_hands(new_state)
    new_state = new_state._replace(defender_has_taken=False)
    return _swap_acting_player(new_state)


def _legal_defense_actions(state: GameState) -> List[DurakAction]:
    """
    Gets a list of actions available to the defender
    """
    if not state.num_undefended():
        return []
    card_to_defend = state.attack_table[len(state.defend_table)]
    trump_suit = state.visible_card.suit
    actions = [DurakAction.take_action()]
    for card in state.hands[state.defender]:
        if card.suit == card_to_defend.suit and card.rank > card_to_defend.rank:
            actions.append(DurakAction.defend(card))
    if card_to_defend.suit != trump_suit:
        for card in state.hands[state.defender]:
            if card.suit == trump_suit:
                actions.append(DurakAction.defend(card))
    return actions


def _ranks(cards: Collection[Card]) -> Set[int]:
    return set(c.rank for c in cards)


def _legal_attack_actions(state: GameState) -> List[DurakAction]:
    """
    Returns a list of legal actions for the attacker. If there is nothing on the board, they
    must attack with a card in their hand. If there is something on the board, then they can
    add any card that shares a rank with a card on the table, or they can elect to stop attacking.
    """
    if not len(state.attack_table):
        return [DurakAction.attack(c) for c in state.hands[state.player_taking_action]]
    ranks_on_table = _ranks(state.attack_table).union(_ranks(state.defend_table))
    actions = [
        DurakAction.attack(c)
        for c in state.hands[state.player_taking_action]
        if c.rank in ranks_on_table
    ]
    actions.append(DurakAction.stop_attacking())
    return actions


def legal_actions(state: GameState) -> GameState:
    """
    Returns a list of legal moves
    """
    if state.is_done:
        return []
    if state.player_taking_action == state.defender:
        return _legal_defense_actions(state)
    return _legal_attack_actions(state)


def _check_done(state: GameState) -> bool:
    """
    Checks if the game is done
    """
    if state.is_done:
        return True
    if len(state.deck):
        return False
    return 0 in set(len(h) for h in state.hands)


def step(state: GameState, action: DurakAction) -> GameState:
    """
    Take a step in the game according to current state and action
    """
    if action not in legal_actions(state):
        raise ValueError("Invalid action", action)
    if DurakAction.is_attack(action):
        new_state = _step_attack(state, action)
    elif DurakAction.is_stop_attacking(action):
        new_state = _step_stop_attacking(state)
    elif DurakAction.is_defend(action):
        new_state = _step_defend(state, action)
    elif DurakAction.is_take(action):
        new_state = _step_take(state)
    else:
        raise ValueError("Invalid action", action)
    return new_state._replace(is_done=_check_done(new_state))


class GameRunner:
    def __init__(self):
        self.state_history = []  # Holds a list of perfect-information states
        self.action_history = []  # Holds a list of actions taken by player
        self.reward_history = []  # Holds a list of tuples of rewards for each player
        self.agents = [None, None]

    def set_agent(self, idx, agent):
        if idx not in range(len(self.agents)):
            raise ValueError("Invalid agent index")
        self.agents[idx] = agent

    def set_agents(self, agents):
        if len(agents) != len(self.agents):
            raise ValueError("Invalid number of agents")
        self.agents = agents

    def reset(self):
        self.state_history = []

    def save_run(self, save_dir: Path):
        """
        Saves the history of the game to a directory in 3 different files.
        """
        os.makedirs(save_dir, exist_ok=True)
        self.save_observable_history(save_dir / "obs.npy")
        self.save_reward_history(save_dir / "rewards.npy")
        self.save_action_history(save_dir / "actions.npy")
        with open(save_dir / "configs.json", "w") as f:
            f.write(str(self.agents))

    def save_reward_history(self, path: Path):
        np.save(path, np.array(self.reward_history))

    def save_action_history(self, path: Path):
        np.save(path, np.array(self.action_history))

    def save_observable_history(self, path: Path):
        """
        Saves the sequence of observable states for both players to a file as an
        np.ndarray with dimensions (num_players, sequence_length, *observable_state_shape)
        """
        seq_len = len(self.state_history)
        obs_shape = observable_state_shape()
        obs = np.zeros((2, seq_len, *obs_shape))
        for i, state in enumerate(self.state_history):
            obs[:, i, :] = (
                state.observable(0).to_array(),
                state.observable(1).to_array(),
            )
        np.save(path, obs)

    def get_information_state(self, player_id) -> List[ObservableGameState]:
        """
        Returns the information state of the player
        """
        return [state.observable(player_id) for state in self.state_history]

    def step(self) -> GameState:
        if any(agent is None for agent in self.agents):
            raise ValueError("Agent is None")
        state = self.state_history[-1]
        actions = legal_actions(state)
        if not len(actions):
            return
        information_state = self.get_information_state(state.player_taking_action)
        action = self.agents[state.player_taking_action].choose_action(
            information_state[-1], actions, full_state=information_state
        )
        state = step(state, action)
        self.state_history.append(state)
        self.action_history.append(action)
        self.reward_history.append(rewards(state))
        return state

    def run(self, seed=0) -> Tuple[float, float]:
        self.state_history = [new_state(seed)]
        if any(agent is None for agent in self.agents):
            raise ValueError("Agent is None")
        state = self.state_history[-1]
        while not state.is_done:
            state = self.step()
        return rewards(state)
