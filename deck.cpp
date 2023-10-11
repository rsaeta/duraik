#include <iostream>
#include <algorithm>
#include <random>
#include <vector>
#include <string>
#include <iterator>

enum class Suit {
    CLUBS,
    DIAMONDS,
    HEARTS,
    SPADES,
};

struct Card {
    int value;
    Suit suit;
};

class Deck {
    Card arrCards[36];
    std::mt19937 rng;
    int nCards;

    public:
    Deck() {
        rng = std::mt19937{std::random_device{}()};
        nCards = 36;
    }

    void SetupCards() {
        for (int i = (int)Suit::CLUBS; i<= (int)Suit::SPADES; i++) {
            for (int j = 6; j <= 14; j++) {
                Card c;
                c.suit = (Suit)i;
                c.value = j;
            }
        }
        nCards = 36;
    }

    void Shuffle() {
        std::shuffle(std::begin(arrCards), std::end(arrCards), rng);
    }

    Card* Take(int n) {
        Card cards[n];
        for (int i = 0; i < n; i++) {
            cards[i] = arrCards[nCards - i - 1];
        }
        nCards -= n;
        return(cards);
    }

    void Print() {
        for (int i = 0; i < nCards; i++) {
            std::cout << arrCards[i].value << " " << (int)arrCards[i].suit << std::endl;
        }
    }
};

int main() {
    Deck deck;
    deck.SetupCards();
    deck.Shuffle();
    deck.Print();
}