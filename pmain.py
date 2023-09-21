"""
Calls main in parallel
"""
from multiprocessing import Pool
import main as mn


def main():
    pool = Pool(4)
    pool.map(mn.main, range(100))


if __name__ == '__main__':
    main()
