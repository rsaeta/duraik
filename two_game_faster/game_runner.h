#pragma once
#include "game.h"
#include "player.h"

namespace durak_game {

class GameRunner {
public:
  GameRunner(Player::IPlayer *player0, Player::IPlayer *player1);
  GameRunner(DurakGameC *game, Player::IPlayer *player0, Player::IPlayer *player1);
  void runGame();
private:
  DurakGameC *game;
  Player::IPlayer *player0;
  Player::IPlayer *player1;
};

} // namespace durak_game
