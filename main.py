from three_game import DurakGame
from agents import RandomPlayer, HumanPlayer


def main(*args, **kwargs):
    print(args, kwargs)
    gconfig = {
        'game_num_players': 3,
        'lowest_card': 6,
        'agents': [RandomPlayer, RandomPlayer, HumanPlayer],
    }
    game = DurakGame()
    game.configure(gconfig)
    game.init_game()
    while not game.is_done:
        game.step()
    print(game.players)


if __name__ == '__main__':
    main()
