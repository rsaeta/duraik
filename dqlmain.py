from pathlib import Path

from three_game import DurakGame, DurakAction
from agents import RandomPlayer, DQAgent


def main(*args, **kwargs):
    print(args, kwargs)
    gconfig = {
        'game_num_players': 3,
        'lowest_card': 6,
        'agents': [RandomPlayer, RandomPlayer, lambda i: DQAgent(
            150, DurakAction.num_actions(), i
        )],
        'save_dir': 'game_history',
    }

    game = DurakGame()
    game.configure(gconfig)
    game.init_game()
    wins = 0

    for i in range(200):
        game.reset_game()
        print('playing three_game ', i)
        while not game.is_done:
            game.step()
        game.save_history(Path('histories'))
        if len(game.player_hands[2]) == 0:
            wins += 1
        print(game.player_hands)
        #for _ in range(5):
        #    three_game.players[2].update()
        # three_game.players[2].save()
        print('win rate: ', wins / (i + 1))


if __name__ == '__main__':
    main()
