#include "player.h"
#include <iostream>

using namespace std;
using namespace DurakGame;

void printVector(vector<int> *v) {
  cout << "[";
  for (int i = 0; i < v->size(); i++) {
    cout << (*v)[i] << " ";
  }
  cout << "]" << endl;
}

void runGame(DurakGame::DurakGame *game, Player::IPlayer *player0, Player::IPlayer *player1) {
  DurakGame::GameState gameState = game->getGameState();
  game->render();
  int iters = 100;
  for (int i = 0; i < iters; i++) {
    cout << "############  Iteration " << i << endl;
    Player::IPlayer *player = gameState.playerTackingAction == 0 ? player0 : player1;
    vector<int> legalActions = game->legalActions();
    cout << "Legal actions: ";
    printVector(&legalActions);
    int action = player->chooseAction(game->getPlayerGameState(gameState.playerTackingAction, gameState), &legalActions);
    cout << "Player " << gameState.playerTackingAction << " chose action " << DurakGame::actionToString(action) << endl;
    game->step(action);
    player->observeAction(action, game->getPlayerGameState(gameState.playerTackingAction, gameState));
    cout << "======= New State =======" << endl;
    gameState = game->getGameState();
    game->render();
  }
}

int main() {
  srand(10);
  DurakGame::DurakGame *game = new DurakGame::DurakGame();
  Player::IPlayer *player0 = new Player::RandomPlayer();
  Player::IPlayer *player1 = new Player::RandomPlayer();
  runGame(game, player0, player1);
  return 0;
}
