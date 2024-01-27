import os
import sys
import torch
from pathlib import Path
from tqdm import tqdm

from agents import RandomPlayer, DQNPlayer, UpdateArgs, DirectoryBasedExperiencedReplayWithHistory

from two_game import game, GameState, Card, new_state

num_saved_games = 5000

optimizer_sd = torch.load('saved_models/heads_up_harder_9/optimizer.pt')
scheduler_sd = torch.load('saved_models/heads_up_harder_9/scheduler.pt')
dqn_agent_sd = torch.load('saved_models/heads_up_harder_9/dqn_agent.pt')

dqn_agent = DQNPlayer(0)
dqn_agent.load_state_dict(dqn_agent_sd)
dqn_agent.to(torch.device('cuda'))
optimizer = torch.optim.Adam(dqn_agent.parameters(), lr=1e-3)
optimizer.load_state_dict(optimizer_sd)
loss_fn = torch.nn.MSELoss().to(torch.device('cuda'))
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=100, gamma=0.99)
scheduler.load_state_dict(scheduler_sd)
replay = DirectoryBasedExperiencedReplayWithHistory(Path('heads_up_histories_sanity_checks_harder_9'))
batch_size = 1


def main(seed, save_dir=None, run_game=True):
    lowest_rank = 9
    if save_dir is None:
        save_dir = Path(f'heads_up_histories_sanity_checks_harder_{lowest_rank}')
    os.makedirs(save_dir, exist_ok=True)
    if run_game:
        game_runner = game.GameRunner()
        game_runner.set_agents([dqn_agent, RandomPlayer(1)])
        initial_state = new_state(seed, lowest_rank)
        game_runner.run(init_state=initial_state)
        run_save_dir = save_dir / f'run_{seed % num_saved_games}'
        game_runner.save_run(run_save_dir)
    update_args = UpdateArgs(optimizer, scheduler, loss_fn, replay, 10, 0.999)
    dqn_agent.update(update_args)

    if torch.rand(1) < 0.001:
        print('Saving models')
        # save model, optimizer, and scheduler
        torch.save(dqn_agent.state_dict(), 'saved_models/heads_up_harder_9_longer/dqn_agent.pt')
        torch.save(optimizer.state_dict(), 'saved_models/heads_up_harder_9_longer/optimizer.pt')
        torch.save(scheduler.state_dict(), 'saved_models/heads_up_harder_9_longer/scheduler.pt')


if __name__ == '__main__':
    num_iters = 500000
    x = 0
    for i in tqdm(range(num_iters)):
        x += main(i*3//2) or 0
    print(x/num_iters)
