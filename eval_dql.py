import os
import sys
import torch
from pathlib import Path

from agents import (
    RandomPlayer,
    DQNPlayer,
    UpdateArgs,
    HumanPlayer as Human,
    DirectoryBasedExperiencedReplayWithHistory,
)

from two_game import game, GameState, Card

dqn_agent = DQNPlayer(0)
agent_state_dict = torch.load("models/dqn_agent.pt")
dqn_agent.load_state_dict(agent_state_dict)
dqn_agent.to(torch.device("cuda"))
dqn_agent.eval()


def main(seed, save_dir=None):
    lowest_rank = 11
    if save_dir is None:
        save_dir = Path(f"heads_up_histories_sanity_checks_{lowest_rank}_eval")
    os.makedirs(save_dir, exist_ok=True)

    game_runner = game.GameRunner()
    game_runner.set_agents([dqn_agent, Human(1)])
    initial_state = GameState(
        deck=[],  # [Card("S", 11), Card("H", 11), Card("D", 11), Card("C", 11)],
        visible_card=Card("S", 11),
        hands=tuple(
            [
                tuple(
                    [
                        Card("S", 14),
                        Card("H", 14),
                        Card("D", 14),
                        Card("C", 14),
                        Card("C", 12),
                        Card("H", 12),
                    ]
                ),
                tuple(
                    [
                        Card("S", 13),
                        Card("H", 13),
                        Card("D", 13),
                        Card("C", 13),
                        Card("S", 12),
                        Card("D", 12),
                    ]
                ),
            ]
        ),
        player_taking_action=0,
        defend_table=tuple(),
        attack_table=tuple(),
        defender=1,
        graveyard=tuple(),
        defender_has_taken=False,
        is_done=False,
    )
    reward, _ = game_runner.run(init_state=initial_state)
    run_save_dir = save_dir / f"run_{seed}"
    game_runner.save_run(run_save_dir)
    print(reward)


if __name__ == "__main__":
    num_iters = 1
    x = 0
    for i in range(num_iters):
        x += main(i * 3 // 2) or 0
    print(x / num_iters)
