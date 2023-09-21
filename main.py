from game import DurakGame
from agents import RandomPlayer, MCTSPlayer


def main():
    gconfig = {
        'game_num_players': 3,
        'lowest_card': 6,
        'agents': [RandomPlayer, MCTSPlayer, RandomPlayer],
    }
    game = DurakGame()
    game.configure(gconfig)
    game.init_game()
    while not game.is_done:
        game.step()
    print(game.players)


if __name__ == '__main__':
    main()
