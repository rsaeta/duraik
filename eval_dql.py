import os
import sys
import torch
from pathlib import Path
from tqdm import tqdm

from agents import (
    RandomPlayer,
    DQNPlayer,
    UpdateArgs,
    HumanPlayer as Human,
    DirectoryBasedExperiencedReplayWithHistory,
)

from two_game import game, GameState, Card, new_state

dqn_agent = DQNPlayer(0)
agent_state_dict = torch.load("saved_models/heads_up_harder_9/dqn_agent.pt")
dqn_agent.load_state_dict(agent_state_dict)
dqn_agent.to(torch.device("cuda"))
dqn_agent.eval()


def main(seed, save_dir=None):
    lowest_rank = 9
    if save_dir is None:
        save_dir = Path(f"heads_up_histories_sanity_checks_harder_{lowest_rank}_longer_eval")
    os.makedirs(save_dir, exist_ok=True)
    initial_state = new_state(seed, lowest_rank)
    game_runner = game.GameRunner()
    game_runner.set_agents([dqn_agent, RandomPlayer(1)])
    reward, _ = game_runner.run(init_state=initial_state)
    run_save_dir = save_dir / f"run_{seed}"
    #game_runner.save_run(run_save_dir)
    #print(reward)
    return reward


if __name__ == "__main__":
    num_iters = 5000
    x = 0
    for i in tqdm(range(num_iters)):
        r = main(i * 3 // 2) or 0
        if r > 0:
            x += 1
    print(x / num_iters)
