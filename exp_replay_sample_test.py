from agents.dqn import DirectoryBasedExperiencedReplayWithHistory
from pathlib import Path


def main():
    history_dir = Path('heads_up_histories_11')
    replay = DirectoryBasedExperiencedReplayWithHistory(history_dir)
    d = history_dir / 'run_0'
    actions, rewards, obs = replay._load_run(d)



if __name__ == '__main__':
    main()
