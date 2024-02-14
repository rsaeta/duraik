from pathlib import Path

from two_game import GameRunner, num_actions, observable_state_shape
from agents import RandomPlayer, DQAgent


def main(*args, **kwargs):
    print(args, kwargs)
    dqagent = DQAgent(observable_state_shape(), num_actions(), 1)
    rand_agent = RandomPlayer(0)
    wins = 0

    for i in range(200):
        game = GameRunner()
        game.set_agents([rand_agent, dqagent])
        print('playing game ', i)
        game.play()
        if len(game.player_hands[2]) == 0:
            wins += 1
        print(game.player_hands)
        #for _ in range(5):
        #    three_game.players[2].update()
        # three_game.players[2].save()
        print('win rate: ', wins / (i + 1))


if __name__ == '__main__':
    main()
