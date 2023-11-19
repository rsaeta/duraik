from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np
import os
import glob
import pickle
from pathlib import Path

from two_game.game import ObservableGameState


class ExperienceReplay(ABC):
    @abstractmethod
    def sample(
        self, batch_size: int = 1
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Sample a batch of experiences from the replay buffer. This should be a tuple of
        (s, a, r, s') where s and s' are the states before and after the action a was taken.
        These should have dimensions
        np.ndarray of shape (batch_size, ..., observation_size) where the columns are:
        """
        raise NotImplementedError


class DirectoryBasedExperiencedReplayWithHistory(ExperienceReplay):
    """
    This implementation of ExperienceReplay expects a directory of numpy files, each of which
    represents a single play through a game. To incorporate history, the state s and s' are
    given as a sequence of observable states, where the most recent state is the last element.
    As a result, the shape of the s is (sequence_length, *observable_state_shape) and s' is
    (sequence_length+1, *observable_state_shape). The action a is a single integer, and r is
    a single float.

    This expects the directory of runs to contain directories, each with 3 files:
    * actions.npy - A numpy array of shape (sequence_length,) containing the action ID's taken
    * rewards.npy - A numpy array of shape (sequence_length,) containing the rewards received
    * obs.npy - A numpy array of shape (num_players, sequence_length, *observable_state_shape)
     containing the observable states for each player.
    """

    def __init__(self, directory: Path):
        self.directory = directory

    def sample(
        self, batch_size: int = 1
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        This really only implements a batch size of 1 at the moment.
        """
        run_dir = self._find_sample_directory()
        print(f"Loading run {self.directory / run_dir}")
        actions, rewards, obs = self._load_run(run_dir)

        n_players, seq_len, *obs_shape = obs.shape
        print(
            f"Found {n_players} players, {seq_len} steps, and {obs_shape} observation shape"
        )

        assert n_players == 2

        starting_index = np.random.randint(seq_len - 1)
        print(f"Sampling from starting index {starting_index}")
        ending_index = self._find_ending_index(obs, starting_index)

        obs_state = ObservableGameState.from_array(obs[0, ending_index, :])
        acting_player = obs_state.player_taking_action

        print(
            f"Ending index is {ending_index} with acting player"
            f" {obs_state.player_taking_action} and action {actions[starting_index]}"
        )
        # Now either ending_index is the end of the game, or the acting player is the same as starting index
        s = obs[acting_player, :starting_index, :]  # [starting_index, *obs_shape]
        s_prime = obs[acting_player, :ending_index, :]  # [ending_index, *obs_shape]

        assert s_prime.shape == (
            s.shape[0] + (ending_index - starting_index),
            s.shape[1],
        )

        a = actions[starting_index]
        r = rewards[ending_index - 1]
        return s, a, r, s_prime

    def _find_sample_directory(self):
        """
        Samples a directory from the directory of runs.
        """
        run_dirs = glob.glob(str(self.directory / "run_*"))
        run_dir = Path(np.random.choice(run_dirs))
        return run_dir

    def _load_run(self, run_dir: Path):
        actions = np.load(run_dir / "actions.npy")
        rewards = np.load(run_dir / "rewards.npy")
        obs = np.load(run_dir / "obs.npy")
        return actions, rewards, obs

    @staticmethod
    def _find_ending_index(obs: np.array, starting_index: int) -> int:
        """
        This finds the ending index given the starting index where the ending index is the first subsequent
        state where the same player is taking action as in the starting index.
        """
        init_state = obs[0, starting_index, :]
        init_obs_state = ObservableGameState.from_array(init_state)
        acting_player = init_obs_state.player_taking_action
        ending_index = starting_index + 1
        obs_state = ObservableGameState.from_array(obs[0, ending_index, :])
        while not obs_state.is_done and obs_state.player_taking_action != acting_player:
            ending_index += 1
            obs_state = ObservableGameState.from_array(obs[0, ending_index, :])
        return ending_index
