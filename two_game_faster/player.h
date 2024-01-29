#include <iostream>
#include "game.h"

using namespace std;

namespace Player {

class IPlayer {
  public:
    virtual int chooseAction(durak_game::PlayerGameState *playerGameState, vector<int> *legalActions) = 0;
    virtual void observeAction(int action, durak_game::PlayerGameState *playerGameState) {}
};

class RandomPlayer : public IPlayer {
  public:
    int chooseAction(durak_game::PlayerGameState *playerGameState, vector<int> *legalActions) override {
      std::cout<<"In .h file" << std::endl;
      return (*legalActions)[rand()%legalActions->size()];
    };
};

};
