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
  durak_game::GameState gameState = game->getGameState();
  game->render();
  int iters = 100;
  for (int i = 0; i < iters; i++) {
    cout << "############  Iteration " << i << endl;
    Player::IPlayer *player = gameState.playerTackingAction == 0 ? player0 : player1;
    vector<int> legalActions = game->legalActions();
    cout << "Legal actions: ";
    printVector(&legalActions, &durak_game::actionToString);
    int action = player->chooseAction(game->getPlayerGameState(gameState.playerTackingAction, gameState), &legalActions);
    cout << "Player " << gameState.playerTackingAction << " chose action " << durak_game::actionToString(action) << endl;
    game->step(action);
    player->observeAction(action, game->getPlayerGameState(gameState.playerTackingAction, gameState));
    cout << "======= New State =======" << endl;
    gameState = game->getGameState();
    game->render();
    if (gameState.isDone) {
      break;
    }
  }
}

int main() {
  srand(100);
  cout << "In main" << endl;
  durak_game::DurakGameC *game = new durak_game::DurakGameC();
  Player::IPlayer *player0 = new Player::RandomPlayer();
  Player::IPlayer *player1 = new Player::RandomPlayer();
  runGame(game, player0, player1);
  return 0;
}
