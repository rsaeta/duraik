#include "game.h"

using namespace std;

namespace Player {

class IPlayer {
  public:
    virtual int chooseAction(DurakGame::PlayerGameState playerGameState, vector<int> *legalActions) = 0;
    virtual void observeAction(int action, DurakGame::PlayerGameState playerGameState) {}
};

class RandomPlayer : public IPlayer {
  public:
    int chooseAction(DurakGame::PlayerGameState playerGameState, vector<int> *legalActions) override {
        return (*legalActions)[rand()%legalActions->size()];
    };
};

};
