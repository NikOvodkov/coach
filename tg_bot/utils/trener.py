import asyncio
import math
import time
from datetime import datetime, timedelta
from operator import truediv
from typing import NamedTuple

from aiogram.types import ReplyKeyboardRemove

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.keyboards.trener import ready


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
def generate_new_split_new(old_split: list[Approach] = None, exercise_id: int = 4) -> list[Approach]:
    if old_split:
        exercise_id = old_split[0][0]
        set_old = list(map(lambda x: x[1], old_split))
        for i in range(5 - len(set_old)):
            set_old.append(0)
    else:
        set_old = [1, 1, 1, 1, 1]
    set_new = [0, 0, 0, 0, 0]
    new_split = [Approach(), Approach(), Approach(), Approach(), Approach()]
    # первый подход = половине от максимума на прошлой тренировке
    set_new[0] = max(1, math.floor(max(set_old) / 2))
    new_split[0] = Approach(exercise_id, set_new[0], False)
    # второй подход = максимуму+ на прошлой тренировке
    set_new[1] = max(set_old)
    new_split[1] = Approach(exercise_id, set_new[1], True)
    # третий подход = половине от максимума на прошлой тренировке + 1
    set_new[2] = math.ceil(max(set_old) / 2) + 1
    new_split[2] = Approach(exercise_id, set_new[2], False)
    # четвёртый подход = половине от максимума на прошлой тренировке
    set_new[3] = math.ceil(max(set_old) / 2)
    new_split[3] = Approach(exercise_id, set_new[3], False)
    # пятый подход
    set_new[4] = max(1, sum(set_old) - set_new[0] - set_new[1] - set_new[2] - set_new[3] + 1)
    new_split[4] = Approach(exercise_id, set_new[4], True)
    if set_new[4] > set_new[1] - 2:
        set_new[1] += 1
        new_split[1] = Approach(exercise_id, set_new[1], True)
        set_new[4] = max(1, sum(set_old) - set_new[0] - set_new[1] - set_new[2] - set_new[3] + 1)
        new_split[4] = Approach(exercise_id, set_new[4], True)
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
    if old_ex is not None:
        logger.debug(f'{old_ex=}')
        approaches = db.select_filtered_sorted_rows(table='approaches', fetch='one',
                                                    sql2=f' ORDER BY approach_id DESC',
                                                    user_id=user_id, exercise_id=old_ex)
        if approaches:
            logger.debug('old_ex approaches')
            workout_id = approaches['workout_id']
            logger.debug(f'{workout_id=}')
            workouts = db.select_rows(table='approaches', fetch='all', workout_id=workout_id, exercise_id=old_ex)
            logger.debug(f'{workouts=}')
            old_wrkt = [Approach(old_ex, workout['dynamic'], False) if i in {0, 2, 3} else
                        Approach(old_ex, workout['dynamic'], True)
                        for i, workout in enumerate(workouts)]
            logger.debug(f'{old_wrkt=}')
            return generate_new_split_new(old_wrkt)
        else:
            logger.debug('old_ex no approaches')
            return [Approach(old_ex, 1, False), Approach(old_ex, 1, False), Approach(old_ex, 1, False),
                    Approach(old_ex, 1, False), Approach(old_ex, 1, True)]
    # если нет, то будем собирать из разных упражнений:
    else:
        logger.debug('no old_ex')
        approaches = db.select_rows(table='approaches', fetch='all', user_id=user_id)
        if approaches:  # продумать алгоритм
            logger.debug('approaches no old_ex')
            #  1. Находим в истории тренировку с максимальной работой за месяц, добавляем 10%,
            #  получаем норму работы на новую тренировку.
            month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            # максимальная работа среди всех воркаутов (выдаётся воркаут, надо обработать ещё)
            logger.debug(f'{month_ago=}')
            max_work = db.select_filtered_sorted_rows(table='workouts', sql2=f' AND date > "{month_ago}" ORDER BY work DESC',
                                                      fetch='one', user_id=user_id)
            logger.debug(f'{max_work=}')
            #  2. Суммируем относительную (работа/кг мышцы) недельную работу по каждой мышце,
            #      выясняем у какой меньше всего, будем прорабатывать её.
            cells = ['work', 'arms', 'legs', 'chest', 'abs', 'back']
            masses = [1, 0.21, 0.55, 0.06, 0.06, 0.12]
            works = db.sum_filtered_sorted_rows(table='approaches', cells=cells, sql2=f' AND date > "{week_ago}"',
                                                tuple_=True, fetch='all', user_id=user_id)[0]
            logger.debug(f'{works=}')
            works = list(map(truediv, works, masses))
            cells = dict(zip(cells, works))
            min_cell = min(cells, key=cells.get)
            logger.debug(f'{min_cell=}')
            #  3. Находим упражнения на нужную мышечную группу, с загрузкой > 0.2. Выбираем то, которое реже всего
            #  встречалось в истории тренировок за последний месяц и отсутствует в постоянном и временном чёрных списках.
            muscle_names = {'arms': 'Руки', 'legs': 'Ноги', 'chest': 'Грудь', 'abs': 'Живот', 'back': 'Спина'}
            exercises = db.select_filtered_sorted_rows(table='exercises_muscles', fetch='all',
                                                       sql2=f' AND load > 0.2 ORDER BY exercise_id ASC',
                                                       muscle_name=muscle_names[min_cell])
            logger.debug(f'exercises_muscles {exercises=}')
            exercises_voc = {}
            for exercise in exercises:
                exercises_voc[exercise['exercise_id']] = 0
            logger.debug(f'{exercises_voc=}')
            exercises = db.select_filtered_sorted_rows(table='approaches', fetch='all',
                                                       sql2=f' AND date > "{month_ago}" ORDER BY exercise_id ASC',
                                                       user_id=user_id)
            logger.debug(f'approaches {len(exercises)=}')
            for exercise in exercises:
                if exercise['exercise_id'] in exercises_voc:
                    exercises_voc[exercise['exercise_id']] += 1
            logger.debug(f'{black_list=}')
            blocked_exercises = db.select_rows(table='exercises_users', fetch='all', user_id=user_id, list=0)
            logger.debug(f'approaches {blocked_exercises=}')
            for exercise in blocked_exercises:
                if exercise['exercise_id'] not in black_list:
                    black_list.append(exercise['exercise_id'])
            logger.debug(f'{black_list=}')
            logger.debug(f'{exercises_voc=}')
            for ex in black_list:
                exercises_voc.pop(ex, '')
            if exercises_voc != {}:
                rare_exercise = min(exercises_voc, key=exercises_voc.get)
                logger.debug(f'{rare_exercise=}')
            #  4. Создаём тренировку с выбранным упражнением, для этого находим предыдущий воркаут с ним.
                workout = db.select_filtered_sorted_rows(table='approaches', fetch='one',
                                                         sql2=f' ORDER BY approach_id DESC',
                                                         user_id=user_id, exercise_id=rare_exercise)
                if workout:
                    workout_id = workout['workout_id']
                    logger.debug(f'{workout_id=}')
                    approaches = db.select_filtered_sorted_rows(table='approaches', fetch='all',
                                                                sql2=f' ORDER BY number ASC',
                                                                workout_id=workout_id)
                    logger.debug(f'{approaches=}')
                    old_wrkt = [Approach(rare_exercise, approach['dynamic'], False) if i in {0, 2, 3} else
                                Approach(rare_exercise, approach['dynamic'], True)
                                for i, approach in enumerate(approaches)]
                    logger.debug(f'{old_wrkt=}')
                    return generate_new_split_new(old_wrkt)
                else:
                    return generate_new_split_new(exercise_id=rare_exercise)
            else:
                # Если до этого ещё не было тренировок, то предлагается набор из самых простых упражнений на разные группы мышц,
                # так называемый входной тест: отжимания на коленях, гиперэкстензии, подъем ног, приседания, гусеница
                return [Approach(4, 1, True), Approach(12, 1, True), Approach(24, 1, True),
                        Approach(8, 1, True), Approach(27, 1, True)]
        else:
            logger.debug('no approaches no old_ex')
            # Если до этого ещё не было тренировок, то предлагается набор из самых простых упражнений на разные группы мышц,
            # так называемый входной тест: отжимания на коленях, гиперэкстензии, подъем ног, приседания, гусеница
            return [Approach(4, 1, True), Approach(12, 1, True), Approach(24, 1, True),
                    Approach(8, 1, True), Approach(27, 1, True)]


async def show_exercise(message, db, exercise_id, keyboard):
    exercise = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id)
    if exercise['file_id']:
        msg = await message.answer_animation(
            animation=exercise['file_id'],
            caption=f'{exercise["exercise_id"]}. {exercise["name"]}',
            reply_markup=keyboard)
    else:
        msg = await message.answer(text=f'{exercise["exercise_id"]}. {exercise["name"]}', reply_markup=keyboard)
    return msg


async def award_user(user_id, db: SQLiteDatabase):
    """
    Проверяем, был ли в последнем воркауте максимум повторений:
    - находим максимальное повторение в последнем воркауте
    - находим максимальное повторение во всех подходах всех воркаутов упражнения
    - сравниваем и выдаем ответ
    Проверяем, была ли в воркауте выполнена максимальная работа:
    - считаем работу в последнем воркауте
    - считаем работу во всех воркаутах
    - сравниваем и выдаем ответ
    :param user_id:
    :param db:
    :return:
    """

    # максимальный повтор упражнения в последнем воркауте
    last_max_approach = db.select_filtered_sorted_rows(table='approaches', sql2=' ORDER BY workout_id DESC, dynamic DESC',
                                                       fetch='one', user_id=user_id)
    exercise_id = last_max_approach['exercise_id']
    workout_id = last_max_approach['workout_id']
    # максимальный повтор упражнения во всех воркаутах, кроме последнего
    max_approach = db.select_filtered_sorted_rows(table='approaches',
                                                  sql2=f' AND workout_id <> {workout_id} ORDER BY dynamic DESC',
                                                  fetch='one', user_id=user_id,
                                                  exercise_id=exercise_id)
    if not max_approach:
        max_approach = {'dynamic': 0}
    # работа в последнем воркауте
    last_job = db.select_filtered_sorted_rows(table='workouts', sql2=' ORDER BY workout_id DESC',
                                              fetch='one', user_id=user_id)
    # максимальная работа среди всех воркаутов, кроме последнего
    max_job = db.select_filtered_sorted_rows(table='workouts', sql2=f' AND workout_id <> {workout_id} ORDER BY work DESC',
                                             fetch='one', user_id=user_id)
    if not max_job:
        max_job = {'work': 0}
    max_work = last_job['work'] > max_job['work']
    max_reps = last_max_approach['dynamic'] > max_approach['dynamic']
    logger.debug(f'{last_job["work"]=}')
    logger.debug(f'{max_job["work"]=}')
    logger.debug(f'{last_max_approach["dynamic"]=}')
    logger.debug(f'{max_approach["dynamic"]=}')
    return {'work': max_work, 'reps': exercise_id if max_reps else max_reps}


async def run_timer(data, db: SQLiteDatabase, message, bot):
    data['delete_list'].append(message.message_id)
    for message_id in data['delete_list']:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
    data['delete_list'] = []
    msg = await message.answer_animation(
        animation=db.select_rows(table='multimedia', fetch='one', name='timer')['file_id'],
        caption='Отдыхайте от 10 секунд до 5 минут...',
        reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await asyncio.sleep(2)
    msg = await message.answer(
        text=f'Выполните подход {data["approach"] + 1} из {data["new_workout"][data["approach"]][1]} повторений '
             f'и нажмите кнопку "Готово". Если вы сделали другое количество, напишите сколько.', reply_markup=ready)
    data['delete_list'].append(msg.message_id)
    return data


async def save_approach(data, db: SQLiteDatabase, message):
    logger.debug(f'{data["new_workout"]=}')
    logger.debug(f'{data["done_approaches"]=}')
    exercise_id = data['new_workout'][0][0]
    new_workout = data['new_workout'].pop(0)
    logger.debug(f'{new_workout=}')
    if message.text.isdigit():
        number = int(message.text)
    else:
        number = new_workout[1]
    if 'done_approaches' in data:
        data['done_approaches'].append(Approach(new_workout[0], number, new_workout[2]))
        logger.debug(f'{data["done_approaches"]=}')
    else:
        data['done_approaches'] = [Approach(new_workout[0], number, new_workout[2])]
    approach = len(data['done_approaches'])
    logger.debug(f'{approach=}')
    user = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
    work = (number * int(user['weight']) / 100
            * db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id)['work'])
    arms_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=0)['load']
    legs_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=1)['load']
    chest_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=2)['load']
    abs_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=3)['load']
    back_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=4)['load']
    db.add_approach(workout_id=data['workout_number'], user_id=user['user_id'], exercise_id=exercise_id,
                    number=approach, dynamic=number, static=0, date=datetime.utcnow().isoformat(),
                    work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs_=abs_work, back=back_work)
    if len(data['new_workout']) == 0:
        work = (sum([x[1] for x in data['done_approaches']]) * int(user['weight']) / 100
                * db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id)['work'])
        arms_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=0)['load']
        legs_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=1)['load']
        chest_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=2)['load']
        abs_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=3)['load']
        back_work = work * db.select_rows('exercises_muscles', 'one', exercise_id=exercise_id, muscle_id=4)['load']
        db.add_workout(workout_id=data['workout_number'], user_id=user['user_id'], date=datetime.utcnow().isoformat(),
                       exercise_id=exercise_id, approaches=approach,
                       work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs_=abs_work, back=back_work)
    return data


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
