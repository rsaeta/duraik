#include "player.h"
#include <iostream>

using namespace std;
using namespace durak_game;

void printVector(vector<int> *v, std::function<string(int)> func) {
  cout << "[";
  for (int i = 0; i < v->size(); i++) {
    cout << func((*v)[i]) << " ";
  }
  cout << "]" << endl;
}

void runGame(durak_game::DurakGameC *game, Player::IPlayer *player0, Player::IPlayer *player1) {
  durak_game::GameState *gameState = game->getGameState();
  game->render();
  int iters = 0;
  while (!gameState->isDone) {
    cout << "############  Iteration " << iters << endl;
    Player::IPlayer *player = gameState->playerTackingAction == 0 ? player0 : player1;
    vector<int> legalActions = game->legalActions();
    cout << "Legal actions: ";
    printVector(&legalActions, &durak_game::actionToString);
    int action = player->chooseAction(game->getPlayerGameState(gameState->playerTackingAction, gameState), &legalActions);
    cout << "Player " << gameState->playerTackingAction << " chose action " << durak_game::actionToString(action) << endl;
    game->step(action);
    player->observeAction(action, game->getPlayerGameState(gameState->playerTackingAction, gameState));
    cout << "======= New State =======" << endl;
    gameState = game->getGameState();
    game->render();
    iters++;
  }

  cout << "Player 1 reward: " << game->reward(0, gameState) << endl;
  cout << "Player 2 reward: " << game->reward(1, gameState) << endl;
}

int main() {
  srand(100);
  cout << "In main" << endl;
  durak_game::DurakGameC *game = new durak_game::DurakGameC();
  Player::HumanPlayer randPlayer0;
  Player::RandomPlayer randPlayer1;
  Player::IPlayer *player0 = &randPlayer0;
  Player::IPlayer *player1 = &randPlayer1;
  runGame(game, player0, player1);
  return 0;
}
