from game import DurakGame
from agents import RandomPlayer


def main(*args, **kwargs):
    print(args, kwargs)
    gconfig = {
        'game_num_players': 3,
        'lowest_card': 6,
        'agents': [RandomPlayer, RandomPlayer, RandomPlayer],
    }
    game = DurakGame()
    game.configure(gconfig)
    game.init_game()
    while not game.is_done:
        transition = game.step()
    print(game.players)
    print(transition)


if __name__ == '__main__':
    main()
