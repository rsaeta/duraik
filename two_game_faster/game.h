#include "dealer.h"
#include <set>

using namespace std;
using namespace Dealer;

namespace DurakGame {

const int numActions();
const int takeAction = 0;
const int stopAttackAction = 1;
int attackAction(Card &card);
int defendAction(Card &card);
Card cardFromAction(int action);
string actionToString(int action);

typedef struct GameState {
  deque<Card> deck;
  vector<Card> player1Cards;
  vector<Card> player2Cards;
  Card visibleCard;
  vector<Card> attackTable;
  vector<Card> defendTable;
  vector<Card> graveyard;
  int playerTackingAction;
  int defender;
  bool defenderHasTaken;
  bool attackerHasStopped;
  bool isDone;
} GameState;

typedef struct PlayerGameState {
  int player;
  int cardsInDeck;
  vector<Card> hand;
  vector<Card> attackTable;
  vector<Card> defendTable;
  vector<Card> graveyard;
  bool isDone;
  int playerTackingAction;
  bool defenderHasTaken;
  int defender;
  int cardsInOpponentHand;
} PlayerGameState;

class DurakGame {
public:
    DurakGame();
    void step(int action);
    void render();
    GameState getGameState();
    vector<int> legalActions();
    static PlayerGameState getPlayerGameState(int player, GameState gameState);
private:
    Dealer::Dealer dealer;
    GameState gameState;
    void handleAttack(int action);
    void handleDefend(int action);
    void handleTake();
    void handleStopAttack();
    bool isRoundOver();
    vector<int> legalDefenderActions();
    vector<int> legalAttackerActions();
    void removeCardFromHand(Card &card, int player);
    vector<Card> currentPlayerHand();
    vector<Card> *attackerHand();
    vector<Card> *defenderHand();
    void postAction();
    set<int> ranksInPlay();
    void addTableCardsToVector(vector<Card> *v);
};

};
