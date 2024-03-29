from durak_rt.rust import Card, GameEnv
import numpy as np

class RandomPlayer:
    def __init__(self, player_id):
        self.player_id = player_id
        self.np_random = np.random.RandomState()

    def choose_action(self, state, actions, full_state=None):
        print(f"Actions: {actions}")
        print(f"State: {state}")
        choice = self.np_random.choice(len(actions))
        print(f"Chose action: {actions[choice]}")
        return choice
    
game = GameEnv(RandomPlayer(1))
game.play()
breakpoint() 