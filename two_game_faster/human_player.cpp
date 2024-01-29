#include <iostream>
#include "player.h"
#include "dealer.h"

using namespace std;
using namespace Cards;

namespace Player {

void printActions(vector<int> *actions) {
  for (int i = 0; i<actions->size(); i++) {
    cout << i << ": " << durak_game::actionToString((*actions)[i]) << endl;
  }
}

int HumanPlayer::chooseAction(durak_game::PlayerGameState *state, vector<int> *legalActions) {
  int res = -1;
  int ubound = legalActions->size();
  while (res < 0 || res > ubound) {
    cout << "$$$$$$$$$$$$$$$$$$$$\nHand: ";
    Cards::printHand(state->hand);

    cout << "Attack Table: ";
    Cards::printHand(state->attackTable);

    cout << "Defend Table: ";
    Cards::printHand(state->defendTable);

    cout << "Visible Card: " << state->visibleCard->to_string() << endl;
    cout << "Cards in opponents hand: " << state->cardsInOpponentHand << endl;;
    cout << "Cards in deck: " << state->cardsInDeck << endl;
    cout << "Defender has taken: " << state->defenderHasTaken << endl;
    cout << "Attacker has stopped: " << state->attackerHasStopped << endl;

    cout << "ACTIONS:" << endl;
    printActions(legalActions);

    cout << "Choose: ";
    cin >> res;
  }

  return res;
}


} // namespace Player
