#include <iostream>
#include "player.h"

using namespace std;
using namespace Player;

class RandomPlayer : public IPlayer {
  public:
    int chooseAction(durak_game::PlayerGameState *playerGameState, vector<int> *legalActions) override {
        int index = rand()%legalActions->size();
        cout << "Choosing " << std::to_string(index) << " action" << endl;
        return (*legalActions)[rand()%legalActions->size()];
    }

    void observeAction(int action, durak_game::PlayerGameState *playerGameState) override { }
};