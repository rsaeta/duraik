use game::Action;
use game::Card;
use game::GameLogic;
use game::GamePlayer;
use game::Player;
use pyo3::prelude::*;
use rand::SeedableRng;
mod game;

use crate::game::Game;
use crate::game::ObservableGameState;
use crate::game::RandomPlayer;

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
        Ok(format!("{}{}", self.rank, self.suit))
    }

    pub fn __str__(&self) -> PyResult<String> {
        Ok(format!("{}{}", self.rank, self.suit))
    }
}

impl std::fmt::Debug for CardPy {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}{}", self.rank, self.suit)
    }
}

#[pyclass(name = "GameEnv", unsendable)]
pub struct GameEnvPy {
    game: Game,
    player1: Py<PyAny>,
    player2: Box<dyn Player>,
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

fn get_p1_move(env: &mut GameEnvPy) -> Action {
    let state = env.game.game_state.observe(GamePlayer::Player1);
    let actions = env.game.legal_actions();
    let py_actions: Vec<String> = actions.iter().map(|a| format!("{:?}", a)).collect();
    let history: Vec<ObservableGameStatePy> = env
        .game
        .history
        .iter()
        .map(|x| x.observe(GamePlayer::Player1))
        .map(|x| x.into())
        .collect();
    let res = Python::with_gil(|py| {
        let action = env
            .player1
            .call_method(
                py,
                "choose_action",
                (ObservableGameStatePy::from(state), py_actions, history),
                None,
            )
            .unwrap();
        action.extract::<u8>(py).unwrap()
    });
    actions[res as usize]
}

#[pymethods]
impl GameEnvPy {
    #[new]
    pub fn new(player1: Py<PyAny>) -> Self {
        GameEnvPy {
            game: Game::new(),
            player1,
            player2: Box::new(RandomPlayer::new(None)),
        }
    }

    pub fn play(&mut self) -> PyResult<(f32, f32)> {
        // reimplement the logic loop here
        let mut game_over = false;
        while !game_over {
            let pta = self.game.game_state.acting_player;
            let actions = self.game.legal_actions();
            let history = self.game.history.iter().map(|x| x.observe(pta)).collect();
            let action = match pta {
                GamePlayer::Player1 => get_p1_move(self),
                GamePlayer::Player2 => {
                    self.player2
                        .choose_action(self.game.game_state.observe(pta), actions, history)
                }
            };
            match self.game.step(action) {
                Ok(_) => (),
                Err(e) => (),
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
}

#[pymethods]
impl ObservableGameStatePy {
    pub fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
            "GameState(Acting player: {}, Player hand: {:?}, Attack table: {:?}, Defense table: {:?}, Deck size: {}, Visible card: {:?}, Defender has taken: {}, Defender: {})",
            self.acting_player, self.player_hand, self.attack_table, self.defense_table, self.deck_size, self.visible_card, self.defender_has_taken, self.defender
        ))
    }

    pub fn __str__(&self) -> PyResult<String> {
        Ok(format!(
            "GameState(Acting player: {}, Player hand: {:?}, Attack table: {:?}, Defense table: {:?}, Deck size: {}, Visible card: {:?}, Defender has taken: {}, Defender: {})",
            self.acting_player, self.player_hand, self.attack_table, self.defense_table, self.deck_size, self.visible_card, self.defender_has_taken, self.defender
        ))
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
                game::Suit::Spades => "S".to_string(),
                game::Suit::Hearts => "H".to_string(),
                game::Suit::Clubs => "C".to_string(),
                game::Suit::Diamonds => "D".to_string(),
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
        }
    }
}

#[pyfunction]
pub fn get_a_state(a: u64, b: u64) -> PyResult<ObservableGameStatePy> {
    // make rng from a seed
    let game = Game::new();
    Ok(ObservableGameStatePy::from(
        game.game_state.observe(game::GamePlayer::Player1),
    ))
}

#[pymodule]
#[pyo3(name = "rust")]
pub fn rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_a_state, m)?)?;
    m.add_class::<CardPy>()?;
    m.add_class::<GameEnvPy>()?;
    Ok(())
}
