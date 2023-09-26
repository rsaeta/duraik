from typing import NamedTuple, Tuple


class ObservableDurakGameState(NamedTuple):
    """
    DurakGameState is an immutable data structure that stores the state of the game.
    Because it uses immutable data structures, it should be hashable easily.
    """
    player_id: int  # ID of player
    hand: Tuple[tuple]  # list of cards in hand
    visible_card: tuple  # the visible card on the table determining the trump suit
    attack_table: Tuple[tuple]  # list of attacking cards on the table
    defend_table: Tuple[tuple]  # list of defending cards on the table
    num_cards_left_in_deck: int  # number of cards left in the deck
    num_cards_in_hands: Tuple[int]  # number of cards left in the opponent's hand
    graveyard: Tuple[tuple]  # list of cards in the graveyard
    is_done: bool  # whether the game is done
    lowest_rank: int  # the lowest card in the deck
    attackers: Tuple[int]  # list of attackers
    defender: int  # defender
    acting_player: int  # acting player
    defender_has_taken: bool  # whether the defender has taken the cards
    stopped_attacking: Tuple[int]  # list of players who have stopped attacking
    available_actions: Tuple[int]  # list of available actions

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
            self.available_actions,
        ))


class GameTransition(NamedTuple):
    state: ObservableDurakGameState
    action: int
    reward: float
    next_state: ObservableDurakGameState
