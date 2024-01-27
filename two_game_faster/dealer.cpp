#include <iostream>
#include <string>
#include <vector>
#include <queue>
#include <random>
#include <algorithm>

#include "dealer.h"

using namespace Dealer;
using namespace std;

auto suit_t_to_string(suit_t s) -> string {
  switch (s) {
    case suit_t::Hearts: return "H";
    case suit_t::Diamonds: return "D";
    case suit_t::Clubs: return "C";
    case suit_t::Spades: return "S";
  }
  return NULL;
}

string Dealer::Card::to_string() {
  string s = suit_t_to_string(suit);
  return s + std::to_string(rank);
}

bool Dealer::Card::operator<(const Card &b) const {
  if (rank == b.rank) {
    return suit < b.suit;
  }
  return rank < b.rank;
}

bool Dealer::Card::operator==(const Card &b) const {
  return rank == b.rank && suit == b.suit;
}

Dealer::Dealer::Dealer() {
  deck = makeDeck();
}

void Dealer::Dealer::printDeck() {
  cout << "[";
  for (int i=0; i<deck.size(); i++) {
    cout << deck[i].to_string();
    if (deck[i].rank == 10) {
      cout << " ";
    } else {
      cout << "  ";
    }
  }
  cout << "]" << endl;
}

deque<Card> Dealer::Dealer::makeDeck() {
  deque<Card> my_deck;
  int lowestRank = 6;
  for (int i=0; i<4; i++) {
    for (int j=lowestRank; j<=14; j++) {
      my_deck.push_back(Card((suit_t)i, j));
    }
  }
  
  return my_deck;
}

void Dealer::Dealer::printHand(vector<Card> &hand) {
  cout << "[";
  for (int i=0; i<hand.size(); i++) {
    cout << hand[i].to_string();
    if (hand[i].rank == 10) {
      cout << " ";
    } else {
      cout << "  ";
    }
  }
  cout << "]\n";
}

void Dealer::Dealer::shuffleDeck() {
  random_shuffle(deck.begin(), deck.end());
}

void Dealer::Dealer::dealCards(int numCards, vector<Card> *cards) {
  for (int i=0; i<numCards; i++) {
    (*cards).push_back(deck.front());
    deck.pop_front();
  }
}
