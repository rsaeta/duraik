#include <iostream>
#include <string>
#include <vector>
#include <queue>
#include <random>
#include <algorithm>

#include "dealer.h"

using namespace Cards;
using namespace std;

string suit_t_to_string(suit_t s) {
  switch (s) {
    case suit_t::Hearts: return "H";
    case suit_t::Diamonds: return "D";
    case suit_t::Clubs: return "C";
    case suit_t::Spades: return "S";
  }
  return NULL;
}

string Cards::Card::to_string() {
  string s = suit_t_to_string(suit);
  return s + std::to_string(rank);
}

bool Cards::Card::operator<(const Card &b) const {
  if (rank == b.rank) {
    return suit < b.suit;
  }
  return rank < b.rank;
}

bool Cards::Card::operator==(const Card &b) const {
  return rank == b.rank && suit == b.suit;
}

void Cards::printDeck(deque<Card> *deck) {
  cout << "[";
  for (int i=0; i<deck->size(); i++) {
    cout << (*deck)[i].to_string();
    if ((*deck)[i].rank == 10) {
      cout << " ";
    } else {
      cout << "  ";
    }
  }
  cout << "]" << endl;
}

void Cards::makeDeck(deque<Card> *inDeque)
{
    int lowestRank = 6;
    for (int i = 0; i < 4; i++)
    {
        for (int j = lowestRank; j <= 14; j++)
        {
            inDeque->push_back(Card((suit_t)i, j));
        }
    }
}

void Cards::printHand(vector<Card> *hand) {
  cout << "[";
  for (int i=0; i<hand->size(); i++) {
    cout << (*hand)[i].to_string();
    if ((*hand)[i].rank == 10) {
      cout << " ";
    } else {
      cout << "  ";
    }
  }
  cout << "]\n";
}

void Cards::shuffleDeck(deque<Card> *deck) {
  std::random_device rd;
  std::mt19937 g(rd());
  shuffle(deck->begin(), deck->end(), g);
}

void Cards::dealCards(int numCards, deque<Card> *deck, vector<Card> *cards) {
  numCards = deck->size() >= numCards ? numCards : deck->size();
  for (int i=0; i<numCards; i++) {
    (*cards).push_back(deck->front());
    deck->pop_front();
  }
}
