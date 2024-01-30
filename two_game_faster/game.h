#pragma once
#include "dealer.h"
#include <set>

using namespace std;
using namespace Cards;

namespace durak_game {

// number of actions in the game total
const int numActions();
// identifier to take action
const int takeAction = 0;
// identifier to stop attack action
const int stopAttackAction = 1;
// get the action number of attacking with a card
int attackAction(Card &card);
// get the action number of defending with a card
int defendAction(Card &card);
// get the card from an action number
Card cardFromAction(int action);
// get a string representation of an action number
string actionToString(int action);

// Holds the entire state of the game (private to the game)
typedef struct GameState {
  // deck of cards
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
  vector<Card> *hand;
  vector<Card> *attackTable;
  vector<Card> *defendTable;
  vector<Card> *graveyard;
  Card *visibleCard;
  bool isDone;
  int playerTackingAction;
  bool defenderHasTaken;
  bool attackerHasStopped;
  int defender;
  int cardsInOpponentHand;
} PlayerGameState;

class DurakGameC {
  public:
  DurakGameC();
  void step(int action);
  void render();
  GameState *getGameState();
  vector<int> legalActions();
  static PlayerGameState *getPlayerGameState(int player, GameState *gameState);
  static int reward(int player, GameState *gameState);
  
  private:
  // Holds all data about the game
  GameState gameState;

  void handleAttack(int action);
  void handleDefend(int action);
  void handleTake();
  void handleStopAttack();
  bool isRoundOver();

  vector<int> legalDefenderActions();
  vector<int> legalAttackerActions();

  void removeCardFromHand(Card *card, int player);
  vector<Card> *currentPlayerHand();
  vector<Card> *attackerHand();
  vector<Card> *defenderHand();
 
  void ranksInPlay(set<int> *outSet);
  void addTableCardsToVector(vector<Card> *v);
  bool isGameOver();
};

};
