use core::fmt;

use super::cards::{Card, Deck, Hand};

macro_rules! pub_struct {
  ($name:ident {$($field:ident: $t:ty,)*}) => {
      #[derive(Clone, PartialEq)] // ewww
      pub struct $name {
          $(pub $field: $t),*
      }
  }
}

#[derive(Clone, PartialEq, Copy, Debug)]
pub enum GamePlayer {
    Player1,
    Player2,
}

impl GamePlayer {
    pub fn other(&self) -> GamePlayer {
        match self {
            GamePlayer::Player1 => GamePlayer::Player2,
            GamePlayer::Player2 => GamePlayer::Player1,
        }
    }
}

// ignore unused variable for now
pub_struct!(ObservableGameState {
    player: GamePlayer,
    num_cards_in_deck: u8,
    attack_table: Vec<Card>,
    defense_table: Vec<Card>,
    hand: Hand,
    visible_card: Card,
    defender_has_taken: bool,
    acting_player: GamePlayer,
    defender: GamePlayer,
    cards_in_opponent: u8,
});

pub_struct!(GameState {
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
});

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

impl GameState {
    pub fn new(
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
    ) -> GameState {
        GameState {
            deck,
            attack_table,
            defense_table,
            hand1,
            hand2,
            acting_player,
            defending_player,
            visible_card,
            defender_has_taken,
            graveyard,
        }
    }

    pub fn observe(&self, player: GamePlayer) -> ObservableGameState {
        let hand = match player {
            GamePlayer::Player1 => self.hand1.clone(),
            GamePlayer::Player2 => self.hand2.clone(),
        };
        ObservableGameState {
            player,
            num_cards_in_deck: self.deck.len() as u8,
            attack_table: self.attack_table.clone(),
            defense_table: self.defense_table.clone(),
            hand,
            visible_card: self.visible_card.clone(),
            defender_has_taken: self.defender_has_taken,
            acting_player: self.acting_player.clone(),
            defender: self.defending_player.clone(),
            cards_in_opponent: match player {
                GamePlayer::Player1 => self.hand2.0.len() as u8,
                GamePlayer::Player2 => self.hand1.0.len() as u8,
            },
        }
    }

    pub fn num_undefended(&self) -> u8 {
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
