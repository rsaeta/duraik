class DurakAction:
    """
    n <- 15-lowest_card
    0 -> n*4: attack actions
    n*4 -> n*8: defend actions
    n*8 -> n*12: pass_with_card actions
    n*12: take action
    n*12+1: stop_attacking action
    Durak Actions are going to be 0-X for attacking, X-2X for defending
    where each action is basically (15-lowest_card)*['S', 'H', 'D', 'C'].index(suit) + (rank-lowest_card).
    """
    lowest_card = 6

    @staticmethod
    def n(m=1):
        return (15 - DurakAction.lowest_card)*m

    @staticmethod
    def is_attack(action_id: int) -> bool:
        return action_id < DurakAction.n(4)

    @staticmethod
    def is_defend(action_id: int) -> bool:
        return DurakAction.n(4) <= action_id < 2*DurakAction.n(4)

    @staticmethod
    def is_pass_with_card(action_id: int) -> bool:
        return DurakAction.n(4)*2 <= action_id < 3*DurakAction.n(4)

    @staticmethod
    def is_take(action_id: int) -> bool:
        return action_id == DurakAction.take_action()

    @staticmethod
    def is_stop_attacking(action_id: int) -> bool:
        return action_id == DurakAction.stop_attacking_action()

    @staticmethod
    def is_noop(action_id: int) -> bool:
        return action_id == DurakAction.noop_action()

    @staticmethod
    def ext_from_card(card):
        suit, rank = card
        return (15 - DurakAction.lowest_card) * ['S', 'H', 'D', 'C'].index(suit) + (rank - DurakAction.lowest_card)

    @staticmethod
    def card_from_ext(ext):
        while ext >= DurakAction.n(4):
            ext -= DurakAction.n(4)
        suit = ['S', 'H', 'D', 'C'][ext // (15 - DurakAction.lowest_card)]
        rank = ext % (15 - DurakAction.lowest_card) + DurakAction.lowest_card
        return suit, rank

    @staticmethod
    def attack_id_from_card(card) -> int:
        return DurakAction.ext_from_card(card)

    @staticmethod
    def defend_id_from_card(card) -> int:
        ext = DurakAction.ext_from_card(card)
        return ext + DurakAction.n(4)

    @staticmethod
    def pass_with_card_id_from_card(card) -> int:
        ext = DurakAction.ext_from_card(card)
        return ext + DurakAction.n(4)*2

    @staticmethod
    def card_from_attack_id(action_id: int) -> tuple:
        return DurakAction.card_from_ext(action_id)

    @staticmethod
    def card_from_defend_id(action_id: int) -> tuple:
        return DurakAction.card_from_ext(action_id)

    @staticmethod
    def card_from_pass_with_card_id(action_id: int) -> tuple:
        return DurakAction.card_from_ext(action_id)

    @staticmethod
    def num_actions() -> int:
        # 8 actions per rank, 4 suits attack/defend, take, stop_attacking, pass_with_card
        return DurakAction.n(4)*3+3

    @staticmethod
    def take_action() -> int:
        return DurakAction.num_actions() - 3

    @staticmethod
    def stop_attacking_action() -> int:
        return DurakAction.num_actions() - 2

    @staticmethod
    def noop_action() -> int:
        return DurakAction.num_actions() - 1

    @staticmethod
    def action_to_string(action_id: int) -> str:
        if DurakAction.is_attack(action_id):
            return 'attack {}'.format(DurakAction.card_from_attack_id(action_id))
        elif DurakAction.is_defend(action_id):
            return 'defend {}'.format(DurakAction.card_from_defend_id(action_id))
        elif DurakAction.is_pass_with_card(action_id):
            return 'pass {}'.format(DurakAction.card_from_pass_with_card_id(action_id))
        elif DurakAction.is_take(action_id):
            return 'take'
        elif DurakAction.is_stop_attacking(action_id):
            return 'stop_attacking'
        elif DurakAction.is_noop(action_id):
            return 'noop'
        else:
            raise ValueError('Invalid action_id {}'.format(action_id))
