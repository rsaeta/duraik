use game::{
    actions::Action,
    cards::{self, Card},
    game::{Game, GameLogic, GamePlayer, ObservableGameState, Player, RandomPlayer},
};
use pyo3::{exceptions::PyException, prelude::*};
mod game;

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

#[pyclass(name = "GameEnv", unsendable)]
pub struct GameEnvPy {
    game: Box<Game>,
    player1: Box<PyPlayer>,
}

impl Into<GamePlayer> for u8 {
    fn into(self) -> GamePlayer {
        match self {
            1 => GamePlayer::Player1,
            2 => GamePlayer::Player2,
            _ => panic!("Invalid player number"),
        }
    }
}

struct PyPlayer(Py<PyAny>);

impl Player for PyPlayer {
    fn choose_action(
        &mut self,
        state: ObservableGameState,
        actions: Vec<Action>,
        history: Vec<ObservableGameState>,
    ) -> Action {
        let state_py = ObservableGameStatePy::from(state);
        let actions_py: Vec<String> = actions.iter().map(|a| format!("{:?}", a)).collect();
        let history_py: Vec<ObservableGameStatePy> = history
            .iter()
            .map(|x| ObservableGameStatePy::from(x))
            .collect();

        let res = Python::with_gil(|py| {
            let action = (*self)
                .0
                .call_method(
                    py,
                    "choose_action",
                    (state_py, actions_py, history_py),
                    None,
                )
                .unwrap();
            action.extract::<u8>(py).unwrap()
        });
        actions[res as usize]
    }
}

#[pymethods]
impl GameEnvPy {
    #[new]
    pub fn new(player1: Py<PyAny>) -> Self {
        GameEnvPy {
            game: Box::new(Game::new()),
            player1: Box::new(PyPlayer(player1)),
        }
    }

    pub fn play(&mut self) -> PyResult<(f32, f32)> {
        let mut p2 = Box::new(RandomPlayer::new(None)) as Box<dyn Player>;
        let p1 = &mut self.player1; // Box::new(PyPlayer(player1)) as Box<dyn Player>;
        let mut game_over = false;
        while !game_over {
            let pta = self.game.game_state.acting_player;
            let actions = self.game.legal_actions();
            let player = match pta {
                GamePlayer::Player1 => p1.as_mut(),
                GamePlayer::Player2 => p2.as_mut(),
            };
            let history = self.game.history.iter().map(|x| x.observe(pta)).collect();
            let action = player.choose_action(self.game.game_state.observe(pta), actions, history);
            match self.game.step(action) {
                Ok(_) => (),
                Err(_e) => (),
            };

            game_over = self.game.is_over();
        }
        Ok(self.game.get_rewards())
    }
}

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

use numpy::{
    ndarray::{concatenate, Array1},
    Ix1, PyArray, PyArray1,
};

struct HandPy<'a>(&'a Vec<CardPy>);

fn indices_to_bitmap(indices: Vec<usize>, total_size: usize) -> Vec<u8> {
    let mut bitmap = vec![0; total_size];
    for idx in indices {
        bitmap[idx] = 1;
    }
    bitmap
}

fn indices_to_bitmap_as_array1(indices: Vec<usize>, total_size: usize) -> Array1<u8> {
    let mut bitmap = Array1::zeros(total_size);
    for idx in indices {
        bitmap[idx] = 1;
    }
    bitmap
}

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
        let deck_size_arr = Array1::from_vec(vec![self.deck_size]);
        let cards_in_opp_arr = Array1::from_vec(vec![self.cards_in_opp_hand]);
        let res = match concatenate(
            numpy::ndarray::Axis(0),
            &[
                hand_arr.view(),
                player_acting_arr.view(),
                attack_table_arr.view(),
                defense_table_arr.view(),
                visible_card_arr.view(),
                defender_arr.view(),
                deck_size_arr.view(),
                cards_in_opp_arr.view(),
            ],
        ) {
            Ok(a) => Ok(Python::with_gil(|py| {
                PyArray1::from_array(py, &a).to_owned()
            })),
            Err(_) => Err(PyErr::new::<PyException, _>("Shape error")),
        };
        res
    }
}

#[pyclass(name = "GamePlayer")]
pub struct GamePlayerPy {
    #[pyo3(get)]
    pub player: u8,
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

impl From<GamePlayer> for u8 {
    fn from(player: GamePlayer) -> Self {
        match player {
            GamePlayer::Player1 => 1,
            GamePlayer::Player2 => 2,
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

#[pymodule]
#[pyo3(name = "rust")]
pub fn rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<CardPy>()?;
    m.add_class::<GameEnvPy>()?;
    m.add_class::<ObservableGameStatePy>()?;
    Ok(())
}
