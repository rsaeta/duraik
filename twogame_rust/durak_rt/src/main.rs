use core::fmt;
use rand::{seq::SliceRandom, Rng};
use std::{collections::HashSet, vec};

#[derive(Clone, Copy, PartialEq, Debug, Eq, Ord, PartialOrd)]
enum Suit {
    Spades,
    Hearts,
    Diamonds,
    Clubs,
}

#[derive(Clone, Copy, PartialEq, Eq, Ord, PartialOrd)]
struct Card {
    suit: Suit,
    rank: u8,
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
struct Deck {
    cards: Vec<Card>,
}

impl fmt::Debug for Deck {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:?}", self.cards)
    }
}

impl Deck {
    fn new(lowest_rank: u8) -> Deck {
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

    fn shuffle(&mut self) {
        let mut rng = rand::thread_rng();
        self.cards.shuffle(&mut rng);
    }

    fn draw(&mut self) -> Option<Card> {
        self.cards.pop()
    }

    fn draw_n(&mut self, n: u8) -> Vec<Card> {
        let mut drawn = Vec::new();
        for _ in 0..n {
            match self.draw() {
                Some(card) => drawn.push(card),
                None => break,
            }
        }
        drawn
    }

    fn get_first(&self) -> Option<Card> {
        self.cards.first().cloned()
    }
}

trait Player {
    fn choose_action(
        &mut self,
        game_state: ObservableGameState,
        actions: Vec<Action>,
        history: Vec<ObservableGameState>,
    ) -> Action;
}

struct RandomPlayer {
    rng: rand::rngs::ThreadRng,
}

impl RandomPlayer {
    fn new(_rng: Option<rand::rngs::ThreadRng>) -> RandomPlayer {
        match _rng {
            Some(rng) => RandomPlayer { rng },
            None => RandomPlayer {
                rng: rand::thread_rng(),
            },
        }
    }
}

impl Player for RandomPlayer {
    fn choose_action(
        &mut self,
        _state: ObservableGameState,
        actions: Vec<Action>,
        _history: Vec<ObservableGameState>,
    ) -> Action {
        let choice = match actions.len() {
            0 => panic!("No actions available"),
            1 => 0,
            _ => self.rng.gen_range(0..actions.len()),
        };
        actions[choice]
    }
}

#[derive(Clone)]
struct Hand(Vec<Card>);

impl fmt::Debug for Hand {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // sort based on suit then rank
        let mut sorted_hand = self.0.clone();
        sorted_hand.sort();
        write!(f, "{:?}", sorted_hand)
    }
}

#[derive(Clone)]
struct GameState {
    deck: Deck,
    attack_table: Vec<Card>,
    defense_table: Vec<Card>,
    hand1: Hand,
    hand2: Hand,
    acting_player: GamePlayer,
    defending_player: GamePlayer,
    visible_card: Card,
    defender_has_taken: bool,
    graveyard: Vec<Card>,
}

impl fmt::Debug for GameState {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "{{\n\tDeck: {:?}\n\tAttack: {:?}\n\tDefense: {:?}\n\tHand1: {:?}\n\tHand2: {:?}\n\tActing: {:?}\n\tDefending: {:?}\n\tVisible: {:?}\n\tDefender has taken: {}\n\tGraveyard: {:?}\n}}",
            self.deck,
            self.attack_table,
            self.defense_table,
            self.hand1,
            self.hand2,
            self.acting_player,
            self.defending_player,
            self.visible_card,
            self.defender_has_taken,
            self.graveyard,
        )
    }
}

#[derive(Clone, PartialEq, Copy, Debug)]
enum GamePlayer {
    Player1,
    Player2,
}

impl GamePlayer {
    fn other(&self) -> GamePlayer {
        match self {
            GamePlayer::Player1 => GamePlayer::Player2,
            GamePlayer::Player2 => GamePlayer::Player1,
        }
    }
}

// ignore unused variable for now
#[allow(dead_code)]
struct ObservableGameState {
    player: GamePlayer,
    num_cards_in_deck: u8,
    attack_table: Vec<Card>,
    defense_table: Vec<Card>,
    hand: Hand,
    visible_card: Card,
    defender_has_taken: bool,
    acting_player: GamePlayer,
    defender: GamePlayer,
}

impl GameState {
    fn observe(&self, player: GamePlayer) -> ObservableGameState {
        let hand = match player {
            GamePlayer::Player1 => self.hand1.clone(),
            GamePlayer::Player2 => self.hand2.clone(),
        };
        ObservableGameState {
            player,
            num_cards_in_deck: self.deck.cards.len() as u8,
            attack_table: self.attack_table.clone(),
            defense_table: self.defense_table.clone(),
            hand,
            visible_card: self.visible_card.clone(),
            defender_has_taken: self.defender_has_taken,
            acting_player: self.acting_player.clone(),
            defender: self.defending_player.clone(),
        }
    }

    fn num_undefended(&self) -> u8 {
        let num_attack = self.attack_table.len() as u8;
        let num_defend = self.defense_table.len() as u8;
        num_attack - num_defend
    }

    fn _defender_hand(&self) -> &Hand {
        match self.defending_player {
            GamePlayer::Player1 => &self.hand1,
            GamePlayer::Player2 => &self.hand2,
        }
    }

    fn _attacker_hand(&self) -> &Hand {
        match self.defending_player.other() {
            GamePlayer::Player1 => &self.hand1,
            GamePlayer::Player2 => &self.hand2,
        }
    }
}

struct Game {
    history: Vec<GameState>,
    game_state: GameState,
    player1: Box<dyn Player>,
    player2: Box<dyn Player>,
}

fn det_first_attacker(hand1: &Hand, hand2: &Hand, suit: Suit) -> GamePlayer {
    let mut min1 = 15;
    let mut min2 = 15;
    for card in hand1.0.iter() {
        if card.suit == suit && card.rank < min1 {
            min1 = card.rank;
        }
    }
    for card in hand2.0.iter() {
        if card.suit == suit && card.rank < min2 {
            min2 = card.rank;
        }
    }
    if min1 < min2 {
        GamePlayer::Player1
    } else {
        GamePlayer::Player2
    }
}

impl Game {
    fn new(player1: Box<dyn Player>, player2: Box<dyn Player>) -> Game {
        let mut deck = Deck::new(6);
        deck.shuffle();
        let hand1 = Hand(deck.draw_n(6));
        let hand2 = Hand(deck.draw_n(6));
        let visible_card = deck.get_first().unwrap();
        let first_attacker = det_first_attacker(&hand1, &hand2, visible_card.suit);
        let game_state = GameState {
            deck,
            hand1,
            hand2,
            attack_table: Vec::new(),
            defense_table: Vec::new(),
            acting_player: first_attacker,
            defending_player: first_attacker.other(),
            visible_card,
            defender_has_taken: false,
            graveyard: Vec::new(),
        };

        Game {
            game_state,
            player1,
            player2,
            history: Vec::new(),
        }
    }

    fn defender_hand(&self) -> &Hand {
        match self.game_state.defending_player {
            GamePlayer::Player1 => &self.game_state.hand1,
            GamePlayer::Player2 => &self.game_state.hand2,
        }
    }

    fn _attacker_hand(&mut self) -> &mut Hand {
        match self.game_state.defending_player.other() {
            GamePlayer::Player1 => &mut self.game_state.hand1,
            GamePlayer::Player2 => &mut self.game_state.hand2,
        }
    }

    fn attacker_hand(&self) -> &Hand {
        match self.game_state.defending_player.other() {
            GamePlayer::Player1 => &self.game_state.hand1,
            GamePlayer::Player2 => &self.game_state.hand2,
        }
    }

    fn num_undefended(&self) -> u8 {
        let num_attack = self.game_state.attack_table.len() as u8;
        let num_defend = self.game_state.defense_table.len() as u8;
        num_attack - num_defend
    }

    fn refill_hands(&mut self) {
        let refill_order = match self.game_state.defending_player {
            GamePlayer::Player2 => vec![GamePlayer::Player1, GamePlayer::Player2],
            GamePlayer::Player1 => vec![GamePlayer::Player2, GamePlayer::Player1],
        };
        for player in refill_order.iter() {
            let hand = match player {
                GamePlayer::Player1 => &mut self.game_state.hand1,
                GamePlayer::Player2 => &mut self.game_state.hand2,
            };
            let num_cards = 6 - hand.0.len() as i8;
            if num_cards > 0 {
                let mut new_cards = self.game_state.deck.draw_n(num_cards as u8);
                hand.0.append(&mut new_cards);
            }
        }
    }

    fn add_table_to_defender(&mut self) {
        // Temporarily take mutable references to the tables you want to modify.
        let defense_table = &mut self.game_state.defense_table;
        let attack_table = &mut self.game_state.attack_table;

        // Borrow `self` mutably once to get a mutable reference to the defender's hand.
        let hand = match self.game_state.defending_player {
            GamePlayer::Player1 => &mut self.game_state.hand1.0,
            GamePlayer::Player2 => &mut self.game_state.hand2.0,
        };

        // Now, you can append the tables to the hand without violating Rust's borrowing rules,
        // because `hand`, `defense_table`, and `attack_table` are clearly separate mutable references.
        hand.append(defense_table);
        hand.append(attack_table);
    }

    fn clear_table(&mut self) {
        self.game_state
            .graveyard
            .extend(self.game_state.attack_table.iter());
        self.game_state
            .graveyard
            .extend(self.game_state.defense_table.iter());
        self.game_state.attack_table.clear();
        self.game_state.defense_table.clear();
    }

    fn handle_take(&mut self) {
        // check whether attacker can add more cards
        let num_attack = self.game_state.attack_table.len() as u8;
        let num_defend = self.game_state.defense_table.len() as u8;
        if num_attack == 6 || (num_attack - num_defend) >= self.defender_hand().0.len() as u8 {
            // here we need to give defender all cards, round is over
            self.add_table_to_defender();
            self.refill_hands();
            self.game_state.acting_player = self.game_state.acting_player.other();
        } else {
            // just need to give controller back to attacker after setting flag
            self.game_state.defender_has_taken = true;
            self.game_state.acting_player = self.game_state.acting_player.other();
        }
    }

    fn handle_stop_attack(&mut self) {
        if self.game_state.defender_has_taken {
            self.add_table_to_defender();
            self.refill_hands();
        } else {
            if self.game_state.num_undefended() == 0 {
                self.clear_table();
                self.game_state.defending_player = self.game_state.defending_player.other();
                self.refill_hands();
            }
            self.game_state.acting_player = self.game_state.acting_player.other();
        }
        self.game_state.defender_has_taken = false;
    }

    fn handle_attack(&mut self, card: Card) {
        self.game_state.attack_table.push(card);
        // remove card from player hand
        let hand = self._attacker_hand();
        let index = hand.0.iter().position(|x| *x == card).unwrap();
        hand.0.remove(index);
    }

    fn handle_defense(&mut self, card: Card) {
        self.game_state.defense_table.push(card);
        {
            let hand = match self.game_state.defending_player {
                GamePlayer::Player1 => &mut self.game_state.hand1,
                GamePlayer::Player2 => &mut self.game_state.hand2,
            };
            let index = hand.0.iter().position(|x| *x == card).unwrap();
            hand.0.remove(index);
        }
        if self.game_state.defense_table.len() == 6 || self.defender_hand().0.len() == 0 {
            self.clear_table();
            self.refill_hands();
            self.game_state.defender_has_taken = false;
            self.game_state.defending_player = self.game_state.defending_player.other();
        } else if self.game_state.num_undefended() == 0 {
            self.game_state.acting_player = self.game_state.acting_player.other();
        }
    }

    fn ranks(&self, game_state: &GameState) -> HashSet<u8> {
        let mut ranks = HashSet::new();
        for card in game_state.attack_table.iter() {
            ranks.insert(card.rank);
        }
        for card in game_state.defense_table.iter() {
            ranks.insert(card.rank);
        }
        ranks
    }

    fn legal_attacks(&self) -> Vec<Action> {
        let mut actions = Vec::new();
        if self.game_state.attack_table.len() == 0 {
            for card in self.attacker_hand().0.iter() {
                actions.push(Action::Attack(card.clone()));
            }
        } else {
            let ranks = self.ranks(&self.game_state);
            for card in self.attacker_hand().0.iter() {
                if ranks.contains(&card.rank) {
                    actions.push(Action::Attack(card.clone()));
                }
            }
            actions.push(Action::StopAttack);
        }

        actions
    }

    fn legal_defenses(&self) -> Vec<Action> {
        let mut actions = Vec::new();
        actions.push(Action::Take);
        let last_attack = self.game_state.attack_table[(self.num_undefended() as usize) - 1];
        let tsuit = self.game_state.visible_card.suit;
        for card in self.defender_hand().0.iter() {
            if last_attack.suit == tsuit {
                if card.suit == tsuit && card.rank > last_attack.rank {
                    actions.push(Action::Defend(card.clone()));
                }
            } else {
                if card.suit == tsuit
                    || (card.suit == last_attack.suit && card.rank > last_attack.rank)
                {
                    actions.push(Action::Defend(card.clone()));
                }
            }
        }

        actions
    }

    fn legal_actions(&self) -> Vec<Action> {
        match (
            self.game_state.acting_player,
            self.game_state.defending_player,
        ) {
            (a, b) if a == b => self.legal_defenses(),
            _ => self.legal_attacks(),
        }
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
enum Action {
    StopAttack,
    Take,
    Attack(Card),
    Defend(Card),
}

trait GameLogic {
    fn step(&mut self, action: Action) -> &GameState;
    fn get_actions(&self) -> Vec<Action>;
    fn get_winner(&self) -> Option<GamePlayer>;
    fn get_rewards(&self) -> (f32, f32);
    fn is_over(&self) -> bool;
}

impl GameLogic for Game {
    fn step(&mut self, action: Action) -> &GameState {
        let current_state = self.game_state.clone();
        self.history.push(current_state);
        match action {
            Action::StopAttack => self.handle_stop_attack(),
            Action::Take => self.handle_take(),
            Action::Attack(card) => self.handle_attack(card),
            Action::Defend(card) => self.handle_defense(card),
        }

        &self.game_state
    }

    fn get_actions(&self) -> Vec<Action> {
        self.legal_actions()
    }

    fn get_winner(&self) -> Option<GamePlayer> {
        let sizes = vec![
            &self.game_state.hand1.0,
            &self.game_state.hand2.0,
            &self.game_state.deck.cards,
        ]
        .iter()
        .map(|x| x.len())
        .collect::<Vec<usize>>();
        match sizes.as_slice() {
            [_, _, 1..=52] => None,
            [0, 0, 0] => None,
            [0, _, _] => Some(GamePlayer::Player1),
            [_, 0, _] => Some(GamePlayer::Player2),
            _ => None,
        }
    }

    fn get_rewards(&self) -> (f32, f32) {
        let winner = self.get_winner();
        match winner {
            Some(GamePlayer::Player1) => (1.0, -1.0),
            Some(GamePlayer::Player2) => (-1.0, 1.0),
            None => (0.0, 0.0),
        }
    }

    fn is_over(&self) -> bool {
        let sizes = vec![
            &self.game_state.hand1.0,
            &self.game_state.hand2.0,
            &self.game_state.deck.cards,
        ]
        .iter()
        .map(|x| x.len())
        .collect::<Vec<usize>>();
        match sizes.as_slice() {
            [_, _, 1..=52] => false,
            [0, 0, 0] => true,
            [0, _, _] => true,
            [_, 0, _] => true,
            _ => false,
        }
    }
}

fn run_game() -> (f32, f32) {
    let p1 = Box::new(RandomPlayer::new(None));
    let p2 = Box::new(RandomPlayer::new(None));
    let mut game = Game::new(p1, p2);
    let mut game_over = false;
    'game_loop: loop {
        // print i
        // println!("i: {}", i);
        if game_over {
            break 'game_loop;
        }
        let pta = game.game_state.acting_player;
        let actions = game.get_actions();
        let player = match pta {
            GamePlayer::Player1 => game.player1.as_mut(),
            GamePlayer::Player2 => game.player2.as_mut(),
        };
        let history = game.history.iter().map(|x| x.observe(pta)).collect();
        //println!("Player: {:?}", pta);
        //println!("Actions: {:?}", actions);
        let action = player.choose_action(game.game_state.observe(pta), actions, history);
        //println!("Action: {:?}", action);
        game.step(action);
        //println!("Gamestate: {:?}", *game_state);
        game_over = game.is_over();
    }
    let rewards = game.get_rewards();
    // println!("Rewards: {:?}", rewards);
    rewards
}

fn main() {
    use rayon::prelude::*;
    let num_games = 100000;
    let range = 0..num_games;
    let results = range
        .into_par_iter()
        .map(|_| run_game())
        .reduce(|| (0., 0.), |(p1, p2), (_p1, _p2)| (p1 + _p1, p2 + _p2));
    println!("Results: {:?}", results);
}