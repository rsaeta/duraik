import os
import sys
import torch
from pathlib import Path

from agents import RandomPlayer, DQNPlayer

from two_game import game, GameState, Card


def main(seed, save_dir=None, run_game=True):
    lowest_rank = 11
    if save_dir is None:
        save_dir = Path(f'heads_up_histories_sanity_checks_{lowest_rank}')
    os.makedirs(save_dir, exist_ok=True)

    game_runner = game.GameRunner()
    game_runner.set_agents([RandomPlayer(0), RandomPlayer(1)])
    initial_state = GameState(
        deck=[],  # [Card("S", 11), Card("H", 11), Card("D", 11), Card("C", 11)],
        visible_card=Card("S", 11),
        hands=tuple([
            tuple([Card("S", 14), Card("H", 14), Card("D", 14), Card("C", 14), Card("C", 12), Card("H", 12)]),
            tuple([Card("S", 13), Card("H", 13), Card("D", 13), Card("C", 13), Card("S", 12), Card("D", 12)]),
        ]),
        player_taking_action=0,
        defend_table=tuple(),
        attack_table=tuple(),
        defender=1,
        graveyard=tuple(),
        defender_has_taken=False,
        is_done=False,
    )
    game_runner.run(init_state=initial_state)
    run_save_dir = save_dir / f'run_{seed}'
    print(game_runner.reward_history[-1])
    return game_runner.reward_history[-1][0]


if __name__ == '__main__':
    num_iters = 10000
    x = 0
    for i in range(num_iters):
        x += main(i*3//2)
    print(x/num_iters)
