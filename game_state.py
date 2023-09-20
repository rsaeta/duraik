import dataclasses
from typing import List


@dataclasses.dataclass
class ObservableDurakGameState:
    """
    DurakGameState is a dataclass that stores the state of the game.
    """
    hand: List[tuple]  # list of cards in hand
    visible_card: tuple  # the visible card on the table determining the trump suit
    attack_table: List[tuple]  # list of attacking cards on the table
    defend_table: List[tuple]  # list of defending cards on the table
    num_cards_left_in_deck: int  # number of cards left in the deck
    num_cards_left_in_opponent_hands: List[int]  # number of cards left in the opponent's hand
    graveyard: List[tuple]  # list of cards in the graveyard
    is_done: bool  # whether the game is done

    def __str__(self):
        return f"""
        hand: {sorted(self.hand, key=lambda x: x[1])}
        visible_card: {self.visible_card}
        attack_table: {self.attack_table}
        defend_table: {self.defend_table}
        num_cards_left_in_deck: {self.num_cards_left_in_deck}
        num_cards_left_in_opponent_hands: {self.num_cards_left_in_opponent_hands}
        graveyard: {self.graveyard}
        is_done: {self.is_done}
        """

    def __repr__(self):
        return str(self)
