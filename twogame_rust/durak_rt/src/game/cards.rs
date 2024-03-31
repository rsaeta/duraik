use core::fmt;

use rand::seq::SliceRandom;

#[derive(Clone, Copy, PartialEq, Debug, Eq, Ord, PartialOrd)]
pub enum Suit {
    Spades,
    Hearts,
    Diamonds,
    Clubs,
}

impl From<Suit> for u8 {
    fn from(value: Suit) -> Self {
        match value {
            Suit::Spades => 0,
            Suit::Hearts => 1,
            Suit::Diamonds => 2,
            Suit::Clubs => 3,
        }
    }
}

impl Suit {
    pub fn to_num(&self) -> u8 {
        match self {
            Suit::Spades => 0,
            Suit::Hearts => 1,
            Suit::Diamonds => 2,
            Suit::Clubs => 3,
        }
    }
}

impl From<u8> for Suit {
    fn from(num: u8) -> Self {
        match num {
            0 => Suit::Spades,
            1 => Suit::Hearts,
            2 => Suit::Diamonds,
            3 => Suit::Clubs,
            _ => panic!("Invalid suit number"),
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Ord, PartialOrd)]
pub struct Card {
    pub suit: Suit,
    pub rank: u8,
}

impl From<Card> for u8 {
    fn from(value: Card) -> Self {
        (u8::from(value.suit) * 9) + value.rank - 6
    }
}

impl From<u8> for Card {
    fn from(value: u8) -> Self {
        let suit = Suit::from((value / 9) as u8);
        let rank = (value % 9) + 6;
        Card { suit, rank }
    }
}

impl fmt::Debug for Card {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let suit = match self.suit {
            Suit::Spades => "♠",
            Suit::Hearts => "♥",
            Suit::Diamonds => "♦",
            Suit::Clubs => "♣",
        };
        let rstr = self.rank.to_string();
        let rank = match self.rank {
            11 => "J",
            12 => "Q",
            13 => "K",
            14 => "A",
            _ => rstr.as_str(),
        };
        write!(f, "{}{}", rank, suit)
    }
}

#[derive(Clone)]
pub struct Hand(pub Vec<Card>);

impl PartialEq for Hand {
    fn eq(&self, other: &Self) -> bool {
        let mut sorted_self = self.0.clone();
        let mut sorted_other = other.0.clone();
        sorted_self.sort();
        sorted_other.sort();
        sorted_self == sorted_other
    }
}

impl fmt::Debug for Hand {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // sort based on suit then rank
        let mut sorted_hand = self.0.clone();
        sorted_hand.sort();
        write!(f, "{:?}", sorted_hand)
    }
}

#[derive(Clone, PartialEq)]
pub struct Deck {
    cards: Vec<Card>,
}

impl fmt::Debug for Deck {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:?}", self.cards)
    }
}

impl Deck {
    pub fn new(lowest_rank: u8) -> Deck {
        let mut cards = Vec::new();
        for suit in [Suit::Spades, Suit::Hearts, Suit::Diamonds, Suit::Clubs].iter() {
            for rank in lowest_rank..15 {
                cards.push(Card {
                    suit: suit.clone(),
                    rank,
                });
            }
        }
        Deck { cards: cards }
    }

    pub fn len(&self) -> usize {
        self.cards.len()
    }

    pub fn shuffle(&mut self) {
        let mut rng = rand::thread_rng();
        self.cards.shuffle(&mut rng);
    }

    fn draw(&mut self) -> Option<Card> {
        self.cards.pop()
    }

    pub fn draw_n(&mut self, n: usize) -> Vec<Card> {
        let mut drawn = Vec::new();
        for _ in 0..n {
            match self.draw() {
                Some(card) => drawn.push(card),
                None => break,
            }
        }
        drawn
    }

    pub fn get_first(&self) -> Option<Card> {
        self.cards.first().cloned()
    }
}
