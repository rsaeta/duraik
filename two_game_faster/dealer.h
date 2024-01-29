#include <string>
#include <vector>
#include <queue>

namespace Cards
{

enum suit_t {
  Clubs,
  Diamonds,
  Hearts,
  Spades,
};

class Card {
public:
  Card() : suit(suit_t::Hearts), rank(0) {}
  Card(suit_t s, unsigned int r) : suit(s), rank(r) {}
  ~Card() {}
  suit_t suit;
  int rank = -1;
  std::string to_string();
  bool operator<(const Card &a) const;
  bool operator==(const Card &a) const;
};

void printHand(std::vector<Card> *hand);
void makeDeck(std::deque<Cards::Card> *inDeque);
void printDeck(std::deque<Cards::Card> *deck);
void dealCards(int numCards, std::deque<Card> *deck, std::vector<Card> *hand);
void shuffleDeck(std::deque<Cards::Card> *deck);

};
