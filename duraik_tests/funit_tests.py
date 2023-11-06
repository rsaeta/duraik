from game import DurakAction, DurakDeck
from game import fgame as f
import numpy as np

nprand = np.random.RandomState(0)


def test_take():
    hands = ((('H', 14), ('C', 13), ('C', 7), ('S', 12), ('D', 6), ('D', 7)),
             (('D', 13), ('H', 8), ('C', 8), ('D', 11), ('C', 9), ('S', 9)),
             (('H', 6), ('C', 14), ('D', 8), ('H', 12), ('S', 7), ('H', 13)))
    deck = DurakDeck.deck_without(hands[0] + hands[1] + hands[2], 69420).deck
    state = f.DurakGameState(
        nprand,
        defender_has_taken=False,
        deck=deck,
        attackers=(0,),
        visible_card=('S', 6),
        defender=1,
        player_hands=hands,
        attack_table=(),
        defend_table=(),
        stopped_attacking=(),
        player_taking_action=0,
        graveyard=(),
        is_done=False,
        round_over=False,
    )
    new_state = f.step_attack_action(state, DurakAction.attack_id_from_card(('C', 7)))
    new_state = f.step_attack_action(new_state, DurakAction.attack_id_from_card(('D', 7)))
    new_state = f.step_stop_attack_action(new_state)
    assert not new_state.defender_has_taken
    assert DurakAction.take_action() in f.get_legal_actions(new_state)
    new_state = f.step_take_action(new_state)
    assert new_state.defender_has_taken
    assert new_state.player_taking_action == 0
    assert DurakAction.stop_attacking_action() in f.get_legal_actions(new_state)
    new_state = f.step_stop_attack_action(new_state)
    assert new_state.player_taking_action == 2
    assert DurakAction.stop_attacking_action() in f.get_legal_actions(new_state)
    new_state = f.step_stop_attack_action(new_state)
    assert new_state.player_taking_action == 2
    assert new_state.defender == 0
    assert list(map(len, new_state.player_hands)) == [6, 8, 6]


def test_not_take():
    hands = ((('H', 14), ('C', 13), ('C', 7), ('S', 12), ('D', 6), ('D', 7)),
             (('D', 13), ('H', 8), ('C', 8), ('D', 11), ('C', 9), ('S', 9)),
             (('H', 6), ('C', 14), ('D', 8), ('H', 12), ('S', 7), ('H', 13)))
    deck = DurakDeck.deck_without(hands[0] + hands[1] + hands[2], 69420).deck
    state = f.DurakGameState(
        nprand,
        defender_has_taken=False,
        deck=deck,
        attackers=(0,),
        visible_card=('S', 6),
        defender=1,
        player_hands=hands,
        attack_table=(),
        defend_table=(),
        stopped_attacking=(),
        player_taking_action=0,
        graveyard=(),
        is_done=False,
        round_over=False,
    )
    new_state = f.step_attack_action(state, DurakAction.attack_id_from_card(('C', 7)))
    new_state = f.step_attack_action(new_state, DurakAction.attack_id_from_card(('D', 7)))
    new_state = f.step_stop_attack_action(new_state)
    assert not new_state.defender_has_taken
    assert new_state.player_taking_action == new_state.defender
    assert len(new_state.player_hands[0]) == 4
    assert len(new_state.player_hands[1]) == 6
    assert len(new_state.player_hands[2]) == 6
    assert len(new_state.attack_table) == 2
    assert len(new_state.defend_table) == 0
    assert DurakAction.defend_id_from_card(('C', 8)) in f.get_legal_actions(new_state)
    new_state = f.step_defend_action(new_state, DurakAction.defend_id_from_card(('C', 8)))
    assert DurakAction.defend_id_from_card(('D', 11)) in f.get_legal_actions(new_state)
    new_state = f.step_defend_action(new_state, DurakAction.defend_id_from_card(('D', 11)))
    assert new_state.player_taking_action == 0
    assert len(new_state.player_hands[0]) == 4
    assert len(new_state.player_hands[1]) == 4
    assert len(new_state.player_hands[2]) == 6
    assert len(new_state.attack_table) == 2
    assert len(new_state.defend_table) == 2
    new_state = f.step_stop_attack_action(new_state)
    assert new_state.player_taking_action == 2
    new_state = f.step_attack_action(new_state, DurakAction.attack_id_from_card(('S', 7)))
    new_state = f.step_stop_attack_action(new_state)
    assert new_state.player_taking_action == new_state.defender
    assert len(new_state.attack_table) == 3
    assert len(new_state.defend_table) == 2
    assert DurakAction.defend_id_from_card(('S', 9)) in f.get_legal_actions(new_state)
    new_state = f.step_defend_action(new_state, DurakAction.defend_id_from_card(('S', 9)))
    assert new_state.player_taking_action == 2
    assert len(new_state.stopped_attacking) == 0
    new_state = f.step_stop_attack_action(new_state)
    assert new_state.player_taking_action == 0
    new_state = f.step_stop_attack_action(new_state)
    assert new_state.player_taking_action == 1
    assert new_state.defender == 2
    assert list(map(len, new_state.player_hands)) == [6]*3


def test_stop_attacking():
    state = f.DurakGameState(
        nprand,
        defender_has_taken=False,
        deck=(),
        attackers=(0,),
        visible_card=('S', 9),
        defender=1,
        player_hands=((('S', 6), ('S', 7)),
                      (('H', 12),),
                      (('D', 14),)),
        attack_table=(('S', 10),),
        stopped_attacking=(),
        defend_table=(('S', 11),),
        player_taking_action=0,
        graveyard=(),
        is_done=False,
        round_over=False,
    )
    new_state = f.step_stop_attack_action(state)
    assert new_state.stopped_attacking == (0,)
    assert new_state.player_taking_action == 2

    newer_state = f.step_stop_attack_action(new_state)
    assert newer_state.attack_table == ()
    assert newer_state.defend_table == ()
    assert newer_state.attackers == (state.defender,)
    assert newer_state.player_taking_action == 1
    assert set(newer_state.graveyard) == {('S', 10), ('S', 11)}
    assert list(map(len, newer_state.player_hands)) == [2, 1, 1]


if __name__ == '__main__':
    test_take()
