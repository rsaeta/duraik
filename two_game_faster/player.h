#include <iostream>
#include "game.h"

using namespace std;

namespace Player {

class IPlayer {
public:
  virtual ~IPlayer() {};
  virtual void observeAction(int action, durak_game::PlayerGameState *playerGameState) {};
  virtual int chooseAction(durak_game::PlayerGameState *playerGameState, std::vector<int> *legalActions) = 0;
};

class RandomPlayer : public IPlayer {
  int chooseAction(durak_game::PlayerGameState *playerGameState, std::vector<int> *legalActions) override;
};

class HumanPlayer : public IPlayer {
  int chooseAction(durak_game::PlayerGameState *playerGameState, std::vector<int> *legalActions) override;
};

}