"""
A functional implementation of Durak game that uses immutable data structure and returns new
game states when actions are taken. Should be easier to reason about eventually.
"""
from typing import List, Tuple
import numpy as np

from .game_state import DurakGameState, ObservableDurakGameState
from .actions import DurakAction
from .entities import Card


def _new_deck(lowest_card: int = 6) -> List[Card]:
    return [(suit, rank) for suit in ['S', 'H', 'D', 'C'] for rank in range(lowest_card, 15)]


def _deal_hands(deck: List[Card]):
    return tuple(tuple(deck.pop() for _ in range(6)) for _ in range(3))


def _initial_attacker(hands: Tuple[Tuple[Card, ...]], visible_card: Card, np_rand: np.random.RandomState):
    init_attacker = -1
    lowest_rank = 15
    ts = visible_card[0]
    for i, hand in enumerate(hands):
        for suit, rank in hand:
            if suit == ts and rank < lowest_rank:
                lowest_rank = rank
                init_attacker = i
    return np_rand.randint(3) if init_attacker < 0 else init_attacker


def new_game_state(seed: int = 0) -> DurakGameState:
    """
    Returns a new game state with the deck shuffled and the first player determined.
    """
    np_rand = np.random.RandomState(seed=seed)
    deck = _new_deck()
    np_rand.shuffle(deck)
    player_hands = _deal_hands(deck)
    visible_card = deck[0]
    attacker = _initial_attacker(player_hands, visible_card, np_rand)
    return DurakGameState(
        np_rand=np_rand,
        defender_has_taken=False,
        deck=tuple(deck),
        visible_card=visible_card,
        attackers=tuple([attacker]),
        defender=(attacker + 1) % 3,
        player_hands=player_hands,
        attack_table=tuple(),
        defend_table=tuple(),
        stopped_attacking=tuple(),
        player_taking_action=attacker,
        graveyard=tuple(),
        is_done=False,
        round_over=False,
    )


def step_attack_action(state: DurakGameState, action_id: DurakAction) -> DurakGameState:
    """
    Handles the state update when a player attacks. This adds a card to the attack table.
    If the attacker does not have any more cards, then the player taking action is updated
    to the defender.
    """
    player_id = state.player_taking_action
    state_updates = dict()
    if not state.defender_has_taken:
        state_updates.update(stopped_attacking=tuple())
    if player_id not in state.attackers:
        state_updates.update(attackers=state.attackers + (player_id,))
    card = DurakAction.card_from_attack_id(action_id)
    hand = state.player_hands[player_id]
    hand = tuple(c for c in hand if c != card)
    attack_table = state.attack_table + (card,)
    new_hands = tuple(
        hand if i == player_id else h for i, h in enumerate(state.player_hands)
    )
    state_updates.update(player_hands=new_hands, attack_table=attack_table)
    if (len(new_hands[state.defender]) == state.num_undefended() + 1) or len(hand) == 0 and not state.defender_has_taken:
        state_updates.update(player_taking_action=state.defender)

    return state._replace(**state_updates)


def step_defend_action(state: DurakGameState, action_id: DurakAction) -> DurakGameState:
    """
    Handles the state update when a player defends against an attack. This adds a card
    to the defend table and removes it from the player's hand. If the defend table is
    as long as the attack table, the player taking action is updated to the attacker,
    otherwise it stays as the defender.
    """
    player_id = state.player_taking_action
    state_updates = dict()
    card = DurakAction.card_from_defend_id(action_id)
    hand = state.player_hands[player_id]
    hand = tuple(c for c in hand if c != card)
    defend_table = state.defend_table + (card,)
    new_hands = tuple(
        hand if i == player_id else h for i, h in enumerate(state.player_hands)
    )
    state_updates.update(player_hands=new_hands, defend_table=defend_table, stopped_attacking=tuple())
    state = state._replace(**state_updates)
    if len(state.attack_table) == 6 or len(hand) == 0:  # Max attacks have happened or defender is out of cards
        state = _clear_table(state)
        state = _refill_cards(state)
        state = _iterate_players(state)
    elif len(state.attack_table) == len(defend_table):
        state = state._replace(player_taking_action=state.attackers[-1])

    return state


def step_pass_with_card_action(state: DurakGameState, action_id: DurakAction) -> DurakGameState:
    """
    Handles the state update when a player passes the attack on to the next player. This
    keeps the person taking action as the passer who can elect to add more cards. Needs
    to handle when the player being passed to initiate the attack and needs to be removed
    from the attack queue.
    """
    player_id = state.player_taking_action
    state_updates = dict()
    card = DurakAction.card_from_pass_with_card_id(action_id)
    hand = state.player_hands[player_id]
    hand = tuple(c for c in hand if c != card)
    new_hands = tuple(
        hand if i == player_id else h for i, h in enumerate(state.player_hands)
    )
    state_updates.update(player_hands=new_hands, stopped_attacking=tuple())
    attack_table = state.attack_table + (card,)
    if player_id not in state.attackers:
        state_updates.update(attackers=state.attackers + (player_id,))
    new_defender = (player_id + 1) % len(state.player_hands)
    state_updates.update(
        attackers=tuple(a for a in state.attackers if a not in [new_defender, player_id]) + (player_id, )
    )
    state_updates.update(attack_table=attack_table, defender=new_defender)
    if len(new_hands[player_id]) == 0:
        state_updates.update(player_taking_action=new_defender)

    return state._replace(**state_updates)


def step_take_action(state: DurakGameState) -> DurakGameState:
    """
    Handles the state update when defender chooses to take. This initiates a portion of the
    game where the attackers may choose to add more cards to the attack table before the
    defender takes all cards. Both attackers must choose the stop_attacking action before
    the round is over.
    """
    state = state._replace(defender_has_taken=True, stopped_attacking=tuple())
    if state.num_undefended() == len(state.player_hands[state.defender]):
        state = _give_defender_cards(state)
        state = _refill_cards(state)
        state = _iterate_players(state)
        return state
    if state.num_undefended() < len(state.player_hands[state.defender]):
        return state._replace(player_taking_action=state.attackers[-1])
    return state


def _give_defender_cards(state: DurakGameState) -> DurakGameState:
    """
    Clear the table after an unsuccessful defense. The attack and defend tables are reset to empty,
    the cards are given to the defender's hand, and the attacker/defender are updated to iterate
    one to the left, skipping defender's turn.
    """
    defender = state.defender
    state_updates = dict()
    #state_updates.update(defender_has_taken=False)
    hand = state.player_hands[defender]
    hand = hand + tuple(c for c in state.attack_table)
    hand = hand + tuple(c for c in state.defend_table)
    new_hands = tuple(
        hand if i == defender else h for i, h in enumerate(state.player_hands)
    )
    state_updates.update(
        player_hands=new_hands, attack_table=tuple(), defend_table=tuple(),
        stopped_attacking=tuple(),
    )

    return state._replace(**state_updates)


def _clear_table(state: DurakGameState) -> DurakGameState:
    """
    Clear the table after a successful defense. The attack and defend tables are reset to empty,
    the graveyard is updated with those cards, and the attacker/defender are updated to iterate
    one to the left.
    """
    print('clearing table')
    state_updates = dict()
    graveyard = list(state.graveyard)
    graveyard.extend(state.attack_table)
    graveyard.extend(state.defend_table)
    state_updates.update(
        attack_table=tuple(),
        defend_table=tuple(),
        graveyard=tuple(graveyard),
        stopped_attacking=tuple(),
    )
    return state._replace(**state_updates)


def _is_attack_done(state: DurakGameState) -> bool:
    """
    Checks if the attack is done. This is the case when the defender has defended all cards or
    the defender has taken.
    """
    if len(state.stopped_attacking) == len(state.in_players()) - 1 or len(state.in_players()) < 2:
        return True
    return state.num_undefended() == len(state.player_hands[state.defender])


def step_stop_attack_action(state: DurakGameState) -> DurakGameState:
    """
    Handles the state update when a player stops attacking. This adds the player to the stopped
    attacking list and updates the player taking action to the next player. If both neighbors of
    the defender have stopped attacking and the defender has taken, then the defender takes all
    cards on the table.
    """
    player_id = state.player_taking_action
    if player_id not in state.stopped_attacking:
        state = state._replace(stopped_attacking=state.stopped_attacking + (player_id,))
    if _is_attack_done(state):  # All players have stopped attacking
        if state.defender_has_taken:
            state = _give_defender_cards(state)
        else:
            state = _clear_table(state)
        state = _refill_cards(state)
        state = _iterate_players(state)
        state = state._replace(stopped_attacking=tuple(),
                               defender_has_taken=False)
        return state
    if state.num_undefended() and not state.defender_has_taken:
        state = state._replace(player_taking_action=state.defender)
    else:
        potential_attackers = state.potential_attackers()
        potential_attackers.remove(player_id)
        if not len(potential_attackers):
            print('Da fuq happened')
        state = state._replace(player_taking_action=potential_attackers[0])
    return state


def _iterate_players(state: DurakGameState) -> DurakGameState:
    """
    Moves the attacker/defender counters forward.
    """
    attacker = state.defender if not state.defender_has_taken else (state.defender + 1) % len(state.player_hands)
    if len(state.player_hands[attacker]) == 0:
        attacker = (attacker + 1) % len(state.player_hands)
    defender = (attacker + 1) % len(state.player_hands)
    if len(state.player_hands[defender]) == 0:
        defender = (defender + 1) % len(state.player_hands)
    print('iterating player: {} -> {}'.format(state.player_taking_action, attacker))



    return state._replace(attackers=(attacker, ), defender=defender, player_taking_action=attacker)


def _refill_cards(state: DurakGameState) -> DurakGameState:
    """
    Refills cards of the players from the deck in the order of attacking given in state#attackers
    """
    if len(state.deck) == 0:
        return state
    deck = list(state.deck)
    attack_order = state.attackers
    hands = {i: list(h) for i, h in enumerate(state.player_hands)}
    for attacker in attack_order:
        while len(hands[attacker]) < 6 and len(deck):
            hands[attacker].append(deck.pop())
    while len(hands[state.defender]) < 6 and len(deck):
        hands[state.defender].append(deck.pop())
    hands = tuple(tuple(hands[i]) for i in range(3))
    return state._replace(deck=tuple(deck), player_hands=hands)


def _check_is_done(state: DurakGameState) -> DurakGameState:
    if len(state.deck):
        return state
    hands_left = [1 for h in state.player_hands if len(h)]
    if sum(hands_left) > 1:
        return state
    return state._replace(is_done=True)


def _distribute_cards(state: DurakGameState) -> DurakGameState:
    """
    This handles giving the cards to the defender if they have taken
    """
    if state.defender_has_taken:
        defender_hand = state.player_hands[state.defender]
        defender_hand = defender_hand + tuple(c for c in state.attack_table)
        defender_hand = defender_hand + tuple(c for c in state.defend_table)
        new_hands = tuple(
            defender_hand if i == state.defender else h
            for i, h in enumerate(state.player_hands)
        )
        #next_attacker = (state.defender + 1) % len(state.player_hands)
        return state._replace(
            player_hands=new_hands,
            #attackers=(next_attacker, ),
            #player_taking_action=next_attacker,
            attack_table=(),
            defend_table=(),
        )
    return state


def _post_step(state: DurakGameState) -> DurakGameState:
    """
    Does checks around the state to see if the game or round is over. If the round
    is over, then we need to refill cards from the deck if there still are any cards.
    """
    state = _check_is_done(state)
    if state.round_over:
        print("Round over")
        state = _give_defender_cards(state)
        state = _refill_cards(state)
        state_updates = dict(defender_has_taken=False,
                             round_over=False,
                             stopped_attacking=tuple())
        state = state._replace(**state_updates)
    return state


def step(state: DurakGameState, action_id: DurakAction) -> DurakGameState:
    """
    Takes a state and an action id and returns a new state with the action applied.
    """
    if action_id not in get_legal_actions(state):
        raise ValueError("Invalid action id: {}".format(action_id))

    if DurakAction.is_attack(action_id):
        state = step_attack_action(state, action_id)
    elif DurakAction.is_defend(action_id):
        state = step_defend_action(state, action_id)
    elif DurakAction.is_pass_with_card(action_id):
        state = step_pass_with_card_action(state, action_id)
    elif DurakAction.is_take(action_id):
        state = step_take_action(state)
    elif DurakAction.is_stop_attacking(action_id):
        state = step_stop_attack_action(state)
    else:
        raise ValueError("Invalid action id: {}".format(action_id))
    state = _check_is_done(state)
    return state


def _get_defender_actions(state: DurakGameState) -> List[DurakAction]:
    """
    Returns a tuple of legal action ids for the defender.
    """
    actions = []
    if not state.defender_has_taken:
        actions.append(DurakAction.take_action())
    ts = state.visible_card[0]
    hand = state.player_hands[state.player_taking_action]
    undefended = state.attack_table[len(state.defend_table)]

    next_defender = (state.defender + 1) % len(state.player_hands)
    if len(state.defend_table) == 0 and len(state.player_hands[next_defender]) >= len(state.attack_table) + 1:
        actions.extend([DurakAction.pass_with_card(card) for card in hand if card[1] == undefended[1]])

    for card in hand:
        if card[0] == undefended[0] and card[1] > undefended[1]:
            actions.append(DurakAction.defend(card))
        if undefended[0] != ts and card[0] == ts:
            actions.append(DurakAction.defend(card))
    return list(set(actions))


def _get_attack_actions(state: DurakGameState) -> List[DurakAction]:
    """
    Gets the attack actions. If this is the initial attack, you cannot stop attacking and can attack
    with any card in hand.
    If attack has already started, then you can stop attacking or attack with any card in hand that
    matches rank with any card on table.
    """
    if len(state.attack_table) == 0:
        return [DurakAction.attack(card) for card in state.player_hands[state.player_taking_action]]
    actions = [DurakAction.stop_attacking()]
    if len(state.attack_table) == 6 or len(state.player_hands[state.defender]) == state.num_undefended():
        return actions
    hand = state.player_hands[state.player_taking_action]
    ranks = set([card[1] for card in state.attack_table])
    ranks = ranks.union(set([card[1] for card in state.defend_table]))
    for card in hand:
        if card[1] in ranks:
            actions.append(DurakAction.attack(card))
    return actions


def get_legal_actions(state: DurakGameState) -> List[DurakAction]:
    """
    Returns a tuple of legal action ids for the player taking action.
    """
    if state.is_done:
        return []
    if state.player_taking_action == state.defender:
        return _get_defender_actions(state)
    return _get_attack_actions(state)


def _rewards(state: DurakGameState) -> List[int]:
    """
    Returns a list of rewards for each player. The defender gets 1 point for each card left in
    the deck, and the attacker gets 1 point for each card left in their hand.
    """
    if not state.is_done:
        return [0]*3
    return [1 if state.player_hands[i] == 0 else -1 for i in range(3)]


class GameRunner:
    """
    Class using functional style of state handling and keeps track of global state over
    time.
    """

    def __init__(self, players, seed=0):
        """
        Give a list of 3 player agents that conform to the interface.
        """
        self.players = players
        self.action_history = []
        self.history = [new_game_state(seed=seed)]

    def get_historical_states(self, player_id) -> List[ObservableDurakGameState]:
        """
        Returns a list of historical states for a given player
        """
        return [state.observable(player_id) for state in self.history]

    def _do_step(self, action_id: DurakAction) -> DurakGameState:
        """
        Takes a step in the game by querying the player for an action and updating the game state
        """
        state = self.history[-1]
        self.action_history.append(action_id)
        print(state.player_taking_action, DurakAction.action_to_string(action_id))
        new_state = step(state, action_id)
        self.history.append(new_state)
        return new_state

    def step(self) -> DurakGameState:
        """
        Takes a step in the game by querying the player for an action and updating the game state
        """
        state = self.history[-1]
        actions = get_legal_actions(state)
        information_state = self.get_historical_states(state.player_taking_action)
        action_id = self.players[state.player_taking_action].choose_action(information_state, actions)
        return self._do_step(action_id)

    def play(self) -> List[int]:
        """
        Plays a game of Durak and returns the rewards per player
        """
        state = self.history[-1]
        while not state.is_done:
            state = self.step()
        return _rewards(state)
