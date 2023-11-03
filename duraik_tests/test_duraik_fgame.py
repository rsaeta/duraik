"""
This file tests the Durak Game engine
"""
import numpy as np
from typing import List

from game import DurakAction, DurakDeck, DurakGameState, Card, GameRunner
from game import fgame
from agents import RandomPlayer


def test_game_ending_easy():
    hands: List[List[Card]] = [
        [('S', 6), ],
        [('S', 7), ],
        [('S', 8), ],
    ]
    visible_card: Card = ('S', 9)
    state = DurakGameState(
        np_rand=np.random.RandomState(0),
        defender_has_taken=False,
        deck=(),
        visible_card=visible_card,
        attackers=(2,),
        defender=0,
        player_hands=tuple(tuple(hand) for hand in hands),
        attack_table=(),
        defend_table=(),
        stopped_attacking=(),
        player_taking_action=2,
        graveyard=(),
        is_done=False,
        round_over=False,
    )
    runner = GameRunner([RandomPlayer(i) for i in range(3)])
    runner.history = [state]
    assert fgame._get_legal_actions(state) == [DurakAction.attack_id_from_card(('S', 8))]
    new_state = runner.step()
    assert new_state.player_taking_action == 0
    assert fgame._get_legal_actions(new_state) == [DurakAction.take_action()]
    new_state = runner.step()
    assert new_state.player_taking_action == 1
    assert len(new_state.player_hands[0]) == 2
    assert len(new_state.player_hands[1]) == 1
    assert len(new_state.player_hands[2]) == 0

    assert fgame._get_legal_actions(new_state) == [DurakAction.attack_id_from_card(('S', 7))]

    new_state = runner.step()
    assert new_state.is_done
    print(new_state)


def test_passing():
    hands: List[List[Card]] = [
        [('S', 6), ('H', 12), ('D', 14), ('S', 7)],
        [('C', 6), ('C', 14)],
        [('D', 6), ('D', 11)],
    ]

    visible_card: Card = ('S', 9)
    state = DurakGameState(
        np_rand=np.random.RandomState(0),
        defender_has_taken=False,
        deck=(),
        visible_card=visible_card,
        attackers=(0,),
        defender=1,
        player_hands=tuple(tuple(hand) for hand in hands),
        attack_table=(),
        defend_table=(),
        stopped_attacking=(),
        player_taking_action=0,
        graveyard=(),
        is_done=False,
        round_over=False,
    )
    runner = GameRunner([RandomPlayer(i) for i in range(3)])
    runner.history = [state]

    assert set(fgame._get_legal_actions(state)) == {DurakAction.attack(('S', 6)),
                                                    DurakAction.attack(('H', 12)),
                                                    DurakAction.attack(('D', 14)),
                                                    DurakAction.attack(('S', 7))}
    new_state = runner._do_step(DurakAction.attack(('S', 6)))
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.stop_attacking_action()}
    new_state = runner.step()
    assert new_state.player_taking_action == new_state.defender

    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action(),
                                                        DurakAction.pass_with_card(('C', 6))}
    new_state = runner._do_step(DurakAction.pass_with_card(('C', 6)))
    assert new_state.defender == 2
    assert new_state.attackers == tuple([0, 1])
    assert new_state.player_taking_action == 1
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.stop_attacking()}
    new_state = runner.step()
    assert new_state.player_taking_action == new_state.defender
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action(), DurakAction.pass_with_card(('D', 6))}
    new_state = runner._do_step(DurakAction.pass_with_card(('D', 6)))
    assert new_state.defender == 0
    assert new_state.attackers == (1, 2)
    assert new_state.player_taking_action == 2
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.stop_attacking()}
    new_state = runner.step()
    assert new_state.player_taking_action == new_state.defender
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action(),
                                                        DurakAction.defend(('S', 7))}
    new_state = runner._do_step(DurakAction.defend(('S', 7)))
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action()}
    new_state = runner.step()
    assert new_state.player_taking_action == 1
    assert fgame._get_legal_actions(new_state) == [DurakAction.attack(('C', 14))]
    assert new_state.defender == 2
    new_state = runner.step()
    assert new_state.player_taking_action == new_state.defender
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action()}
    new_state = runner.step()
    assert new_state.player_taking_action == 0
    assert new_state.attackers == (0,)
    assert new_state.defender == 2
    assert len(new_state.player_hands[new_state.defender]) == 2
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.attack(('H', 12)),
                                                        DurakAction.attack(('D', 14)),
                                                        DurakAction.attack(('S', 7)),
                                                        DurakAction.attack(('S', 6)),
                                                        DurakAction.attack(('C', 6)),
                                                        DurakAction.attack(('D', 6))}
    new_state = runner._do_step(DurakAction.attack(('H', 12)))
    assert fgame._get_legal_actions(new_state) == [DurakAction.stop_attacking_action()]
    new_state = runner.step()
    assert new_state.player_taking_action == new_state.defender
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action()}
    new_state = runner.step()
    assert new_state.player_taking_action == 0
    assert fgame._get_legal_actions(new_state) == [DurakAction.stop_attacking()]
    new_state = runner.step()

    assert new_state.player_taking_action == 0
    assert new_state.attackers == (0,)
    assert len(new_state.attack_table) == len(new_state.defend_table) == 0
    assert new_state.defender == 2
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.attack(('S', 6)),
                                                        DurakAction.attack(('S', 7)),
                                                        DurakAction.attack(('D', 14)),
                                                        DurakAction.attack(('C', 6)),
                                                        DurakAction.attack(('D', 6))}
    new_state = runner._do_step(DurakAction.attack(('S', 6)))
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.stop_attacking_action(),
                                                        DurakAction.attack(('C', 6)),
                                                        DurakAction.attack(('D', 6))}
    new_state = runner._do_step(DurakAction.attack(('C', 6)))
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.stop_attacking_action(),
                                                        DurakAction.attack(('D', 6))}
    new_state = runner._do_step(DurakAction.attack(('D', 6)))
    assert len(new_state.attack_table) == 3
    assert new_state.player_taking_action == new_state.defender
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action()}
    new_state = runner.step()
    assert new_state.player_taking_action == 0
    assert new_state.attackers == (0,)
    assert len(new_state.attack_table) == len(new_state.defend_table) == 0
    assert new_state.defender == 2
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.attack(('S', 7)), DurakAction.attack(('D', 14))}
    new_state = runner._do_step(DurakAction.attack(('D', 14)))
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.stop_attacking_action()}
    new_state = runner.step()
    assert new_state.player_taking_action == new_state.defender
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.defend(('S', 6)), DurakAction.take_action()}
    new_state = runner._do_step(DurakAction.defend(('S', 6)))
    assert new_state.player_taking_action == 0
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.stop_attacking()}
    new_state = runner.step()
    assert new_state.player_taking_action == 2
    assert new_state.attackers == (2,)
    assert len(new_state.attack_table) == len(new_state.defend_table) == 0
    assert new_state.defender == 0
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.attack(('C', 6)),
                                                        DurakAction.attack(('D', 6)),
                                                        DurakAction.attack(('D', 11)),
                                                        DurakAction.attack(('H', 12)),
                                                        DurakAction.attack(('C', 14))}

    new_state = runner._do_step(DurakAction.attack(('C', 6)))

    assert new_state.player_taking_action == new_state.defender
    assert set(fgame._get_legal_actions(new_state)) == {DurakAction.take_action(), DurakAction.defend(('S', 7))}

    new_state = runner._do_step(DurakAction.defend(('S', 7)))
    assert new_state.is_done


if __name__ == '__main__':
    test_passing()
