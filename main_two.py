from two_game import game


def main():
    state = game.new_state(1, lowest_rank=11)
    while not state.is_done:
        actions = game.legal_actions(state)
        print(actions)
        print(state)
        state = game.step(state, actions[-1])
    print(state)
    print(game.rewards(state))


if __name__ == '__main__':
    main()
