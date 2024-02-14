#include "game.h"
#include <algorithm>
#include <iostream>
#include <string>
#include <set>


using namespace std;
using namespace Cards;

namespace durak_game {

const int numCards = (15-6)*4;

const int numActions() {
  // Take, Stop Attack, Attack, Defend
  return 2 + numCards*2;
}

int cardToOrder(Card &card) {
  return (card.rank-6) + (int)card.suit*9;
}

int attackAction(Card &card) {
  return 2 + cardToOrder(card);
}

int defendAction(Card &card) {
  return 2 + numCards + cardToOrder(card);
}

int otherPlayer(int player) {
    return (player+1)%2;
}

int playerBeginAction(vector<Card> &hand0, vector<Card> &hand1, suit_t trumpSuit) {
    // TODO
    return 0;
}

bool isTakeAction(int action) {
    return action == 0;
}

bool isStopAttackAction(int action) {
    return action == 1;
}

bool isAttackAction(int action) {
    return action >= 2 && action < 2 + numCards;
}

bool isDefendAction(int action) {
    return action >= 2 + numCards && action < 2 + numCards*2;
}

Card cardFromAction(int action) {
    action -= 2;
    action = action % numCards;

    int suit = action/9;
    int rank = action%9 + 6;
    return Card((suit_t)suit, rank);
}

std::string actionToString(int action) {
    if (isTakeAction(action)) {
        return "Take";
    } else if (isStopAttackAction(action)) {
        return "Stop Attack";
    } else if (isAttackAction(action)) {
        return "ATTACK(" + cardFromAction(action).to_string() + ")";
    } else if (isDefendAction(action)) {
        return "DEFEND(" + cardFromAction(action).to_string() + ")";
    } else {
        return "Invalid Action";
    }
}

DurakGameC::DurakGameC() {
  Cards::makeDeck(&gameState.deck);
  Cards::shuffleDeck(&gameState.deck);
  Cards::dealCards(6, &gameState.deck, &gameState.player1Cards);
  Cards::dealCards(6, &gameState.deck, &gameState.player2Cards);
  gameState.visibleCard = gameState.deck.back();
  gameState.attackTable = vector<Card>();
  gameState.defendTable = vector<Card>();
  gameState.graveyard = vector<Card>();
  gameState.playerTackingAction = playerBeginAction(gameState.player1Cards, gameState.player2Cards, gameState.visibleCard.suit);
  gameState.defender = otherPlayer(gameState.playerTackingAction);
  gameState.defenderHasTaken = false;
  gameState.attackerHasStopped = false;
  gameState.isDone = false;
}

vector<int> DurakGameC::legalDefenderActions() {
  int numDefend = gameState.defendTable.size();
  if (numDefend >= gameState.attackTable.size()) {
    cout << "Got more defenders than attackers" << endl;
    return vector<int>();
  }
  suit_t trumpSuit = gameState.visibleCard.suit;
  Card attackCard = gameState.attackTable[numDefend];
  vector<int> actions;
  actions.push_back(takeAction);
  vector<Card> *hand = defenderHand();
  for (int i=0; i<hand->size(); i++) {
    Card card = (*hand)[i];
    if (card.suit == attackCard.suit && card.rank > attackCard.rank) {
      actions.push_back(defendAction(card));
    } else if (card.suit == trumpSuit && attackCard.suit != trumpSuit) {
      actions.push_back(defendAction(card));
    }
  }
  return actions;
}

void DurakGameC::ranksInPlay(set<int> *ranks) {
  for (int i=0; i<gameState.attackTable.size(); i++) {
    ranks->insert(gameState.attackTable[i].rank);
  }
  for (int i=0; i<gameState.defendTable.size(); i++) {
    ranks->insert(gameState.defendTable[i].rank);
  }
}

vector<Card> *DurakGameC::currentPlayerHand() {
  return gameState.playerTackingAction == 0 
      ? &gameState.player1Cards
      : &gameState.player2Cards;
}

vector<int> DurakGameC::legalAttackerActions() {
  vector<int> actions;

  if (gameState.attackTable.empty()) {
    cout << "Attacker has not attacked yet" << endl;
    vector<Card> *hand = currentPlayerHand();
    for (int i=0; i<hand->size(); i++) {
      actions.push_back(attackAction(hand->at(i)));
    }
    return actions;
  }

  actions.push_back(stopAttackAction);
  if (gameState.attackTable.size() - gameState.defendTable.size() == defenderHand()->size()) {
    // Can not attack more if there are not enough cards in defender hand
    return actions;
  }

  set<int> ranks;
  ranksInPlay(&ranks);
  for (Card card : *currentPlayerHand()) {
    if (ranks.find(card.rank) != ranks.end()) {  // if rank of card is in play, can attack with it
      actions.push_back(attackAction(card));
    }
  }

  return actions;
}

vector<int> DurakGameC::legalActions() {
  if (gameState.playerTackingAction == gameState.defender) {
    return legalDefenderActions();
  }
  return legalAttackerActions();
}

void DurakGameC::removeCardFromHand(Card *card, int player) {
  vector<Card> *hand = player == 0 ? &gameState.player1Cards : &gameState.player2Cards;
  for (std::vector<Card>::iterator iter = hand->begin(); iter != hand->end(); ++iter) {
    if (*iter == *card) {
      hand->erase(iter);
      break;
    }
  }
}

void DurakGameC::handleAttack(int action) {
  Card card = cardFromAction(action);
  gameState.attackTable.push_back(card);
  // remove card from hand
  removeCardFromHand(&card, gameState.playerTackingAction);
}

void DurakGameC::handleDefend(int action) {
  Card card = cardFromAction(action);
  gameState.defendTable.push_back(card);
  removeCardFromHand(&card, gameState.playerTackingAction);
  if (gameState.attackTable.size() == gameState.defendTable.size()) {
    if (gameState.attackTable.size() == 6 || defenderHand()->size() == 0) {  
      // Reached max, successful defense give cards to graveyard
      addTableCardsToVector(&gameState.graveyard);

      // Deal cards to attacker
      vector<Card> *attHand = attackerHand();
      int numCardsToDeal = 6 - attHand->size();
      Cards::dealCards(numCardsToDeal, &gameState.deck, attHand);

      // Deal cards to defender
      vector<Card> *defHand = defenderHand();
      numCardsToDeal = 6 - defHand->size();
      Cards::dealCards(numCardsToDeal, &gameState.deck, defHand);

      // Reset defenderHasTaken and attackerHasStopped
      gameState.defenderHasTaken = false;
      gameState.attackerHasStopped = false;

      // Swap attacker/defender
      gameState.defender = otherPlayer(gameState.defender);
      gameState.playerTackingAction = otherPlayer(gameState.defender);
    } else {
      // Player can attack again
      gameState.playerTackingAction = otherPlayer(gameState.playerTackingAction);  
    }
  } 
  // else: player must defend again
}

void DurakGameC::addTableCardsToVector(vector<Card> *v) {
  // Utility to add table cards to a vector (can be hand or graveyard)
  v->insert(v->end(), gameState.attackTable.begin(), gameState.attackTable.end());
  v->insert(v->end(), gameState.defendTable.begin(), gameState.defendTable.end());

  // Clear table cards
  gameState.attackTable = vector<Card>();
  gameState.defendTable = vector<Card>();
}

void DurakGameC::handleTake() {
  gameState.defenderHasTaken = true;
  // Check if attacker can add cards
  if (gameState.attackTable.size() - gameState.defendTable.size() < defenderHand()->size()) {
    gameState.playerTackingAction = otherPlayer(gameState.playerTackingAction);
  } else {
    // Give cards in attackDeck and defendDeck to defender
    vector<Card> *defHand = defenderHand();
    addTableCardsToVector(defHand);

    // Reset defenderHasTaken and attackerHasStopped
    gameState.defenderHasTaken = false;
    gameState.attackerHasStopped = false;

    // Make sure next to act is still the same attacker as before
    gameState.playerTackingAction = otherPlayer(gameState.defender);

    // Deal cards to attacker
    vector<Card> *attHand = attackerHand();
    int numCardsToDeal = 6 - attHand->size();
    Cards::dealCards(numCardsToDeal, &gameState.deck, attHand);
  }
}

void DurakGameC::handleStopAttack() {
  gameState.attackerHasStopped = true;
  if (gameState.defenderHasTaken) { 
    // defender has taken, give cards in attackDeck and defendDeck to defender
    vector<Card> *defHand = defenderHand();
    addTableCardsToVector(defHand);

    // Reset defenderHasTaken and attackerHasStopped
    gameState.defenderHasTaken = false;
    gameState.attackerHasStopped = false;

    // Deal cards to attacker
    vector<Card> *attHand = attackerHand();
    int numCardsToDeal = 6 - attHand->size();
    Cards::dealCards(numCardsToDeal, &gameState.deck, attHand);

  } else if (gameState.attackTable.size() == gameState.defendTable.size()) { 
    // Successful defense, give cards in attackDeck and defendDeck to graveyard
    addTableCardsToVector(&gameState.graveyard);

    // Reset defenderHasTaken and attackerHasStopped
    gameState.defenderHasTaken = false;
    gameState.attackerHasStopped = false;

    // Deal cards to attacker
    vector<Card> *attHand = attackerHand();
    int numCardsToDeal = 6 - attHand->size();
    dealCards(numCardsToDeal, &gameState.deck, attHand);

    // Deal cards to defender
    vector<Card> *defHand = defenderHand();
    numCardsToDeal = 6 - defHand->size();
    Cards::dealCards(numCardsToDeal, &gameState.deck, defHand);

    // Swap attacker/defender
    gameState.playerTackingAction = otherPlayer(gameState.playerTackingAction);
    gameState.defender = otherPlayer(gameState.defender);
  } else {
    // Player must try to defend
    gameState.playerTackingAction = gameState.defender;
  }
}

bool DurakGameC::isRoundOver() {
  return gameState.defenderHasTaken || gameState.attackerHasStopped || (gameState.attackTable.size() == 6 && gameState.defendTable.size() == 6);
}

vector<Card> *DurakGameC::attackerHand() {
    return gameState.defender == 0 ? &gameState.player2Cards : &gameState.player1Cards;
}

vector<Card> *DurakGameC::defenderHand() {
    return gameState.defender == 0 ? &gameState.player1Cards : &gameState.player2Cards;
}

void DurakGameC::step(int action) {
  if (isTakeAction(action)) {
    handleTake();
  } else if (isStopAttackAction(action)) {
    handleStopAttack();
  } else if (isAttackAction(action)) {
    handleAttack(action);
  } else if (isDefendAction(action)) {
    handleDefend(action);
  } else {
    cout << "Invalid action: " << action << endl;
  }
  gameState.isDone = isGameOver();
}

bool DurakGameC::isGameOver() {
  return gameState.deck.size() == 0 && 
    (gameState.player1Cards.size() == 0 || gameState.player2Cards.size() == 0);
}

void DurakGameC::render() {
  // Prints out the gameState in a nice way
  cout << "Deck: ";
  Cards::printDeck(&gameState.deck);
  cout << "Player 1 Hand: ";
  Cards::printHand(&gameState.player1Cards);
  cout << "Player 2 Hand: ";
  Cards::printHand(&gameState.player2Cards);
  cout << "Attack Table: ";
  Cards::printHand(&gameState.attackTable);
  cout << "Defend Table: ";
  Cards::printHand(&gameState.defendTable);
  cout << "Graveyard: ";
  Cards::printHand(&gameState.graveyard);
  cout << "Visible Card: " << gameState.visibleCard.to_string() << endl;
  cout << "Defender has taken: " << gameState.defenderHasTaken << endl;
  cout << "Attacker has stopped: " << gameState.attackerHasStopped << endl;
  cout << "Player Tacking Action: " << gameState.playerTackingAction << endl;
}

GameState *DurakGameC::getGameState() {
  return &gameState;
}

PlayerGameState *DurakGameC::getPlayerGameState(int player, GameState *gameState) {
  PlayerGameState *pgs = new PlayerGameState();
  pgs->player = player;
  pgs->cardsInDeck = gameState->deck.size();
  pgs->hand = player == 0 ? &gameState->player1Cards : &gameState->player2Cards;
  pgs->attackTable = &gameState->attackTable;
  pgs->defendTable = &gameState->defendTable;
  pgs->graveyard = &gameState->graveyard;
  pgs->visibleCard = &gameState->visibleCard;
  pgs->isDone = gameState->isDone;
  pgs->playerTackingAction = gameState->playerTackingAction;
  pgs->defenderHasTaken = gameState->defenderHasTaken;
  pgs->attackerHasStopped = gameState->attackerHasStopped;
  pgs->defender = gameState->defender;
  vector<Card> *oppHand = player == 0 ? &gameState->player2Cards : &gameState->player1Cards;
  pgs->cardsInOpponentHand = oppHand->size();
  return pgs;
}

int DurakGameC::reward(int player, GameState *gameState) {
  if (!gameState->isDone) {
    return 0;
  }

  vector<Card> *hand = player == 0 ? &gameState->player1Cards : &gameState->player2Cards;
  return hand->size() == 0 ? 1 : -1;
}

};