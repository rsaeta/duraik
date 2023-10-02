from game import DurakGame, DurakAction, ObservableDurakGameState, DurakDeck
from agents import RandomPlayer, DQAgent
from agents.mcts import random_game_from_observation_state


easy_state = ObservableDurakGameState(
    player_id=2,
    hand=(('H', 14), ),
    visible_card=('H', 6),
    attack_table=(('S', 6), ),
    defend_table=tuple(),
    num_cards_left_in_deck=0,
    num_cards_in_hands=(10, 10, 1),
    graveyard=tuple(),
    is_done=False,
    lowest_rank=6,
    attackers=(1, ),
    defender=2,
    acting_player=2,
    defender_has_taken=False,
    stopped_attacking=tuple(),
    available_actions=(DurakAction.take_action(), DurakAction.defend_id_from_card(('H', 14)), ),
)


def easy_main(*args, **kwargs):
    agent = DQAgent(150, DurakAction.num_actions(), 2, hand=(('H', 14), ))
    for epoch in range(100):
        game = random_game_from_observation_state(easy_state)
        agent.hand = game.players[2].hand
        game.players[2] = agent

        print(f'playing game {epoch+1}')
        while not game.is_done:
            game.step()
        print(game.players)
        game.players[2].update()
    print('Done')


def main(*args, **kwargs):
    print(args, kwargs)
    gconfig = {
        'game_num_players': 3,
        'lowest_card': 6,
        'agents': [RandomPlayer, RandomPlayer, lambda i, hand: DQAgent(
            150, DurakAction.num_actions(), i, hand=hand
        )],
    }

    game = DurakGame()
    game.configure(gconfig)
    game.init_game()

    game.players[2].load()
    i = 0
    while i < 1e6:
        game.reset_game()
        print('playing game ', i)
        while not game.is_done:
            game.step()
        print(game.players)
        for _ in range(5):
            game.players[2].update()
        game.players[2].save()
        i += 1


if __name__ == '__main__':
    easy_main()
