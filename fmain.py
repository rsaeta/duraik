from game import GameRunner
from agents import RandomPlayer, HumanPlayer


def main():
    game = GameRunner([*[RandomPlayer(i, hand=[]) for i in range(2)], HumanPlayer(2)])
    game.play()


if __name__ == '__main__':
    main()
