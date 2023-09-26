import mcts_simple
from agents.mcts_lib import MCTSGame

mcts = mcts_simple.OpenLoopMCTS(MCTSGame())
mcts.self_play(100)
mcts.save('mcts_simple.pkl')
