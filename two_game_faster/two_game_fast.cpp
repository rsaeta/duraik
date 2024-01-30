#include "player.h"
#include "game_runner.h"
#include <iostream>

using namespace std;
using namespace durak_game;

int main() {
  Player::RandomPlayer player0;
  Player::RandomPlayer player1;

  GameRunner *gameRunner = new GameRunner(&player0, &player1);

  gameRunner->runGame();
  delete gameRunner;
  return 0;
}
