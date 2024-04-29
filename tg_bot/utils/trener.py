import asyncio
import math
import time
from typing import NamedTuple


class Approach(NamedTuple):
    exercise: int = 0
    repetitions: int = 0


class Split(NamedTuple):
    s1: int = 0
    s2: int = 0
    s3: int = 0
    s4: int = 0
    s5: int = 0


def generate_new_split_split(split: Split) -> Split:
    new_split = Split(
        max(1, math.floor(max(split) / 2)),
        max(split),
        math.ceil(max(split) / 2),
        math.ceil(max(split) / 2),
        max(0, sum(split) - max(1, math.floor(max(split) / 2)) - max(split) - 2 * math.ceil(max(split) / 2) + 1)
    )
    return tuple(new_split)


def generate_new_split(set_str: str) -> str:
    set_symbols = set_str.split(' ')
    set_old = list(map(int, set_symbols))
    set_new = [0, 0, 0, 0, 0]
    set_new[0] = str(max(1, math.floor(max(set_old) / 2)))
    set_new[1] = str(max(set_old))
    set_new[2] = str(math.ceil(max(set_old) / 2))
    set_new[3] = str(math.ceil(max(set_old) / 2))
    set_new[4] = str(max(0, sum(set_old) - max(1, math.floor(max(set_old) / 2)) - max(set_old) - 2 * math.ceil(max(set_old) / 2) + 1))
    return ' '.join(set_new)


if __name__ == '__main__':
    # user_split = Split(*map(int, input('Input split: ').split()))
    # print(*user_split)
    # while True:
    #     time.sleep(1)
    #     user_split = generate_new_split(user_split)
    #     print(*user_split)

    user_split = input('Input split: ')
    print(user_split)
    while True:
        time.sleep(1)
        user_split = generate_new_split(user_split)
        print(user_split)


    # print(generate_new_split([1,1,0,0,1]))
    # asyncio.run(generate_new_split([1,1,0,0,1]))
