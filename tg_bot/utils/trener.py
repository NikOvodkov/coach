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
        workout = await generate_solo_workout(db, user_id, old_ex)
    # если нет, то будем собирать из разных упражнений:
    else:
        workout = await generate_full_workout(db, user_id, black_list)
    return workout


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
    logger.debug(f'enter_award_user')
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
    logger.debug(f'award_user before last db operation {workout_id=}')
    max_job = db.select_filtered_sorted_rows(table='workouts', sql2=f' AND workout_id <> {workout_id} ORDER BY work DESC',
                                             fetch='one', user_id=user_id)
    logger.debug(f'award_user db data get')
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
    exercise = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id)
    work = (number * int(user['weight']) / 100 * exercise['work'])
    arms_work = work * exercise['arms']
    legs_work = work * exercise['legs']
    chest_work = work * exercise['chest']
    abs_work = work * exercise['abs']
    back_work = work * exercise['back']
    logger.debug(f'{data=}')
    if 'workout_number' not in data:
        data['workout_number'] = 0
    if approach == 1:
        db.add_workout(user_id=user['user_id'], date=datetime.utcnow().isoformat(), exercise_id=exercise_id, approaches=approach)
        data['workout_number'] = db.select_filtered_sorted_rows(table='workouts', fetch='one',
                                                                sql2=f' ORDER BY workout_id DESC',
                                                                user_id=user['user_id'])['workout_id']
    db.add_approach(workout_id=data['workout_number'], user_id=user['user_id'], exercise_id=exercise_id,
                    number=approach, dynamic=number, static=0, date=datetime.utcnow().isoformat(),
                    work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs_=abs_work, back=back_work)
    if len(data['new_workout']) == 0:
        work = (sum([x[1] for x in data['done_approaches']]) * int(user['weight']) / 100 * exercise['work'])
        arms_work = work * exercise['arms']
        legs_work = work * exercise['legs']
        chest_work = work * exercise['chest']
        abs_work = work * exercise['abs']
        back_work = work * exercise['back']
        db.update_cells(table='workouts',
                        cells={'date': datetime.utcnow().isoformat(), 'approaches': approach, 'work': work,
                               'arms': arms_work, 'legs': legs_work, 'chest': chest_work, 'abs_': abs_work, 'back': back_work},
                        workout_id=data['workout_number'])
    return data


async def fill_exercises_users(user_id: int, db: SQLiteDatabase):
    logger.debug(f'enter fill_exercises_users')
    exercises = db.select_table(table='exercises')
    logger.debug(f'fill_exercises_users {exercises=}')
    for exercise in exercises:
        exercise_user = db.select_rows(table='exercises_users', fetch='one',
                                       user_id=user_id, exercise_id=exercise['exercise_id'])
        if not exercise_user:
            db.add_exercise_user(user_id=user_id, exercise_id=exercise['exercise_id'])
    return


async def count_exercises_levels(db: SQLiteDatabase):
    """
    Функция рассчитывает уровни сложности упражнений на основе количества повторений в подходах пользователей.
    Запускается вручную администратором.
    Текущая формула расчёта:
    а) Пробегаемся по таблице подходов, собираем из неё таблицу
       {exercise_id: [{user_id: max_rep, ex_reps, all_reps}, {}, {}], ... }.
    б) Сложность для пользователя рассчитываем, как 1/max_rep, и умножаем на участие каждой группы мышц, т.е. 0.1 * 1/Й и т.д.
    в) На основе отфильтрованных пользователей (более 25 подходов к упражнению, более 100 подходов всего)
       рассчитываем сложность упражнений и записываем в базу упражнений
    :param data:
    :param db:
    :param message:
    :return:
    """
    approaches = db.select_table(table='approaches')
    # собираем словарь из таблицы подходов, ключ - кортеж (exercise_id, user_id)
    # значение - список [макс кол-во повторений, общее количество подходов в этом упражнении, сложность=1/повторения]
    exercises_users = {}
    for approach in approaches:
        ind = (approach['exercise_id'], approach['user_id'])
        if ind in exercises_users:
            exercises_users[ind] = [max(exercises_users[ind][0], approach['dynamic']),
                                    exercises_users[ind][1] + 1,
                                    1 / max(exercises_users[ind][0], approach['dynamic'])]
        else:
            exercises_users[ind] = [approach['dynamic'], 1, 1 / approach['dynamic']]
    # собираем словарь пользователей, ключ - user_id
    # значение - общее количество подходов во всех упражнениях
    users = {}
    for ind in exercises_users:
        if ind[1] in users:
            users[ind[1]] += exercises_users[ind][1]
        else:
            users[ind[1]] = exercises_users[ind][1]
        exercise = db.select_rows('exercises', fetch='one', exercise_id=ind[0])
        db.update_cells(table='exercises_users',
                        cells={'arms': exercise['arms'] * exercises_users[ind][2],
                               'legs': exercise['legs'] * exercises_users[ind][2],
                               'chest': exercise['chest'] * exercises_users[ind][2],
                               'abs': exercise['abs'] * exercises_users[ind][2],
                               'back': exercise['back'] * exercises_users[ind][2]},
                        user_id=ind[1], exercise_id=ind[0])
    # собираем словарь упражнений, ключ - exercise_id
    # значение - список [сумма сложностей по всем пользователям, количество пользователей]
    exercises = {}
    for ind in exercises_users:
        if (users[ind[1]] > 100) and (exercises_users[ind][1] > 10):
            if ind[0] in exercises:
                exercises[ind[0]] = [exercises[ind[0]][0] + exercises_users[ind][2], exercises[ind[0]][1] + 1]
            else:
                exercises[ind[0]] = [exercises_users[ind][2], 1]
    # в этом цикле рассчитываем сложность упражнений делением суммы сложностей на количество пользователей
    for exercise_id in exercises:
        exercise = db.select_rows('exercises', fetch='one', exercise_id=exercise_id)
        k = exercises[exercise_id][0] / exercises[exercise_id][1]
        db.update_cells(table='exercises',
                        cells={'level_arms': exercise['arms'] * k,
                               'level_legs': exercise['legs'] * k,
                               'level_chest': exercise['chest'] * k,
                               'level_abs': exercise['abs'] * k,
                               'level_back': exercise['back'] * k},
                        exercise_id=exercise_id)
    logger.debug(f'{exercises_users=}')
    logger.debug(f'{users=}')
    logger.debug(f'{exercises=} {len(exercises)=}')
    return


async def generate_solo_workout(db: SQLiteDatabase, user_id: int, exercise_id: int):
    logger.debug(f'generate_solo_workout {exercise_id=}')
    approaches = db.select_filtered_sorted_rows(table='approaches', fetch='one', sql2=f' ORDER BY approach_id DESC',
                                                user_id=user_id, exercise_id=exercise_id)
    if (approaches and approaches['date']
            and (datetime.utcnow() - datetime.fromisoformat(approaches['date'])) < timedelta(days=29)):
        approaches = db.select_filtered_sorted_rows(table='approaches', fetch='all', sql2=f' ORDER BY approach_id ASC',
                                                    workout_id=approaches['workout_id'], exercise_id=exercise_id)
        logger.debug('generate_solo_workout approaches')
        old_wrkt = [Approach(exercise_id, approach['dynamic'], False) if i in {0, 2, 3} else
                    Approach(exercise_id, approach['dynamic'], True)
                    for i, approach in enumerate(approaches)]
        logger.debug(f'{old_wrkt=}')
        return generate_new_split_new(old_wrkt)
    else:
        logger.debug('generate_solo_workout no approaches')
        return [Approach(exercise_id, 1, False), Approach(exercise_id, 1, False), Approach(exercise_id, 1, False),
                Approach(exercise_id, 1, False), Approach(exercise_id, 1, True)]


async def generate_full_workout(db: SQLiteDatabase, user_id: int, black_list: list = None):
    logger.debug('generate_full_workout')
    # Для начала выясним когда была последняя тренировка и была ли она вообще:
    last_approach = db.select_filtered_sorted_rows(table='approaches', fetch='one',
                                                   sql2=f' ORDER BY workout_id DESC',
                                                   user_id=user_id)
    if last_approach:
        break_time = datetime.utcnow() - datetime.fromisoformat(last_approach['date'])
        # Если перерыв 29 дней и более, начинаем как с нуля, с тестов типа 1 1 1 1 1.

        # Если перерыв менее 7 дней, запускаем стандартного автотренера.
    else:
        # Если до этого ещё не было тренировок, то предлагается набор из самых простых упражнений на разные группы мышц,
        # так называемый входной тест: отжимания на коленях, гиперэкстензии, подъем ног, приседания, гусеница;
        # пока режим тренировки с разными упражнениями не реализован, ограничимся отжиманиями на коленях.
        # return [Approach(4, 1, True), Approach(12, 1, True), Approach(24, 1, True),
        #         Approach(8, 1, True), Approach(27, 1, True)]
        return [Approach(4, 1, True), Approach(4, 1, True), Approach(4, 1, True),
                Approach(4, 1, True), Approach(4, 1, True)]
    # Если перерыв 7-28 дней, сгенерируем соло тренировку на базе последнего упражнения.
    if break_time > timedelta(days=7):
        solo_workout = await generate_solo_workout(db, user_id, last_approach['exercise_id'])
        return solo_workout
    else:
        logger.debug('approaches no old_ex')
        #  1. Находим в истории за последний месяц день с максимальной работой,
        #  получаем норму работы на новую тренировку.
        month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        last_month_workouts = db.select_filtered_sorted_rows(table='workouts', sql2=f' AND date > "{month_ago}" ORDER BY work DESC',
                                                             fetch='all', user_id=user_id)
        dates = {}
        for workout in last_month_workouts:
            date = datetime.fromisoformat(workout['date']).date()
            if workout['work'] is not None:
                if date in dates:
                    dates[date] += workout['work']
                else:
                    dates[date] = workout['work']
        max_work = max(dates, key=dates.get)
        #  2. Суммируем относительную (работа/кг мышцы) недельную работу по каждой мышце,
        #      выясняем у какой меньше всего, будем прорабатывать её.
        cells = ['arms', 'legs', 'chest', 'abs', 'back']
        # cells = ['work', 'arms', 'legs', 'chest', 'abs', 'back']
        # masses = [1, 0.21, 0.55, 0.06, 0.06, 0.12]
        masses = [0.21, 0.55, 0.06, 0.06, 0.12]
        works = db.sum_filtered_sorted_rows(table='approaches', cells=cells, sql2=f' AND date > "{week_ago}"',
                                            tuple_=True, fetch='one', user_id=user_id)
        works = list(map(truediv, works, masses))
        cells = dict(zip(cells, works))
        min_cell = min(cells, key=cells.get)
        logger.warning(f'last week works {user_id=} {cells=} {min_cell=}')
        #  3. Берём все упражнения и сортируем сначала в порядке убывания нагрузки на нужную группу,
        #  затем в порядке частоты встречаемости за последний месяц. Затем удаляем те, что в ЧС.
        #  Если min_cell = None, то повторяем последний воркаут
        exercises = (db.select_rows(table='exercises', fetch='all', type=1) +
                     db.select_rows(table='exercises', fetch='all', type=2))
        exercises_voc = {}
        for exercise in exercises:
            exercises_voc[exercise['exercise_id']] = [0, exercise[min_cell]]
        exercises = db.select_filtered_sorted_rows(table='approaches', fetch='all',
                                                   sql2=f' AND date > "{month_ago}"',
                                                   user_id=user_id)
        favourite_exercises = db.select_rows(table='exercises_users', fetch='all', user_id=user_id, list=1)
        favourite_exercises = [ex['exercise_id'] for ex in favourite_exercises]
        logger.debug(f'{favourite_exercises=}')
        blocked_exercises = db.select_rows(table='exercises_users', fetch='all', user_id=user_id, list=0)
        for exercise in exercises:
            if exercise['exercise_id'] in favourite_exercises:
                exercises_voc[exercise['exercise_id']][0] -= 0.5
            else:
                exercises_voc[exercise['exercise_id']][0] -= 1
        logger.warning(f'last months exercises {exercises_voc=}')
        if not black_list:
            black_list = []
        for exercise in blocked_exercises:
            if exercise['exercise_id'] not in black_list:
                black_list.append(exercise['exercise_id'])
        logger.debug(f'{black_list=}')
        for ex in black_list:
            if len(exercises_voc) > 1:
                exercises_voc.pop(ex, '')
        rare_exercise = max(exercises_voc, key=exercises_voc.get)
        logger.warning(f'{rare_exercise=}')
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
