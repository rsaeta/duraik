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

#[derive(Clone, Debug)]
struct Deck {
    cards: Vec<Card>,
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

    fn get_last(&self) -> Option<Card> {
        self.cards.last().cloned()
    }
}

trait Player {
    fn choose_action(&mut self, game_state: ObservableGameState, actions: Vec<Action>) -> Action;
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
    fn choose_action(&mut self, _state: ObservableGameState, actions: Vec<Action>) -> Action {
        let choice = self.rng.gen_range(0..actions.len());
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
}

impl fmt::Debug for GameState {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "{{\n\tDeck: {:?}\n\tAttack: {:?}\n\tDefense: {:?}\n\tHand1: {:?}\n\tHand2: {:?}\n\tActing: {:?}\n\tDefending: {:?}\n\tVisible: {:?}\n\tDefender has taken: {}\n}}",
            self.deck.cards.len(),
            self.attack_table,
            self.defense_table,
            self.hand1,
            self.hand2,
            self.acting_player,
            self.defending_player,
            self.visible_card,
            self.defender_has_taken
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
        let visible_card = deck.get_last().unwrap();
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
        };

        Game {
            game_state,
            player1: player1,
            player2: player2,
        }
    }

    fn _defender_hand(&mut self) -> &mut Hand {
        match self.game_state.defending_player {
            GamePlayer::Player1 => &mut self.game_state.hand1,
            GamePlayer::Player2 => &mut self.game_state.hand2,
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

    fn num_undefended(&self, game_state: &GameState) -> u8 {
        let num_attack = game_state.attack_table.len() as u8;
        let num_defend = game_state.defense_table.len() as u8;
        num_attack - num_defend
    }

    fn refill_hands(&self, game_state: &mut GameState) {
        let refill_order = match game_state.defending_player {
            GamePlayer::Player2 => vec![GamePlayer::Player1, GamePlayer::Player2],
            GamePlayer::Player1 => vec![GamePlayer::Player2, GamePlayer::Player1],
        };
        for player in refill_order.iter() {
            let hand = match player {
                GamePlayer::Player1 => &mut game_state.hand1,
                GamePlayer::Player2 => &mut game_state.hand2,
            };
            let num_cards = 6 - hand.0.len() as u8;
            let mut new_cards = game_state.deck.draw_n(num_cards);
            hand.0.append(&mut new_cards);
        }
    }

    fn add_table_to_defender(&mut self) {
        let mut dt = self.game_state.defense_table.clone();
        let mut at = self.game_state.attack_table.clone();
        let hand = self._defender_hand();
        hand.0.append(&mut dt);
        hand.0.append(&mut at);
        self.game_state.attack_table.clear();
        self.game_state.defense_table.clear();
    }

    fn handle_take(&mut self) -> GameState {
        let mut new_state = self.game_state.clone();
        // check whether attacker can add more cards
        let num_attack = new_state.attack_table.len() as u8;
        let num_defend = new_state.defense_table.len() as u8;
        if num_attack == 6 || (num_attack - num_defend) >= self.defender_hand().0.len() as u8 {
            // here we need to give defender all cards, round is over
            self.add_table_to_defender();
            self.refill_hands(&mut new_state);
        } else {
            // just need to give controller back to attacker after setting flag
            new_state.defender_has_taken = true;
            new_state.acting_player = new_state.acting_player.other();
        }
        new_state
    }

    fn handle_stop_attack(&mut self) -> GameState {
        let mut new_state: GameState = self.game_state.clone();
        if self.game_state.defender_has_taken {
            self.add_table_to_defender();
            self.refill_hands(&mut new_state);
        } else {
            new_state.acting_player = new_state.acting_player.other();
        }

        new_state
    }

    fn handle_attack(&mut self, card: Card) -> GameState {
        let mut new_state = self.game_state.clone();
        new_state.attack_table.push(card);
        // remove card from player hand
        let hand = match new_state.acting_player {
            GamePlayer::Player1 => &mut new_state.hand1,
            GamePlayer::Player2 => &mut new_state.hand2,
        };
        let index = hand.0.iter().position(|x| *x == card).unwrap();
        hand.0.remove(index);
        new_state
    }

    fn handle_defense(&self, card: Card) -> GameState {
        let mut new_state = self.game_state.clone();
        new_state.defense_table.push(card);
        if new_state.num_undefended() == 0 {}
        new_state
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
        let last_attack =
            self.game_state.attack_table[self.num_undefended(&self.game_state) as usize];
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
            (A, B) if A == B => self.legal_defenses(),
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
    fn step(&mut self, game_state: &GameState, action: Action) -> GameState;
    fn get_actions(&self, game_state: &GameState) -> Vec<Action>;
    fn get_winner(&self, game_state: GameState) -> Option<GamePlayer>;
    fn get_rewards(&self, game_state: GameState) -> (f32, f32);
    fn is_over(&self, game_state: &GameState) -> bool;
}

impl GameLogic for Game {
    fn step(&mut self, game_state: &GameState, action: Action) -> GameState {
        match action {
            Action::StopAttack => self.handle_stop_attack(),
            Action::Take => self.handle_take(),
            Action::Attack(card) => self.handle_attack(card),
            Action::Defend(card) => self.handle_defense(card),
        }
    }

    fn get_actions(&self, game_state: &GameState) -> Vec<Action> {
        self.legal_actions()
    }

    fn get_winner(&self, game_state: GameState) -> Option<GamePlayer> {
        let sizes = vec![
            game_state.hand1.0,
            game_state.hand2.0,
            game_state.deck.cards,
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

    fn get_rewards(&self, game_state: GameState) -> (f32, f32) {
        let winner = self.get_winner(game_state);
        match winner {
            Some(GamePlayer::Player1) => (1.0, -1.0),
            Some(GamePlayer::Player2) => (-1.0, 1.0),
            None => (0.0, 0.0),
        }
    }

    fn is_over(&self, game_state: &GameState) -> bool {
        let sizes = vec![
            &game_state.hand1.0,
            &game_state.hand2.0,
            &game_state.deck.cards,
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

fn run_game() {
    let p1 = Box::new(RandomPlayer::new(None));
    let p2 = Box::new(RandomPlayer::new(None));
    let mut game = Game::new(p1, p2);
    let mut game_over = false;
    let mut game_state = game.game_state.clone();
    let mut i = 0;
    'game_loop: loop {
        i += 1;
        // print i
        println!("i: {}", i);
        if game_over {
            break 'game_loop;
        }
        game.game_state = game_state;
        let pta = game.game_state.acting_player;
        let actions = game.get_actions(&game.game_state);
        let player = match pta {
            GamePlayer::Player1 => game.player1.as_mut(),
            GamePlayer::Player2 => game.player2.as_mut(),
        };
        println!("Player: {:?}", pta);
        println!("Actions: {:?}", actions);
        let action = player.choose_action(game.game_state.observe(pta), actions);
        println!("Action: {:?}", action);
        game_state = game.step(&game.game_state, action);
        println!("Gamestate: {:?}", game_state);
        game_over = game.is_over(&game_state);
    }
}

fn main() {
    run_game();
}
