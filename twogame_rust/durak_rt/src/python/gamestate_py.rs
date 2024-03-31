use numpy::ndarray::concatenate;
use numpy::PyArray1;
use numpy::{ndarray::Array1, Ix1, PyArray};
use pyo3::exceptions::PyException;
use pyo3::{pyclass, pymethods, PyErr, PyResult, Python};

use crate::game::gamestate::{GamePlayer, ObservableGameState};

use super::card_py::{CardPy, HandPy};
use super::utils::indices_to_bitmap_as_array1;

#[pyclass(name = "ObservableGameState")]
pub struct ObservableGameStatePy {
    #[pyo3(get)]
    pub acting_player: u8,
    #[pyo3(get)]
    pub player_hand: Vec<CardPy>,
    #[pyo3(get)]
    pub attack_table: Vec<CardPy>,
    #[pyo3(get)]
    pub defense_table: Vec<CardPy>,
    #[pyo3(get)]
    pub deck_size: u8,
    #[pyo3(get)]
    pub visible_card: CardPy,
    #[pyo3(get)]
    pub defender_has_taken: bool,
    #[pyo3(get)]
    pub defender: u8,
    #[pyo3(get)]
    pub cards_in_opp_hand: u8,
}

#[pyclass(name = "GamePlayer")]
pub struct GamePlayerPy {
    #[pyo3(get)]
    pub player: u8,
}

impl From<GamePlayer> for u8 {
    fn from(player: GamePlayer) -> Self {
        match player {
            GamePlayer::Player1 => 0,
            GamePlayer::Player2 => 1,
        }
    }
}

impl From<ObservableGameState> for ObservableGameStatePy {
    fn from(state: ObservableGameState) -> Self {
        let player_hand = state.hand.0.iter().map(|c| CardPy::from(*c)).collect();
        let attack_table = state
            .attack_table
            .iter()
            .map(|c| CardPy::from(*c))
            .collect();
        let defense_table = state
            .defense_table
            .iter()
            .map(|c| CardPy::from(*c))
            .collect();
        let visible_card = CardPy::from(state.visible_card);
        ObservableGameStatePy {
            acting_player: u8::from(state.acting_player), // 2
            player_hand,                                  // 36
            attack_table,                                 // 36
            defense_table,                                // 36
            deck_size: state.num_cards_in_deck,           // 1
            visible_card,                                 // 36
            defender_has_taken: state.defender_has_taken, // 1
            defender: u8::from(state.defender),           // 2
            cards_in_opp_hand: state.cards_in_opponent,   // 1
        }
    }
}

// impl for a ObservableGameState reference
impl From<&ObservableGameState> for ObservableGameStatePy {
    fn from(state: &ObservableGameState) -> Self {
        let player_hand = state.hand.0.iter().map(|c| CardPy::from(*c)).collect();
        let attack_table = state
            .attack_table
            .iter()
            .map(|c| CardPy::from(*c))
            .collect();
        let defense_table = state
            .defense_table
            .iter()
            .map(|c| CardPy::from(*c))
            .collect();
        let visible_card = CardPy::from(state.visible_card);
        ObservableGameStatePy {
            acting_player: u8::from(state.acting_player),
            player_hand,
            attack_table,
            defense_table,
            deck_size: state.num_cards_in_deck,
            visible_card,
            defender_has_taken: state.defender_has_taken,
            defender: u8::from(state.defender),
            cards_in_opp_hand: state.cards_in_opponent,
        }
    }
}

#[pymethods]
impl ObservableGameStatePy {
    pub fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
          // gamestate but with new-lines so everythign lines up well
            "GameState(\n  Acting player: {},\n  Player hand: {:?},\n  Attack table: {:?},\n  Defense table: {:?},\n  Deck size: {},\n  Visible card: {:?},\n  Defender has taken: {},\n  Defender: {},\n  Cards in opponent's hand: {}\n)",
            self.acting_player, self.player_hand, self.attack_table, self.defense_table, self.deck_size, self.visible_card, self.defender_has_taken, self.defender, self.cards_in_opp_hand
        ))
    }

    pub fn __str__(&self) -> PyResult<String> {
        Ok(format!(
            "GameState(\n  Acting player: {},\n  Player hand: {:?},\n  Attack table: {:?},\n  Defense table: {:?},\n  Deck size: {},\n  Visible card: {:?},\n  Defender has taken: {},\n  Defender: {},\n  Cards in opponent's hand: {}\n)",
            self.acting_player, self.player_hand, self.attack_table, self.defense_table, self.deck_size, self.visible_card, self.defender_has_taken, self.defender, self.cards_in_opp_hand
        ))
    }

    pub fn to_numpy(&self) -> PyResult<pyo3::Py<PyArray<u8, Ix1>>> {
        let hand_arr = <HandPy as Into<Array1<u8>>>::into(HandPy(&self.player_hand));
        let player_acting_arr = indices_to_bitmap_as_array1(vec![self.acting_player as usize], 2);
        let attack_table_arr = <HandPy as Into<Array1<u8>>>::into(HandPy(&self.attack_table));
        let defense_table_arr = <HandPy as Into<Array1<u8>>>::into(HandPy(&self.defense_table));
        let visible_card_arr =
            <HandPy as Into<Array1<u8>>>::into(HandPy(&vec![<CardPy as Clone>::clone(
                &self.visible_card,
            )]));
        let defender_arr = indices_to_bitmap_as_array1(vec![self.defender as usize], 2);
        let defender_has_taken_arr = Array1::from_vec(vec![self.defender_has_taken as u8]);
        let deck_size_arr = Array1::from_vec(vec![self.deck_size]);
        let cards_in_opp_arr = Array1::from_vec(vec![self.cards_in_opp_hand]);
        match concatenate(
            numpy::ndarray::Axis(0),
            &[
                player_acting_arr.view(),
                hand_arr.view(),
                attack_table_arr.view(),
                defense_table_arr.view(),
                deck_size_arr.view(),
                visible_card_arr.view(),
                defender_has_taken_arr.view(),
                defender_arr.view(),
                cards_in_opp_arr.view(),
            ],
        ) {
            Ok(a) => Ok(Python::with_gil(|py| {
                PyArray1::from_array(py, &a).to_owned()
            })),
            Err(_) => Err(PyErr::new::<PyException, _>("Shape error")),
        }
    }
}
