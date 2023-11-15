from three_game import DurakGame, DurakAction, DurakDeck
from agents import RandomPlayer, MCTSPlayer
from test_duraik_game import get_normal_random_game


def test_mcts():
    game = get_normal_random_game()
    hands = [
        [('S', 6), ('H', 12), ('D', 14), ('S', 7)],
        [('C', 6), ('C', 14)],
        [('D', 6), ('D', 11)],
    ]

    mcts_player = MCTSPlayer(0, hand=[])
    game.players[0] = mcts_player

    visible_card = ('S', 9)
    for player, hand in zip(game.players, hands):
        player.hand = hand
    game.visible_card = visible_card
    game.player_taking_action = 0
    game.defender = 1
    game.attackers = [0]
    game.is_done = False
    game.deck.deck = []
    game.graveyard = DurakDeck.deck_without(hands[0] + hands[1] + hands[2]).new_deck
    game.step()

if __name__ == '__main__':
    test_mcts()
