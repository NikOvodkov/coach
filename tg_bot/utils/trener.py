import asyncio
import math
import time
from typing import NamedTuple

from tg_bot.database.sqlite2 import SQLiteDatabase


class Approach(NamedTuple):
    exercise: int = None
    repetitions: int = None
    max: bool = None


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
    # первый подход = половине от максимума на прошлой тренировке
    set_new[0] = max(1, math.floor(max(set_old) / 2))
    # второй подход = максимуму+ на прошлой тренировке
    set_new[1] = max(set_old)
    # третий подход = половине от максимума на прошлой тренировке + 1
    set_new[2] = math.ceil(max(set_old) / 2) + 1
    # четвёртый подход = половине от максимума на прошлой тренировке
    set_new[3] = math.ceil(max(set_old) / 2)
    # пятый подход
    set_new[4] = max(1, sum(set_old) - set_new[0] - set_new[1] - set_new[2] - set_new[3] + 1)
    if set_new[4] > set_new[1] - 2:
        set_new[1] += 1
        set_new[4] = max(1, sum(set_old) - set_new[0] - set_new[1] - set_new[2] - set_new[3] + 1)
    set_new = list(map(str, set_new))
    return ' '.join(set_new)


def generate_new_split_new(old_split: list[Approach] = None) -> list[Approach]:
    if old_split:
        ex = old_split[0][0]
        set_old = list(map(lambda x: x[1], old_split))
    else:
        ex = 0
        set_old = [1, 1, 1, 1, 1]
    set_new = [0, 0, 0, 0, 0]
    new_split = [Approach(), Approach(), Approach(), Approach(), Approach()]
    # первый подход = половине от максимума на прошлой тренировке
    set_new[0] = max(1, math.floor(max(set_old) / 2))
    new_split[0] = [Approach(ex, set_new[0], False)]
    # второй подход = максимуму+ на прошлой тренировке
    set_new[1] = max(set_old)
    new_split[1] = [Approach(ex, set_new[1], True)]
    # третий подход = половине от максимума на прошлой тренировке + 1
    set_new[2] = math.ceil(max(set_old) / 2) + 1
    new_split[2] = [Approach(ex, set_new[2], False)]
    # четвёртый подход = половине от максимума на прошлой тренировке
    set_new[3] = math.ceil(max(set_old) / 2)
    new_split[3] = [Approach(ex, set_new[3], False)]
    # пятый подход
    set_new[4] = max(1, sum(set_old) - set_new[0] - set_new[1] - set_new[2] - set_new[3] + 1)
    new_split[4] = [Approach(ex, set_new[4], True)]
    if set_new[4] > set_new[1] - 2:
        set_new[1] += 1
        new_split[1] = [Approach(ex, set_new[1], True)]
        set_new[4] = max(1, sum(set_old) - set_new[0] - set_new[1] - set_new[2] - set_new[3] + 1)
        new_split[4] = [Approach(ex, set_new[4], True)]
    return new_split





async def gnrt_wrkt(user_id: int, db: SQLiteDatabase, old_ex: int = None) -> list[Approach]:
    if old_ex:
        approaches = db.select_last_workout(user_id=user_id, exercise_id=old_ex)
        if approaches:
            workout_id = approaches['workout_id']
            workout = db.select_rows(table='approaches', fetch='all', workout_id=workout_id, exercise=old_ex)
            old_wrkt = []
        else:
            return [Approach(old_ex, 1, False), Approach(old_ex, 1, False), Approach(old_ex, 1, False),
                    Approach(old_ex, 1, False), Approach(old_ex, 1, True)]

    old_wrkt = list[Approach] = None
    if old_wrkt:  # Если до этого уже были тренировки,
        if old_ex:  # и упражнение выбрано
            return generate_new_split_new(old_wrkt)
        else:  # и упражнение ещё не выбрано
            pass
        new_workout = old_wrkt
        return new_workout
    elif old_ex:  # Если до этого ещё не было тренировок, но упражнение уже выбрано:
        return [Approach(old_ex, 1, False), Approach(old_ex, 1, False), Approach(old_ex, 1, False),
                Approach(old_ex, 1, False), Approach(old_ex, 1, True)]
    else:  # Если до этого ещё не было тренировок, и упражнение ещё не выбрано,
        # то предлагается набор из самых простых упражнений на разные группы мышц, так называемый входной тест:
        # отжимания на коленях, гиперэкстензии, подъем ног, приседания, гусеница
        return [Approach(4, 1, True), Approach(12, 1, True), Approach(24, 1, True), Approach(8, 1, True), Approach(27, 1, True)]


if __name__ == '__main__':
    # user_split = Split(*map(int, input('Input split: ').split()))
    # print(*user_split)
    # while True:
    #     time.sleep(1)
    #     user_split = generate_new_split(user_split)
    #     print(*user_split)

    user_split = input('Input split: ')
    print(generate_new_split_new(list(map(lambda x: Approach(0, int(x), False), user_split.split()))))
    # while True:
    #     time.sleep(1)
    #     user_split = generate_new_split(user_split)
    #     print(user_split)

    # print(generate_new_split([1,1,0,0,1]))
    # asyncio.run(generate_new_split([1,1,0,0,1]))
