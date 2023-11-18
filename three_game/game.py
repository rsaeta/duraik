import copy
import random
import string
from pathlib import Path
import pickle

import numpy as np
from typing import Optional, List, Tuple, Literal, NamedTuple

from .actions import DurakAction
from .game_state import ObservableDurakGameState, DurakGameState


class Card(NamedTuple):
    suit: Literal["S", "H", "D", "C"]
    rank: int

    def __repr__(self):
        return f"{self.suit}{self.rank}"


class DurakDeck:

    def __init__(self, lowest_card: int, np_rand: np.random.RandomState):
        self.deck = [
            Card(suit, rank)
            for suit in ["S", "H", "D", "C"]
            for rank in range(lowest_card, 15)
        ]
        np_rand.shuffle(self.deck)
        self.visible_card = None

    def deal(self, num_cards: int, num_players: int):
        """
        Deal cards to players.
        :param num_cards: int, number of cards to deal to each player
        :param num_players: int, number of players
        :return: list of list of cards, list of cards
        """
        hands = [[] for _ in range(num_players)]
        for _ in range(num_cards):
            for i in range(num_players):
                hands[i].append(self.deck.pop())
        self.visible_card = self.deck[0]
        return hands, self.visible_card

    def __str__(self):
        return str(self.deck)

    def __repr__(self):
        return str(self.deck)

    @classmethod
    def deck_without(cls, cards: List[Card]):
        deck = cls(6, np.random.RandomState())
        for card in cards:
            deck.deck.remove(card)
        return deck


class DurakGame:
    def __init__(self, allow_step_back=False):
        self.defender_has_taken: bool = False
        self.lowest_card: Optional[int] = None  # lowest card rank in the deck
        self.num_players: Optional[int] = None  # number of players
        self.allow_step_back: bool = allow_step_back  # whether to allow step_back
        self.np_random = np.random.RandomState()  # numpy random generator
        self.deck: Optional[DurakDeck] = None  # deck of cards
        self.player_hands: Optional[List[List[tuple]]] = None  # list of player hands
        self.visible_card: Optional[
            tuple
        ] = None  # the visible card on the table determining the trump suit
        self.attackers: Optional[List[int]] = None  # the player id of the attacker
        self.defender: Optional[int] = None  # the player id of the defender
        self.player_agents = None  # list of player agent classes
        self.players: Optional[List] = None  # list of players
        self.in_players: Optional[List[int]] = None  # list of players still in the three_game
        self.attack_table: Optional[
            List[tuple]
        ] = None  # list of attacking cards on the table
        self.defend_table: Optional[
            List[tuple]
        ] = None  # list of defending cards on the table
        self.stopped_attacking: Optional[
            List[int]
        ] = None  # whether the attacker has passed
        self.player_taking_action: Optional[int] = None  # the player taking action
        self.is_done: bool = False  # whether the three_game is done
        self.graveyard: Optional[List[tuple]] = None  # list of cards in the graveyard
        self.history: List[DurakGameState] = None

    def configure(self, game_config):
        self.num_players = game_config.get("game_num_players", 3)
        self.lowest_card = game_config.get("lowest_card", 6)
        self.np_random = np.random.RandomState(game_config.get("seed", 0))
        self.player_agents = game_config["agents"]

    def _determine_init_attacker(self):
        """
        Determine the initial attacker.
        :return: int, player id of the initial attacker
        """
        suit, _ = self.visible_card
        min_rank = 20
        min_rank_player = -1
        for i, hand in enumerate(self.player_hands):
            for s, r in hand:
                if s == suit and r < min_rank:
                    min_rank = r
                    min_rank_player = i
        if min_rank_player < 0:
            return self.np_random.randint(self.num_players)
        return min_rank_player

    def reset_game(self):
        self.init_game(init_players=False)

    def init_game(self, init_players: Optional[bool] = True):
        """
        Initialize all the three_game elements.
        :return: state (dict), player_id (int)
        """
        self.deck = DurakDeck(self.lowest_card, self.np_random)
        self.player_hands, self.visible_card = self.deck.deal(6, self.num_players)
        if init_players:
            self.players = [agent(i) for i, agent in enumerate(self.player_agents)]
        self.in_players = list(range(self.num_players))
        self.attackers = [self._determine_init_attacker()]
        self.defender = (self.attackers[0] + 1) % self.num_players
        self.player_taking_action = self.attackers[0]
        self.attack_table = []
        self.defend_table = []
        self.stopped_attacking = []
        self.graveyard = []
        self.is_done = False
        self.defender_has_taken = False
        self.history = [self.current_state()]

    def get_observable_state(self, player_id: int) -> ObservableDurakGameState:
        """
        Gets the state of the three_game observable to that player's perspective.
        :return: ObservableDurakGameState
        """
        return self.current_state().observable(player_id)

    def state_per_player(self) -> List[ObservableDurakGameState]:
        """
        Returns the state according to each player's perspective.
        """
        return [self.get_observable_state(i) for i in range(self.num_players)]

    def get_rewards(self):
        if not self.is_done:
            return [0.0] * self.num_players
        return [1.0 if len(hand) == 0 else -1.0 for hand in self.player_hands]

    def step(self):
        player_id = self.player_taking_action
        information_state = [state.observable(player_id) for state in self.history]
        actions = self.get_legal_actions(player_id)
        player = self.players[player_id]
        action = player.choose_action(information_state[-1], actions, full_state=information_state)

        self._do_step(player_id, action)
        new_state = self.current_state()
        self.history.append(new_state)

    def current_state(self) -> DurakGameState:
        """
        Creates a new DurakGameState from the current state of the three_game.
        """
        return DurakGameState(
            player_hands=tuple(tuple(hand) for hand in self.player_hands),
            visible_card=self.visible_card,
            attack_table=tuple(self.attack_table),
            defend_table=tuple(self.defend_table),
            graveyard=tuple(self.graveyard),
            attackers=tuple(self.attackers),
            defender=self.defender,
            player_taking_action=self.player_taking_action,
            defender_has_taken=self.defender_has_taken,
            stopped_attacking=tuple(self.stopped_attacking),
            is_done=self.is_done,
            deck=tuple(self.deck.deck),
            np_rand=self.np_random,
            round_over=False,
        )

    def _give_defender_table_cards(self):
        """
        Helper function to update current state when the current defender needs to take cards from the table.
        It will also update the state variables for attacker and defender.
        :return:
        """
        for card in self.defend_table:
            self.player_hands[self.defender].append(card)
        for card in self.attack_table:
            self.player_hands[self.defender].append(card)
        self.attack_table = []
        self.defend_table = []
        self.attackers = [(self.defender + 1) % self.num_players]
        self.player_taking_action = self.attackers[0]
        self.defender = (self.player_taking_action + 1) % self.num_players
        self.stopped_attacking = []

    def _clear_table(self):
        """
        Helper function to update the state of three_game when the table needs to be cleared.
        :return:
        """
        for att, defend in zip(self.attack_table, self.defend_table):
            self.graveyard.append(att)
            self.graveyard.append(defend)
        self.stopped_attacking = []
        self.attack_table = []
        self.defend_table = []
        self.attackers = [self.defender]
        self.player_taking_action = self.defender
        self.defender = (self.defender + 1) % self.num_players

    def _is_game_over(self):
        """
        Helper function to check if the three_game is over.
        """
        if len(self.deck.deck) == 0:
            hands_left = [
                hand for hand in self.player_hands if len(hand) or len(self.deck.deck)
            ]
            if len(hands_left) <= 1:
                return True
        return False

    def _refill_cards(self, attack_order, defender_id):
        for attacker_id in attack_order:
            while len(self.player_hands[attacker_id]) < 6 and len(self.deck.deck):
                self.player_hands[attacker_id].append(self.deck.deck.pop())
        while len(self.player_hands[defender_id]) < 6 and len(self.deck.deck):
            self.player_hands[defender_id].append(self.deck.deck.pop())

    def get_potential_attackers(self, defender_id: int):
        attackers = [
            (defender_id + 1) % self.num_players,
            (defender_id - 1) % self.num_players,
        ]
        if not len(self.deck.deck):
            attackers = list(filter(lambda x: len(self.player_hands[x]) > 0, attackers))
        return attackers

    def get_defender(self):
        return self.players[self.defender]

    def get_num_undefended(self):
        return len(self.attack_table) - len(self.defend_table)

    def legal_actions(self):
        return self.get_legal_actions(self.player_taking_action)

    def _handle_attack_action(self, player_id: int, action_id: int):
        if not self.defender_has_taken:
            self.stopped_attacking = []
        if player_id not in self.attackers:
            self.attackers.append(player_id)
        card = DurakAction.card_from_attack_id(action_id)
        self.player_hands[player_id].remove(card)
        self.attack_table.append(card)
        if (len(self.player_hands[self.defender]) == self.get_num_undefended()) or (
            len(self.player_hands[self.player_taking_action]) == 0
        ):
            self.player_taking_action = self.defender

    def _handle_defend_action(self, player_id: int, action_id: int):
        self.stopped_attacking = []
        card = DurakAction.card_from_defend_id(action_id)
        self.player_hands[player_id].remove(card)
        self.defend_table.append(card)
        if len(self.attack_table) == len(self.defend_table):
            self.player_taking_action = self.attackers[-1]

    def _handle_pass_with_card_action(self, player_id: int, action_id: int):
        self.stopped_attacking = []
        card = DurakAction.card_from_pass_with_card_id(action_id)
        self.player_hands[player_id].remove(card)
        self.attack_table.append(card)
        if player_id not in self.attackers:
            self.attackers.append(player_id)
        self.defender = (player_id + 1) % self.num_players
        if self.defender in self.attackers:
            self.attackers.remove(self.defender)

    def _attackers_with_cards_left(self):
        return list(filter(lambda x: len(self.player_hands[x]) > 0, self.attackers))

    def _handle_take_action(self):
        round_over = False
        self.defender_has_taken = True
        if (
            len(self.stopped_attacking) == len(self._attackers_with_cards_left())
            or len(self.player_hands[self.defender]) == self.get_num_undefended()
        ):
            self._give_defender_table_cards()
            round_over = True
        else:
            self.player_taking_action = self.attackers[-1]
        return round_over

    def _handle_stop_attack_action(self, player_id: int):
        round_over = False
        if player_id not in self.stopped_attacking:
            self.stopped_attacking.append(player_id)
        if len(self.attack_table) > len(self.defend_table):
            if self.defender_has_taken:
                if len(self.stopped_attacking) == len(self.in_players) - 1:
                    self._give_defender_table_cards()
                    round_over = True
                else:
                    potential_attackers = self.get_potential_attackers(self.defender)
                    if self.attackers[-1] in potential_attackers:
                        potential_attackers.remove(self.attackers[-1])
                    if len(potential_attackers):
                        self.player_taking_action = potential_attackers[0]
                    else:
                        self.player_taking_action = self.defender
            else:
                self.player_taking_action = self.defender
        elif len(self.stopped_attacking) == len(self.in_players) - 1:
            round_over = True
            self._clear_table()
        else:
            potential_attackers = self.get_potential_attackers(self.defender)
            if self.attackers[-1] in potential_attackers:
                potential_attackers.remove(self.attackers[-1])
            if len(potential_attackers):
                self.player_taking_action = potential_attackers[0]
            else:
                self.player_taking_action = self.defender
            if self.player_taking_action not in self.attackers + [self.defender]:
                self.attackers.append(self.player_taking_action)
        return round_over

    def _check_players_out(self):
        if len(self.deck.deck) > 0:
            return
        nimplayers = []
        for i in range(self.num_players):
            if len(self.player_hands[i]) > 0:
                nimplayers.append(i)
        self.in_players = nimplayers

    def _handle_round_over(self, prev_state: dict):
        # Need to replenish hands from deck, going in order of attacker
        prev_attackers = prev_state["attackers"]
        prev_defender = prev_state["defender"]
        self._refill_cards(prev_attackers, prev_defender)
        self.defender_has_taken = False

        self._check_players_out()

        # Check if three_game is over
        self.is_done = self._is_game_over()
        if not self.is_done and len(self.deck.deck) == 0:
            while len(self.player_hands[self.player_taking_action]) == 0:
                self.player_taking_action = (
                    self.player_taking_action + 1
                ) % self.num_players
            self.defender = (self.player_taking_action + 1) % self.num_players
            while len(self.player_hands[self.defender]) == 0:
                self.defender = (self.defender + 1) % self.num_players

    def _do_step(self, player_id: int, action_id: DurakAction):
        """
        Perform one draw of the three_game.
        :param player_id: int, player id of the current player
        :param action_id: int, action taken by the current player
        :return: state (dict)
        """
        print(f"Player {player_id} chose action {action_id}")
        prev_state = self.get_whole_state()
        round_over = False
        if self.player_taking_action != player_id and not DurakAction.is_noop(
            action_id
        ):
            raise ValueError(
                "Player {} cannot take action {}, it is player {}'s turn".format(
                    player_id,
                    DurakAction.action_to_string(action_id),
                    self.player_taking_action,
                )
            )
        if action_id not in self.get_legal_actions(player_id):
            raise ValueError(
                "Player {} cannot take action {}, it is not a legal action".format(
                    player_id, DurakAction.action_to_string(action_id)
                )
            )
        # Delegate handling of actions to helper functions
        if DurakAction.is_attack(action_id):
            self._handle_attack_action(player_id, action_id)
        elif DurakAction.is_defend(action_id):
            self._handle_defend_action(player_id, action_id)
        elif DurakAction.is_pass_with_card(action_id):
            self._handle_pass_with_card_action(player_id, action_id)
        elif DurakAction.is_take(action_id):
            round_over = self._handle_take_action()
        elif DurakAction.is_stop_attacking(action_id):
            round_over = self._handle_stop_attack_action(player_id)
        else:
            raise ValueError("Invalid action_id {}".format(action_id))

        if round_over:
            self._handle_round_over(prev_state)

        self.is_done = self._is_game_over()

    def save_history(self, save_dir: Path):
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = save_dir / f"history{''.join(random.choices(string.ascii_letters, k=10))}.pkl"
        with open(filename, "wb") as f:
            pickle.dump(self.history, f)

    def _get_defender_actions(self) -> List[DurakAction]:
        """
        Returns a tuple of legal action ids for the defender.
        """
        state = self.current_state()
        actions = [DurakAction.take_action()]
        ts = state.visible_card[0]
        hand = state.player_hands[state.player_taking_action]
        undefended = state.attack_table[len(state.defend_table)]

        next_defender = (state.defender + 1) % len(state.player_hands)
        if (
            len(state.defend_table) == 0
            and len(state.player_hands[next_defender]) >= len(state.attack_table) + 1
        ):
            actions.extend(
                [
                    DurakAction.pass_with_card(card)
                    for card in hand
                    if card[1] == undefended[1]
                ]
            )

        for card in hand:
            if card[0] == undefended[0] and card[1] > undefended[1]:
                actions.append(DurakAction.defend(card))
            if undefended[0] != ts and card[0] == ts:
                actions.append(DurakAction.defend(card))
        return list(set(actions))

    def _get_attacker_actions(self) -> List[DurakAction]:
        """
        Gets the attack actions. If this is the initial attack, you cannot stop attacking and can attack
        with any card in hand.
        If attack has already started, then you can stop attacking or attack with any card in hand that
        matches rank with any card on table.
        """
        state = self.current_state()
        if len(state.attack_table) == 0:
            return [
                DurakAction.attack(card)
                for card in state.player_hands[state.player_taking_action]
            ]
        actions = [DurakAction.stop_attacking()]
        if (
            len(state.attack_table) == 6
            or len(state.player_hands[state.defender]) == state.num_undefended()
        ):
            return actions
        hand = state.player_hands[state.player_taking_action]
        ranks = set([card[1] for card in state.attack_table])
        ranks = ranks.union(set([card[1] for card in state.defend_table]))
        for card in hand:
            if card[1] in ranks:
                actions.append(DurakAction.attack(card))
        return actions

    def get_legal_actions(self, player_id: int):
        """
        Get all legal actions for current player.
        :param player_id: int, player id of the current player
        :return: list of int
        """
        if player_id == self.defender:
            return self._get_defender_actions()
        return self._get_attacker_actions()

    def set_agent(self, i, agent):
        self.players[i] = agent

    def copy(self):
        return copy.deepcopy(self)

    def get_whole_state(self):
        return copy.deepcopy(
            {
                "attackers": self.attackers,
                "defender": self.defender,
                "player_taking_action": self.player_taking_action,
                "attack_table": self.attack_table,
                "defend_table": self.defend_table,
                "stopped_attacking": self.stopped_attacking,
                "players": self.players,
                "visible_card": self.visible_card,
                "deck": self.deck,
                "is_done": self.is_done,
                "graveyard": self.graveyard,
            }
        )

    def __str__(self):
        return str(self.get_whole_state())
