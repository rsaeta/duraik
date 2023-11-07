import copy

import numpy as np
from typing import Optional, List, Tuple, Literal

from .actions import DurakAction
from .game_state import ObservableDurakGameState, GameTransition, DurakGameState


class DurakDeck:

    Card = Tuple[Literal['S', 'H', 'D', 'C'], int]

    def __init__(self, lowest_card: int, np_rand: np.random.RandomState):
        self.deck = [(suit, rank) for suit in ['S', 'H', 'D', 'C'] for rank in range(lowest_card, 15)]
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
        self.visible_card: Optional[tuple] = None  # the visible card on the table determining the trump suit
        self.attackers: Optional[List[int]] = None  # the player id of the attacker
        self.defender: Optional[int] = None  # the player id of the defender
        self.player_agents = None  # list of player agent classes
        self.players: Optional[List] = None  # list of players
        self.in_players: Optional[List[int]] = None  # list of players still in the game
        self.attack_table: Optional[List[tuple]] = None  # list of attacking cards on the table
        self.defend_table: Optional[List[tuple]] = None  # list of defending cards on the table
        self.stopped_attacking: Optional[List[int]] = None  # whether the attacker has passed
        self.player_taking_action: Optional[int] = None  # the player taking action
        self.is_done: bool = False  # whether the game is done
        self.graveyard: Optional[List[tuple]] = None  # list of cards in the graveyard
        self.history: List[DurakGameState] = None

    def configure(self, game_config):
        self.num_players = game_config.get('game_num_players', 3)
        self.lowest_card = game_config.get('lowest_card', 6)
        self.np_random = np.random.RandomState(game_config.get('seed', 0))
        self.player_agents = game_config['agents']

    def _determine_init_attacker(self):
        """
        Determine the initial attacker.
        :return: int, player id of the initial attacker
        """
        suit, _ = self.visible_card
        min_rank = 20
        min_rank_player = -1
        for i, player in enumerate(self.players):
            for (s, r) in player.hand:
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
        Initialize all the game elements.
        :return: state (dict), player_id (int)
        """
        self.deck = DurakDeck(self.lowest_card, self.np_random)
        hands, self.visible_card = self.deck.deal(6, self.num_players)
        if init_players:
            self.players = [agent(i, hand=hand) for i, (agent, hand) in enumerate(zip(self.player_agents, hands))]
        else:
            for i, hand in enumerate(hands):
                self.players[i].hand = hand
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
        Gets the state of the game observable to that player's perspective.
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
            return [0.]*self.num_players
        return [1. if len(player.hand) == 0 else -1. for player in self.players]

    def step(self):
        """
        TODO: Need to update this to create a before and after state for each player
        to get them to update correctly and so that all agents see all transitions, not
        just the ones they are involved in. Not sure how I can actually do this well tbh
        """
        prev_states = self.state_per_player()
        player_id = self.player_taking_action
        actions = self.get_legal_actions(player_id)
        player = self.players[player_id]
        action = player.choose_action(self.get_observable_state(player_id), actions)
        self._do_step(player_id, action)
        rewards = self.get_rewards()
        new_states = self.state_per_player()
        for player, prev_state, new_state, reward in zip(self.players, prev_states, new_states, rewards):
            if self.is_done:
                print('done')
            transition = GameTransition(prev_state, action, reward, new_state)
            player.observe(transition)

    def current_state(self) -> DurakGameState:
        """
        Creates a new DurakGameState from the current state of the game.
        """
        return DurakGameState(
            player_hands=tuple(tuple(player.hand) for player in self.players),
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
            self.players[self.defender].add_card(card)
        for card in self.attack_table:
            self.players[self.defender].add_card(card)
        self.attack_table = []
        self.defend_table = []
        self.attackers = [(self.defender + 1) % self.num_players]
        self.player_taking_action = self.attackers[0]
        self.defender = (self.player_taking_action + 1) % self.num_players
        self.stopped_attacking = []

    def _clear_table(self):
        """
        Helper function to update the state of game when the table needs to be cleared.
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
        Helper function to check if the game is over.
        """
        if len(self.deck.deck) == 0:
            players_with_hands_left = [player for player in self.players if len(player.hand) > 0]
            if len(players_with_hands_left) <= 1:
                return True
        return False

    def _refill_cards(self, attack_order, defender_id):
        for attacker_id in attack_order:
            while len(self.players[attacker_id].hand) < 6 and len(self.deck.deck):
                self.players[attacker_id].add_card(self.deck.deck.pop())
        while len(self.players[defender_id].hand) < 6 and len(self.deck.deck):
            self.players[defender_id].add_card(self.deck.deck.pop())

    def get_potential_attackers(self, defender_id: int):
        attackers = [(defender_id + 1) % self.num_players, (defender_id - 1) % self.num_players]
        if not len(self.deck.deck):
            attackers = list(filter(lambda x: len(self.players[x].hand) > 0, attackers))
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
        self.players[player_id].remove_card(card)
        self.attack_table.append(card)
        if len(self.get_defender().hand) == self.get_num_undefended():
            self.player_taking_action = self.defender
        elif len(self.players[self.player_taking_action].hand) == 0:
            self.player_taking_action = self.defender

    def _handle_defend_action(self, player_id: int, action_id: int):
        self.stopped_attacking = []
        card = DurakAction.card_from_defend_id(action_id)
        self.players[player_id].remove_card(card)
        self.defend_table.append(card)
        if len(self.attack_table) == len(self.defend_table):
            self.player_taking_action = self.attackers[-1]

    def _handle_pass_with_card_action(self, player_id: int, action_id: int):
        self.stopped_attacking = []
        card = DurakAction.card_from_pass_with_card_id(action_id)
        self.players[player_id].remove_card(card)
        self.attack_table.append(card)
        if player_id not in self.attackers:
            self.attackers.append(player_id)
        self.defender = (player_id + 1) % self.num_players
        if self.defender in self.attackers:
            self.attackers.remove(self.defender)

    def _attackers_with_cards_left(self):
        return list(filter(lambda x: len(self.players[x].hand) > 0, self.attackers))

    def _handle_take_action(self):
        round_over = False
        self.defender_has_taken = True
        if len(self.stopped_attacking) == len(self._attackers_with_cards_left()) or len(self.get_defender().hand) == self.get_num_undefended():
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
            if len(self.players[i].hand) > 0:
                nimplayers.append(i)
        self.in_players = nimplayers

    def _handle_round_over(self, prev_state: dict):
        # Need to replenish hands from deck, going in order of attacker
        prev_attackers = prev_state['attackers']
        prev_defender = prev_state['defender']
        self._refill_cards(prev_attackers, prev_defender)
        self.defender_has_taken = False

        self._check_players_out()

        # Check if game is over
        self.is_done = self._is_game_over()
        if not self.is_done and len(self.deck.deck) == 0:
            while len(self.players[self.player_taking_action].hand) == 0:
                self.player_taking_action = (self.player_taking_action + 1) % self.num_players
            self.defender = (self.player_taking_action + 1) % self.num_players
            while len(self.players[self.defender].hand) == 0:
                self.defender = (self.defender + 1) % self.num_players

    def _do_step(self, player_id: int, action_id: int):
        """
        Perform one draw of the game.
        :param player_id: int, player id of the current player
        :param action_id: int, action taken by the current player
        :return: state (dict)
        """
        prev_state = self.get_whole_state()
        round_over = False
        if self.player_taking_action != player_id and not DurakAction.is_noop(action_id):
            raise ValueError('Player {} cannot take action {}, it is player {}\'s turn'.format(
                player_id, DurakAction.action_to_string(action_id), self.player_taking_action
            ))
        if action_id not in self.get_legal_actions(player_id):
            raise ValueError('Player {} cannot take action {}, it is not a legal action'.format(
                player_id, DurakAction.action_to_string(action_id)
            ))
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
            raise ValueError('Invalid action_id {}'.format(action_id))

        if round_over:
            self._handle_round_over(prev_state)

        self.is_done = self._is_game_over()

    def get_legal_actions(self, player_id: int):
        """
        Get all legal actions for current player.
        :param player_id: int, player id of the current player
        :return: list of int
        TODO: Figure out how to encode multiple defense actions
        """
        player = self.players[player_id]
        legal_actions = []
        if player_id == self.defender:
            legal_actions.append(DurakAction.take_action())
            if len(self.attack_table) == 0 or len(self.attack_table) == len(self.defend_table):
                return legal_actions
            attack_card = self.attack_table[len(self.defend_table)]
            defend_actions = player.can_defend_with(attack_card, self.visible_card[0])
            for card in defend_actions:
                legal_actions.append(DurakAction.defend_id_from_card(card))
            if not len(self.defend_table):  # Can only pass on initial attack
                next_attacker = (self.defender + 1) % self.num_players
                if len(self.players[next_attacker].hand) == 0:
                    next_attacker = (self.defender + 2) % self.num_players
                if len(self.players[next_attacker].hand) > len(self.attack_table):  # Can only pass if defender can
                    pass_actions = player.can_pass_with(self.attack_table[-1])
                    for card in pass_actions:
                        legal_actions.append(DurakAction.pass_with_card_id_from_card(card))

        elif player_id not in [((self.defender + 1) % self.num_players),
                               ((self.defender - 1) % self.num_players)]:  # only neighbors can attack
            legal_actions.append(DurakAction.stop_attacking_action())
        else:
            if len(self.attack_table) == 0:
                for card in player.hand:
                    legal_actions.append(DurakAction.attack_id_from_card(card))
            elif len(self.attack_table) == 6:
                legal_actions.append(DurakAction.stop_attacking_action())
            else:
                legal_actions.append(DurakAction.stop_attacking_action())
                attack_ranks = set([rank for (_, rank) in self.attack_table])
                defend_ranks = set([rank for (_, rank) in self.defend_table])
                ranks = attack_ranks.union(defend_ranks)
                for card in player.hand:
                    if card[1] in ranks:
                        legal_actions.append(DurakAction.attack_id_from_card(card))
        return legal_actions

    def set_agent(self, i, agent):
        self.players[i] = agent

    def copy(self):
        return copy.deepcopy(self)

    def get_whole_state(self):
        return copy.deepcopy({
            'attackers': self.attackers,
            'defender': self.defender,
            'player_taking_action': self.player_taking_action,
            'attack_table': self.attack_table,
            'defend_table': self.defend_table,
            'stopped_attacking': self.stopped_attacking,
            'players': self.players,
            'visible_card': self.visible_card,
            'deck': self.deck,
            'is_done': self.is_done,
            'graveyard': self.graveyard,
        })

    def __str__(self):
        return str(self.get_whole_state())
