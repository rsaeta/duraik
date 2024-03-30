use super::cards::Card;

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Action {
    StopAttack,
    Take,
    Attack(Card),
    Defend(Card),
}

pub fn num_actions() -> u8 {
    // one for take, one for stop attack, 36 attack, 36 defend
    1 + 1 + 36 + 36
}

impl From<Action> for u8 {
    fn from(action: Action) -> u8 {
        match action {
            Action::StopAttack => 0,
            Action::Take => 1,
            Action::Attack(c) => 2 + (<Card as Into<u8>>::into(c)),
            Action::Defend(c) => 38 + <Card as Into<u8>>::into(c),
        }
    }
}

impl From<u8> for Action {
    fn from(num: u8) -> Action {
        match num {
            0 => Action::StopAttack,
            1 => Action::Take,
            2..=37 => Action::Attack(Card::from(num - 2)),
            38..=73 => Action::Defend(Card::from(num - 38)),
            _ => panic!("Invalid action number"),
        }
    }
}

pub struct ActionList(pub Vec<Action>);

impl ActionList {
    pub fn to_strings(&self) -> Vec<String> {
        self.0.iter().map(|a| format!("{:?}", a)).collect()
    }

    pub fn to_u8s(&self) -> Vec<u8> {
        self.0.iter().map(|&a| u8::from(a)).collect()
    }

    pub fn to_bitmap(&self) -> Vec<u8> {
        let mut bitmap = vec![0; num_actions() as usize];
        for action in &self.0 {
            bitmap[<Action as Into<u8>>::into(*action) as usize] = 1;
        }
        bitmap
    }

    pub fn from_bitmap(bitmap: Vec<u8>) -> Self {
        let actions = bitmap
            .iter()
            .enumerate()
            .filter_map(|(i, &b)| {
                if b == 1 {
                    Some(Action::from(i as u8))
                } else {
                    None
                }
            })
            .collect();
        ActionList(actions)
    }
}
