#include <iostream>
#include "player.h"

using namespace std;

namespace Player {

int RandomPlayer::chooseAction(durak_game::PlayerGameState *playerGameState, std::vector<int> *legalActions) {
  int index = rand()%legalActions->size();
  cout << "Choosing " << std::to_string(index) << " action in .cpp file" << endl;
  return (*legalActions)[rand()%legalActions->size()];
}

};
