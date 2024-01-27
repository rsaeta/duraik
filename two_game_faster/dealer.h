#include <string>
#include <vector>
#include <queue>

namespace Dealer
{

enum class suit_t : unsigned char {
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

class Dealer {
public:
  Dealer();
  void printHand(std::vector<Card> &hand);
  std::deque<Card> makeDeck();
  void printDeck();
  void dealCards(int numCards, std::vector<Card> *hand);
  void shuffleDeck();
  std::deque<Card> getDeck() {
    return deck;
  }

  private:
  std::deque<Card> deck;
};

};
