import asyncio
import math
import time
from datetime import datetime, timedelta
from operator import truediv
from typing import NamedTuple

from logging_settings import logger
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


# Генерирует новый сплит из 5 подходов, даже если старого не было или в нём было другое число подходов
def generate_new_split_new(old_split: list[Approach] = None) -> list[Approach]:
    if old_split:
        ex = old_split[0][0]
        set_old = list(map(lambda x: x[1], old_split))
        for i in range(5 - len(set_old)):
            set_old.append(0)
    else:
        ex = None
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


async def gnrt_wrkt(user_id: int, db: SQLiteDatabase, old_ex: int = None, black_list: list[int] = []) -> list[Approach]:
    """
    Функция генерирует тренировку на основе выполненных ранее тренировок, если они имеются.
    Пока основной алгоритм:
    1. Находим в истории тренировку с максимальной работой за месяц, добавляем 10%, получаем норму работы на новую тренировку.
    2. Суммируем относительную (работа/кг мышцы) недельную работу по каждой мышце,
     выясняем у какой меньше всего, будем прорабатывать её.
    3. Находим упражнения на нужную мышечную группу, с загрузкой 0.3 и выше. Выбираем то, которое реже всего встречалось в
    истории тренировок и отсутствует в постоянном и временном чёрных списках.
    4. Создаём тренировку с выбранным упражнением, для этого находим предыдущий воркаут с ним.
    5. Если осталась часть нормы работы, повторяем с пункта 2.
    :param black_list:
    :param user_id:
    :param db:
    :param old_ex:
    :return:
    """
    # Если воркаут на конкретное упражнение/тренировку:
    if old_ex:
        approaches = db.select_last_workout(user_id=user_id, exercise_id=old_ex)
        if approaches:
            workout_id = approaches['workout_id']
            workouts = db.select_rows(table='approaches', fetch='all', workout_id=workout_id, exercise=old_ex)
            old_wrkt = [Approach(old_ex, workout['dynamic'], False) if i in {0, 2, 3} else
                        Approach(old_ex, workout['dynamic'], True)
                        for i, workout in enumerate(workouts)]
            return generate_new_split_new(old_wrkt)
        else:
            return [Approach(old_ex, 1, False), Approach(old_ex, 1, False), Approach(old_ex, 1, False),
                    Approach(old_ex, 1, False), Approach(old_ex, 1, True)]
    # если нет, то будем собирать из разных упражнений:
    else:
        approaches = db.select_rows(table='approaches', fetch='all', user_id=user_id)
        if approaches:  # продумать алгоритм
            #  1. Находим в истории тренировку с максимальной работой за месяц, добавляем 10%,
            #  получаем норму работы на новую тренировку.
            month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            # максимальная работа среди всех воркаутов (выдаётся воркаут, надо обработать ещё)
            max_work = db.select_filtered_sorted_rows(table='workouts', sql2=f' AND date > {month_ago} ORDER BY work DESC',
                                                      fetch='one', user_id=user_id)
            #  2. Суммируем относительную (работа/кг мышцы) недельную работу по каждой мышце,
            #      выясняем у какой меньше всего, будем прорабатывать её.
            cells = ['work', 'arms', 'legs', 'chest', 'abs', 'back']
            masses = [1, 0.21, 0.55, 0.06, 0.06, 0.12]
            works = db.sum_filtered_sorted_rows(table='approaches', cells=cells, sql2=f' AND date > {week_ago}',
                                                tuple_=True, fetch='all', user_id=user_id)[0]
            works = list(map(truediv, works, masses))
            cells = dict(zip(cells, works))
            min_cell = min(cells, key=cells.get)
            logger.debug(f'{min_cell=}')
            #  3. Находим упражнения на нужную мышечную группу, с загрузкой > 0.2. Выбираем то, которое реже всего
            #  встречалось в истории тренировок за последний месяц и отсутствует в постоянном и временном чёрных списках.
            exercises = db.select_filtered_sorted_rows(table='exercises_muscles', fetch='all',
                                                       sql2=f' AND load > 0.2 ORDER BY exercise_id ASC',
                                                       muscle_name=min_cell)
            exercises_voc = {}
            for exercise in exercises:
                exercises_voc[exercise['exercise_id']] = 0
            exercises = db.select_filtered_sorted_rows(table='approaches', fetch='all',
                                                       sql2=f' AND date > {month_ago} ORDER BY exercise_id ASC',
                                                       user_id=user_id)
            for exercise in exercises:
                exercises_voc[exercise['exercise_id']] += 1
            logger.debug(f'{black_list=}')
            blocked_exercises = db.select_rows(table='exercises_users', fetch='all', user_id=user_id, list=0)
            for exercise in blocked_exercises:
                if exercise['exercise_id'] not in black_list:
                    black_list.append(exercise['exercise_id'])
            logger.debug(f'{black_list=}')
            for ex in black_list:
                exercises_voc.pop(ex, '')
            rare_exercise = min(exercises_voc, key=exercises_voc.get)
            logger.debug(f'{rare_exercise=}')
            #  4. Создаём тренировку с выбранным упражнением, для этого находим предыдущий воркаут с ним.
            workout_id = db.select_filtered_sorted_rows(table='approaches', fetch='one',
                                                        sql2=f' ORDER BY approach_id DESC',
                                                        user_id=user_id, exercise_id=rare_exercise)['workout_id']
            approaches = db.select_filtered_sorted_rows(table='approaches', fetch='all',
                                                        sql2=f' ORDER BY number ASC',
                                                        workout_id=workout_id)
            old_wrkt = [Approach(rare_exercise, approach['dynamic'], False) if i in {0, 2, 3} else
                        Approach(rare_exercise, approach['dynamic'], True)
                        for i, approach in enumerate(approaches)]
            logger.debug(f'{old_wrkt=}')
            return generate_new_split_new(old_wrkt)
        else:
            # Если до этого ещё не было тренировок, то предлагается набор из самых простых упражнений на разные группы мышц,
            # так называемый входной тест: отжимания на коленях, гиперэкстензии, подъем ног, приседания, гусеница
            return [Approach(4, 1, True), Approach(12, 1, True), Approach(24, 1, True),
                    Approach(8, 1, True), Approach(27, 1, True)]


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
