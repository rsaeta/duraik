from typing import NamedTuple, Literal

suit = Literal['S', 'H', 'D', 'C']


class DurakCard(NamedTuple):
    rank: int
    suit: suit

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def __repr__(self):
        return str(self)


def new_deck():
    return [DurakCard(r, s) for s in ['S', 'H', 'D', 'C'] for r in range(6, 15)]
