from abc import ABC


class Env(ABC):
    """
    This defines an abstract environment class that all RL games should adhere to
    """

    def __init__(self):
        pass

    def reset(self):
        """
        Reset the environment to its initial state
        """
        raise NotImplementedError

    def step(self, action):
        """
        Take a step in the environment
        :param action: the action to take
        :return: a tuple of (reward, next_state, done)
        """
        raise NotImplementedError

    def get_state_size(self):
        """
        Get the size of the state
        :return: the size of the state
        """
        raise NotImplementedError

    def get_legal_actions(self):
        """
        Get the legal actions for the current player
        :return: a list of legal actions
        """
        raise NotImplementedError

    def get_current_player(self):
        """
        Get the current player
        :return: the current player
        """
        raise NotImplementedError

    def get_num_players(self):
        """
        Get the number of players in the three_game
        :return: the number of players
        """
        raise NotImplementedError

    def get_state(self):
        """
        Get the current state of the three_game
        :return: the current state
        """
        raise NotImplementedError

    def get_current_player_id(self):
        """
        Get the current player id
        :return: the current player id
        """
        raise NotImplementedError

    def get_players(self):
        """
        Get the players
        :return: the players
        """
        raise NotImplementedError
