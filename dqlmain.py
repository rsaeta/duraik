from game import DurakGame, DurakAction
from agents import RandomPlayer, DQAgent


def main(*args, **kwargs):
    print(args, kwargs)
    gconfig = {
        'game_num_players': 3,
        'lowest_card': 6,
        'agents': [RandomPlayer, RandomPlayer, lambda i, hand: DQAgent(
            150, DurakAction.num_actions(), i, hand=hand
        )],
    }

    game = DurakGame()
    game.configure(gconfig)
    game.init_game()

    game.players[2].load()

    for i in range(200):
        game.reset_game()
        print('playing game ', i)
        while not game.is_done:
            game.step()
        print(game.players)
        for _ in range(5):
            game.players[2].update()
        game.players[2].save()


if __name__ == '__main__':
    main()
