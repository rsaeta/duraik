"""
This file tests the Durak Game engine
"""

from game import DurakGame, DurakAction, DurakDeck
from agents import RandomPlayer


def get_normal_random_game() -> DurakGame:
    game = DurakGame()
    game.configure({
        'game_num_players': 3,
        'lowest_card': 6,
        'agents': [RandomPlayer] * 3,
        'seed': 0,
    })
    game.init_game()
    return game


def test_game_ending_easy():
    game = get_normal_random_game()
    hands = [
        [('S', 6), ],
        [('S', 7), ],
        [('S', 8), ],
    ]
    visible_card = (9, 'S')
    for player, hand in zip(game.players, hands):
        player.hand = hand
    game.visible_card = visible_card
    game.player_taking_action = 2
    game.defender = 0
    game.attackers = [2]
    game.is_done = False
    game.deck.deck = []
    game.graveyard = DurakDeck.deck_without(hands[0] + hands[1] + hands[2]).deck

    assert game.get_legal_actions(game.player_taking_action) == [DurakAction.attack_id_from_card(('S', 8))]
    game.step()
    assert game.player_taking_action == 0
    assert game.get_legal_actions(game.player_taking_action) == [DurakAction.take_action()]
    game.step()
    assert game.player_taking_action == 1
    assert len(game.players[0].hand) == 2
    assert len(game.players[1].hand) == 1
    assert len(game.players[2].hand) == 0
    assert game.get_legal_actions(game.player_taking_action) == [DurakAction.attack_id_from_card(('S', 7))]

    game.step()
    assert game._is_game_over()
    assert game.is_done
    assert game.player_taking_action == game.defender
    assert set(game.get_legal_actions(game.player_taking_action)) == {DurakAction.defend_id_from_card(('S', 8)),
                                                                      DurakAction.take_action()}
    print(game)


def test_passing():
    game = get_normal_random_game()
    hands = [
        [('S', 6), ('H', 12), ('D', 14), ('S', 7)],
        [('C', 6), ('C', 14)],
        [('D', 6), ('D', 11)],
    ]

    visible_card = ('S', 9)
    for player, hand in zip(game.players, hands):
        player.hand = hand
    game.visible_card = visible_card
    game.player_taking_action = 0
    game.defender = 1
    game.attackers = [0]
    game.is_done = False
    game.deck.deck = []
    game.graveyard = DurakDeck.deck_without(hands[0] + hands[1] + hands[2]).deck

    assert set(game.legal_actions()) == {DurakAction.attack(('S', 6)),
                                         DurakAction.attack(('H', 12)),
                                         DurakAction.attack(('D', 14)),
                                         DurakAction.attack(('S', 7))}
    game._do_step(0, DurakAction.attack(('S', 6)))
    assert set(game.legal_actions()) == {DurakAction.stop_attacking_action()}
    game.step()
    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.take_action(),
                                         DurakAction.pass_with_card(('C', 6))}
    game._do_step(1, DurakAction.pass_with_card(('C', 6)))
    assert game.defender == 2
    assert game.attackers == [0, 1]
    assert game.player_taking_action == 1
    assert set(game.legal_actions()) == {DurakAction.stop_attacking()}
    game.step()
    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.take_action(), DurakAction.pass_with_card(('D', 6))}
    game._do_step(2, DurakAction.pass_with_card(('D', 6)))
    assert game.defender == 0
    assert game.attackers == [1, 2]
    assert game.player_taking_action == 2
    assert set(game.legal_actions()) == {DurakAction.stop_attacking()}
    game.step()
    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.take_action(),
                                         DurakAction.defend(('S', 7))}
    game._do_step(0, DurakAction.defend(('S', 7)))
    print([DurakAction.action_to_string(action) for action in game.legal_actions()])
    assert set(game.legal_actions()) == {DurakAction.take_action()}
    game.step()
    assert game.player_taking_action == 1
    assert game.legal_actions() == [DurakAction.attack(('C', 14))]
    assert game.defender == 2
    game.step()
    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.take_action()}
    game.step()
    assert game.player_taking_action == 0
    assert game.attackers == [0]
    assert game.defender == 2
    assert len(game.get_defender().hand) == 2
    assert set(game.legal_actions()) == {DurakAction.attack(('H', 12)),
                                         DurakAction.attack(('D', 14)),
                                         DurakAction.attack(('S', 7)),
                                         DurakAction.attack(('S', 6)),
                                         DurakAction.attack(('C', 6)),
                                         DurakAction.attack(('D', 6))}
    game._do_step(0, DurakAction.attack(('H', 12)))
    assert game.legal_actions() == [DurakAction.stop_attacking_action()]
    game.step()
    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.take_action()}
    game.step()
    assert game.player_taking_action == 0
    assert game.legal_actions() == [DurakAction.stop_attacking()]
    game.step()

    assert game.player_taking_action == 0
    assert game.attackers == [0]
    assert len(game.attack_table) == len(game.defend_table) == 0
    assert game.defender == 2
    assert set(game.legal_actions()) == {DurakAction.attack(('S', 6)),
                                         DurakAction.attack(('S', 7)),
                                         DurakAction.attack(('D', 14)),
                                         DurakAction.attack(('C', 6)),
                                         DurakAction.attack(('D', 6))}
    game._do_step(0, DurakAction.attack(('S', 6)))
    assert set(game.legal_actions()) == {DurakAction.stop_attacking_action(),
                                         DurakAction.attack(('C', 6)),
                                         DurakAction.attack(('D', 6))}
    game._do_step(0, DurakAction.attack(('C', 6)))
    assert set(game.legal_actions()) == {DurakAction.stop_attacking_action(), DurakAction.attack(('D', 6))}
    game._do_step(0, DurakAction.attack(('D', 6)))
    assert len(game.attack_table) == 3
    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.take_action()}
    game.step()
    assert game.player_taking_action == 0
    assert game.attackers == [0]
    assert len(game.attack_table) == len(game.defend_table) == 0
    assert game.defender == 2
    assert set(game.legal_actions()) == {DurakAction.attack(('S', 7)), DurakAction.attack(('D', 14))}
    game._do_step(0, DurakAction.attack(('D', 14)))
    assert set(game.legal_actions()) == {DurakAction.stop_attacking_action()}
    game.step()
    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.defend(('S', 6)), DurakAction.take_action()}
    game._do_step(2, DurakAction.defend(('S', 6)))
    assert game.player_taking_action == 0
    assert set(game.legal_actions()) == {DurakAction.stop_attacking()}
    game.step()
    assert game.player_taking_action == 2
    assert game.attackers == [2]
    assert len(game.attack_table) == len(game.defend_table) == 0
    assert game.defender == 0
    assert set(game.legal_actions()) == {DurakAction.attack(('C', 6)),
                                         DurakAction.attack(('D', 6)),
                                         DurakAction.attack(('D', 11)),
                                         DurakAction.attack(('H', 12)),
                                         DurakAction.attack(('C', 14))}

    game._do_step(2, DurakAction.attack(('C', 6)))

    assert game.player_taking_action == game.defender
    assert set(game.legal_actions()) == {DurakAction.take_action(), DurakAction.defend(('S', 7))}

    game._do_step(0, DurakAction.defend(('S', 7)))
    assert game.is_done


if __name__ == '__main__':
    test_passing()
