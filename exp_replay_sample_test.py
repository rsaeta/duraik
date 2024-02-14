from agents.dqn import DirectoryBasedExperiencedReplayWithHistory
from pathlib import Path


def main():
    history_dir = Path('heads_up_histories_11')
    replay = DirectoryBasedExperiencedReplayWithHistory(history_dir)
    d = history_dir / 'run_0'
    actions, rewards, obs = replay._load_run(d)
    s, a, r, s_prime = replay.sample()
    while 1 not in r:
        s, a, r, s_prime = replay.sample()
    print('got one')


def train_agent(config: dict):
    """
    This trains an agent using the given configuration.
    :param config: A dictionary of configuration options.
    """
    replay = DirectoryBasedExperiencedReplayWithHistory(Path(config.get("history_dir", "heads_up_histories_11")))
    agent = DQAgentWithHistory(
        observation_shape=observable_state_shape,
        n_actions=num_actions,
        latent_dim=config.get("latent_dim", 128),
        hidden_dim=config.get("hidden_dim", 256),
        depth=config.get("depth", 2),
    )
    opt = torch.optim.Adam(agent.parameters(), lr=config.get("lr", 1e-3))
    loss_fn = nn.MSELoss()
    for i in range(config.get("num_iters", 100)):
        opt.zero_grad()
        s, a, r, s_prime = replay.sample(batch_size=config.get("batch_size", 1))
        q_values = agent(s)
        q_values_prime = agent(s_prime)
        q_values_prime_max = torch.max(q_values_prime, dim=1)[0]
        q_values_target = q_values.clone()
        q_values_target[:, a] = r + config.get("gamma", 0.9) * q_values_prime_max
        loss = loss_fn(q_values, q_values_target)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if i % 100 == 0:
            print(f"Iteration {i} loss: {loss.item()}")



if __name__ == '__main__':
    main()
