import os
import sys
import torch
from pathlib import Path

from agents import RandomPlayer, DQNPlayer

from two_game import game


def main(seed, save_dir=None):
    lowest_rank = 11
    if save_dir is None:
        save_dir = Path(f'heads_up_histories_{lowest_rank}')
    os.makedirs(save_dir, exist_ok=True)
    game_runner = game.GameRunner()
    game_runner.set_agents([RandomPlayer(0), DQNPlayer(1)])
    game_runner.run(seed)
    run_save_dir = save_dir / f'run_{seed}'
    # game_runner.save_run(run_save_dir)


if __name__ == '__main__':
    num_iters = 10
    for i in range(num_iters):
        main(i*3//2)
