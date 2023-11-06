from typing import NamedTuple, Tuple
import numpy as np

from .entities import Card


class ObservableDurakGameState(NamedTuple):
    """
    DurakGameState is an immutable data structure that stores the state of the game.
    Because it uses immutable data structures, it should be hashable easily.
    """
    player_id: int  # ID of player
    hand: Tuple[Card]  # list of cards in hand
    visible_card: tuple  # the visible card on the table determining the trump suit
    attack_table: Tuple[Card]  # list of attacking cards on the table
    defend_table: Tuple[Card]  # list of defending cards on the table
    num_cards_left_in_deck: int  # number of cards left in the deck
    num_cards_in_hands: Tuple[int]  # number of cards left in the opponent's hand
    graveyard: Tuple[Card]  # list of cards in the graveyard
    is_done: bool  # whether the game is done
    lowest_rank: int  # the lowest card in the deck
    attackers: Tuple[int]  # list of attackers
    defender: int  # defender
    acting_player: int  # acting player
    defender_has_taken: bool  # whether the defender has taken the cards
    stopped_attacking: Tuple[int]  # list of players who have stopped attacking
    # available_actions: Tuple[int]  # list of available actions

    def __str__(self):
        return f"""
GameState(
    player_id: {self.player_id}
    hand: {tuple(sorted(self.hand, key=lambda x: x[1]))}
    visible_card: {self.visible_card}
    attack_table: {self.attack_table}
    defend_table: {self.defend_table}
    num_cards_left_in_deck: {self.num_cards_left_in_deck}
    num_cards_in_hands: {self.num_cards_in_hands}
    graveyard: {self.graveyard}
    is_done: {self.is_done}
    lowest_rank: {self.lowest_rank}
    attackers: {self.attackers}
    defender: {self.defender}
    acting_player: {self.acting_player}
    defender_has_taken: {self.defender_has_taken}
    stopped_attacking: {self.stopped_attacking}
)
"""

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((
            self.player_id,
            self.hand,
            self.visible_card,
            self.attack_table,
            self.defend_table,
            self.num_cards_left_in_deck,
            self.num_cards_in_hands,
            self.graveyard,
            self.is_done,
            self.lowest_rank,
            self.attackers,
            self.defender,
            self.acting_player,
            self.defender_has_taken,
            self.stopped_attacking,
        ))


class DurakGameState(NamedTuple):
    """
    This dataclass encompasses the entire game state of a Durak game from which we can generate
    ObservableDurakGameState for each given player.
    """
    np_rand: np.random.RandomState
    defender_has_taken: bool
    deck: Tuple[Card, ...]
    visible_card: Card
    attackers: Tuple[int, ...]
    defender: int
    player_hands: Tuple[Tuple[Card, ...], ...]
    attack_table: Tuple[Card, ...]
    defend_table: Tuple[Card, ...]
    stopped_attacking: Tuple[int, ...]
    player_taking_action: int
    graveyard: Tuple[Card, ...]
    is_done: bool
    round_over: bool

    def potential_attackers(self):
        defender = self.defender
        attackers = [(defender + i) % len(self.player_hands) for i in [1, -1]]
        if not len(self.deck):
            attackers = list(filter(lambda x: len(self.player_hands[x]), attackers))
        return attackers

    def in_players(self):
        return tuple(i for i, hand in enumerate(self.player_hands) if len(hand) > 0 or len(self.deck))

    def num_undefended(self):
        return len(self.attack_table) - len(self.defend_table)

    def attackers_with_cards(self):
        return tuple(a for a in self.attackers if len(self.player_hands[a]) > 0)

    def observable(self, player_id: int) -> ObservableDurakGameState:
        """
        Creates an ObservableDurakGameState instance from the point of view of player_id
        """
        hand = self.player_hands[player_id]
        num_cards_in_hands = tuple(len(hand) for hand in self.player_hands)
        return ObservableDurakGameState(
            player_id=player_id,
            hand=tuple(hand),
            visible_card=self.visible_card,
            attack_table=tuple(self.attack_table),
            defend_table=tuple(self.defend_table),
            num_cards_left_in_deck=len(self.deck),
            num_cards_in_hands=num_cards_in_hands,
            graveyard=tuple(self.graveyard),
            is_done=self.is_done,
            lowest_rank=self.visible_card[1],
            attackers=tuple(self.attackers),
            defender=self.defender,
            acting_player=self.player_taking_action,
            defender_has_taken=self.defender_has_taken,
            stopped_attacking=tuple(self.stopped_attacking),
        )


class GameTransition(NamedTuple):
    state: ObservableDurakGameState
    action: int
    reward: float
    next_state: ObservableDurakGameState
