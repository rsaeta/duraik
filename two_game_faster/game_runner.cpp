#include "game_runner.h"

namespace durak_game {

GameRunner::GameRunner(Player::IPlayer *player0, Player::IPlayer *player1) {
  this->game = new DurakGameC();
  this->player0 = player0;
  this->player1 = player1;
}

GameRunner::GameRunner(DurakGameC *game, Player::IPlayer *player0, Player::IPlayer *player1) {
  this->game = game;
  this->player0 = player0;
  this->player1 = player1;
}

void GameRunner::runGame() {
  GameState *gameState = game->getGameState();
  game->render();
  int iters = 0;
  while (!gameState->isDone) {
    cout << "############  Iteration " << iters << endl;
    Player::IPlayer *player = gameState->playerTackingAction == 0 ? player0 : player1;
    vector<int> legalActions = game->legalActions();    
    int action = player->chooseAction(game->getPlayerGameState(gameState->playerTackingAction, gameState), &legalActions);
    cout << "Player " << gameState->playerTackingAction << " chose action " << actionToString(action) << endl;
    game->step(action);
    player->observeAction(action, game->getPlayerGameState(gameState->playerTackingAction, gameState));
    cout << "======= New State =======" << endl;
    gameState = game->getGameState();
    game->render();
    iters++;
  }

  cout << "Player 1 reward: " << game->reward(0, gameState) << endl;
  cout << "Player 2 reward: " << game->reward(1, gameState) << endl;

  delete gameState;
}

} // namespace durak_game