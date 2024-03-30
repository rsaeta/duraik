use numpy::ndarray::Array1;
use pyo3::{pyclass, pymethods, PyResult};

use crate::game::cards::{self, Card};

use super::utils::{indices_to_bitmap, indices_to_bitmap_as_array1};

#[pyclass(name = "Card")]
#[derive(Clone)]
pub struct CardPy {
    #[pyo3(get)]
    pub suit: String,
    #[pyo3(get)]
    pub rank: u8,
}

#[pymethods]
impl CardPy {
    #[new]
    pub fn new(suit: String, rank: u8) -> Self {
        CardPy { suit, rank }
    }

    pub fn __repr__(&self) -> PyResult<String> {
        let rank_str = match self.rank {
            11 => "J".to_string(),
            12 => "Q".to_string(),
            13 => "K".to_string(),
            14 => "A".to_string(),
            _ => self.rank.to_string(),
        };
        Ok(format!("{}{}", rank_str, self.suit))
    }

    pub fn __str__(&self) -> PyResult<String> {
        let rank_str = match self.rank {
            11 => "J".to_string(),
            12 => "Q".to_string(),
            13 => "K".to_string(),
            14 => "A".to_string(),
            _ => self.rank.to_string(),
        };
        Ok(format!("{}{}", rank_str, self.suit))
    }
}

impl From<CardPy> for u8 {
    fn from(value: CardPy) -> Self {
        let suit = match value.suit.as_str() {
            "\x1b[90m♠️\x1b[0m" => 0,
            "\x1b[31m♥️\x1b[0m" => 1,
            "\x1b[90m♣️\x1b[0m" => 2,
            "\x1b[31m♦️\x1b[0m" => 3,
            _ => 5,
        };
        (suit * 9) + value.rank - 6
    }
}

impl From<u8> for CardPy {
    fn from(value: u8) -> Self {
        let suit_val = (value / 9) as u8;
        let suit = match suit_val {
            0 => "♠".to_string(),
            1 => "♥".to_string(),
            2 => "♦".to_string(),
            3 => "♣".to_string(),
            _ => panic!("Invalid suit number"),
        };
        let rank = (value % 9) + 6;
        CardPy { suit, rank }
    }
}

impl std::fmt::Debug for CardPy {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        let rank_str = match self.rank {
            11 => "J".to_string(),
            12 => "K".to_string(),
            13 => "Q".to_string(),
            14 => "A".to_string(),
            _ => self.rank.to_string(),
        };
        write!(f, "{}{}", rank_str, self.suit)
    }
}

impl From<Card> for CardPy {
    fn from(card: Card) -> Self {
        CardPy {
            suit: match card.suit {
                cards::Suit::Spades => "\x1b[90m♠️\x1b[0m".to_string(),
                cards::Suit::Hearts => "\x1b[31m♥️\x1b[0m".to_string(),
                cards::Suit::Clubs => "\x1b[90m♣️\x1b[0m".to_string(),
                cards::Suit::Diamonds => "\x1b[31m♦️\x1b[0m".to_string(),
            },
            rank: card.rank,
        }
    }
}

pub struct HandPy<'a>(pub &'a Vec<CardPy>);

impl Into<Vec<u8>> for HandPy<'_> {
    fn into(self) -> Vec<u8> {
        indices_to_bitmap(
            self.0
                .iter()
                .map(|card| <CardPy as Into<u8>>::into(<CardPy as Clone>::clone(&*card)) as usize)
                .collect(),
            36,
        )
    }
}

impl Into<Array1<u8>> for HandPy<'_> {
    fn into(self) -> Array1<u8> {
        Array1::from_vec(self.into())
    }
}
