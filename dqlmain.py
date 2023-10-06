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
    wins = 0

    for i in range(200):
        game.reset_game()
        print('playing game ', i)
        while not game.is_done:
            game.step()
        if len(game.players[2].hand) == 0:
            wins += 1
        print(game.players)
        for _ in range(5):
            game.players[2].update()
        game.players[2].save()
        print('win rate: ', wins / (i + 1))


if __name__ == '__main__':
    main()
