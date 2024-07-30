import asyncio
import math
import time
from datetime import datetime, timedelta
from operator import truediv
from typing import NamedTuple

from aiogram import Bot
from aiogram.types import ReplyKeyboardRemove

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.keyboards.trener import ready, ready_end, ready_change
from tg_bot.services.ufuncs import clear_delete_list


class Approach(NamedTuple):
    exercise: int = None
    repetitions: int = None
    max: bool = None


def generate_triple(old_max: int = 1, old_sum: int = 3, exercise_id: int = 4):  # 2 4 3
    one = max(1, round(old_max / 2))   # 2 2
    two = old_max                      # 4 5
    three = old_sum - two - one + 1    # 4 5
    while (three > two - 1) or ( one > round(two * 0.6)):
        if three > two - 1:                #
            three -= 1                     # 4 3
            one += 1                       # 2 3
            if one > round(two * 0.6):     #
                one -= 1                   # 3 2
                two += 1                   # 4 5
    if three >= two:
        logger.warning(f'3>2 {exercise_id=}')
    return [[exercise_id, one, False],
            [exercise_id, two, True],
            [exercise_id, three, True]]


async def generate_short_split(db, user_id, exercise_id):
    # создаём список с последним воркаутом, находим в нём максимум и общую сумму повторений
    # на основе этих данных строим трипл
    logger.debug(f'enter generate_short_split')
    last_approach = db.select_filtered_sorted_rows(table='approaches', fetch='one', sql2=f' ORDER BY approach_id DESC',
                                                   user_id=user_id, exercise_id=exercise_id)
    if last_approach:
        workout_id = last_approach['workout_id']
        last_approaches = db.select_filtered_sorted_rows(table='approaches', fetch='all', sql2=f' ORDER BY approach_id ASC',
                                                         user_id=user_id, exercise_id=exercise_id, workout_id=workout_id)
        triple_max = 0
        triple_sum = 0
        for approach in last_approaches:
            triple_sum += approach['dynamic']
            if triple_max < approach['dynamic']:
                triple_max = approach['dynamic']
        logger.debug(f'generate_triple {triple_max=} {triple_sum=}')
        triple = generate_triple(old_max=triple_max, exercise_id=exercise_id, old_sum=triple_sum)
    else:
        triple = generate_triple(old_max=1, exercise_id=exercise_id, old_sum=3)
    return triple


async def show_exercise(message, db, exercise_id, keyboard, muscle: str = None):
    exercise = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id)
    if muscle:
        caption = f'{exercise["exercise_id"]}. {exercise["name"]}, проработаем {muscle}.'
    else:
        caption = f'{exercise["exercise_id"]}. {exercise["name"]}'
    if exercise['file_id']:
        msg = await message.answer_animation(
            animation=exercise['file_id'],
            caption=caption,
            reply_markup=keyboard)
    else:
        msg = await message.answer(text=f'{exercise["exercise_id"]}. {exercise["name"]}', reply_markup=keyboard)
    return msg


async def show_approach(data, message, db, keyboard, bot: Bot):
    exercise = db.select_rows(table='exercises', fetch='one', exercise_id=data["new_workout"][0][0])
    if (("done_approaches" in data and data["done_approaches"][-1][0] != data["new_workout"][0][0])
            or "done_approaches" not in data):
        data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
        if exercise['file_id']:
            msg = await message.answer_animation(
                animation=exercise['file_id'],
                caption=f'{exercise["exercise_id"]}. {exercise["name"]}',
                reply_markup=keyboard)
        else:
            msg = await message.answer(text=f'{exercise["exercise_id"]}. {exercise["name"]}', reply_markup=keyboard)
    if "done_approaches" in data:
        data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
        msg = await message.answer(
            text=f'Сделано: {", ".join([str(app[0]) + "-" + str(app[1]) for app in data["done_approaches"]])} '
                 f'Выполните повторов: {data["new_workout"][0][1]}'
                 f'{"+" if data["new_workout"][0][2] else ""}. '
                 f'Нажмите "Продолжить" или напишите сколько сделали:', reply_markup=ready_end)
    else:
        msg = await message.answer(
            text=f'Выполните повторов: {data["new_workout"][0][1]}'
                 f'{"+" if data["new_workout"][0][2] else ""}. '
                 f'Нажмите "Продолжить" или напишите сколько сделали:', reply_markup=ready_end)
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

    # максимальный повтор упражнения за последний день
    logger.debug(f'enter_award_user')
    today = datetime.today().isoformat()[:10]
    today_approaches = db.select_filtered_sorted_rows(table='approaches',
                                                      sql2=f' AND date>"{today}"',
                                                      fetch='all', user_id=user_id)
    exercises = {}
    max_reps = {}
    for approach in today_approaches:
        if approach['exercise_id'] in exercises:
            if approach['dynamic'] > exercises[approach['exercise_id']]['dynamic']:
                exercises[approach['exercise_id']] = {'dynamic': approach['dynamic'], 'approach_id': approach['approach_id']}
        else:
            exercises[approach['exercise_id']] = {'dynamic': approach['dynamic'], 'approach_id': approach['approach_id']}
    for exercise_id in exercises:
        # максимальный повтор упражнения во всех воркаутах, кроме последнего
        max_approach = db.select_filtered_sorted_rows(table='approaches',
                                                      sql2=f' AND date<"{today}" ORDER BY dynamic DESC',
                                                      fetch='one', user_id=user_id,
                                                      exercise_id=exercise_id)
        if not max_approach:
            max_approach = {'dynamic': 0}
        max_reps[exercise_id] = exercises[exercise_id]['dynamic'] > max_approach['dynamic']
    max_reps_list = []
    for mr in max_reps:
        if max_reps[mr]:
            max_reps_list.append(str(mr))
    max_reps = max_reps_list if len(max_reps_list) > 0 else False
    # работа в последнем воркауте
    last_job = db.select_filtered_sorted_rows(table='workouts', sql2=' ORDER BY workout_id DESC',
                                              fetch='one', user_id=user_id)
    # максимальная работа среди всех воркаутов, кроме последнего
    max_job = db.select_filtered_sorted_rows(table='workouts',
                                             sql2=f' AND workout_id <> {last_job["workout_id"]} ORDER BY work DESC',
                                             fetch='one', user_id=user_id)
    logger.debug(f'award_user db data get')
    if not max_job:
        max_job = {'work': 0}
    max_work = last_job['work'] > max_job['work']
    logger.debug(f'{last_job["work"]=}')
    logger.debug(f'{max_job["work"]=}')
    logger.debug(f'{max_reps=}')
    return {'work': max_work, 'reps': max_reps}


async def run_warmup(data, db: SQLiteDatabase, message):
    logger.debug('enter run_warmup')
    users_exercises = db.select_rows(table='exercises_users', fetch='one', user_id=message.from_user.id, type=5, list=1)
    if users_exercises:
        video = db.select_rows(table='exercises', fetch='one', exercise_id=users_exercises['exercise_id'])['file_id']
    else:
        video = db.select_filtered_sorted_rows(table='exercises', sql2=' ORDER BY exercise_id ASC',
                                               fetch='one', type=5)['file_id']
    msg = await message.answer_video(
        video=video,
        caption='Выполните разминку...',
        reply_markup=ready)
    if 'delete_list' in data:
        data['delete_list'].append(msg.message_id)
    else:
        data['delete_list'] = [msg.message_id]
    return data


async def run_timer(data, db: SQLiteDatabase, message):
    users_exercises = db.select_rows(table='exercises_users', fetch='one', user_id=message.from_user.id, type=8, list=1)
    logger.debug(f'{users_exercises=}')
    if users_exercises:
        animation = db.select_rows(table='exercises', fetch='one', exercise_id=users_exercises['exercise_id'])['file_id']
    else:
        animation = db.select_filtered_sorted_rows(table='exercises', sql2=' ORDER BY exercise_id ASC',
                                                   fetch='one', type=8)['file_id']
    logger.debug(f'{animation=}')
    msg = await message.answer_animation(
        animation=animation,
        caption='Отдыхайте от 10 секунд до 5 минут...',
        reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await asyncio.sleep(5)
    return data


async def save_approach(data, db: SQLiteDatabase, message):
    exercise_id = data['new_workout'][0][0]
    new_workout = data['new_workout'].pop(0)
    logger.debug(f'{new_workout=}')
    if message.text.isdigit():
        number = int(message.text)
    else:
        number = new_workout[1]
    if 'done_approaches' in data:
        data['done_approaches'].append([new_workout[0], number, new_workout[2]])
        logger.debug(f'{data["done_approaches"]=}')
    else:
        data['done_approaches'] = [[new_workout[0], number, new_workout[2]]]
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
            db.add_exercise_user(user_id=user_id, exercise_id=exercise['exercise_id'], type_=exercise['type'])
    return


async def is_good_level(exercise_id: int, user_id: int, db: SQLiteDatabase):
    e_r = db.select_rows(table='exercises_users', fetch='one', user_id=user_id, exercise_id=exercise_id)
    levels = [e_r['arms'], e_r['legs'], e_r['chest'], e_r['abs'], e_r['back']]
    if None in levels:
        return False
    else:
        return 0.01 <= max(levels) <= 0.2


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
    г) заполнить таблицу exercises_users личными рекордами где они есть, из таблицы exercises где их нет
    д) При окончании тренировки заполнить таблицу exercises_users по упражнению текущим упражнением
    :param data:
    :param db:
    :param message:
    :return:
    """
    exercises_users = db.select_table('exercises_users')
    for exercise_user in exercises_users:
        exercise = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_user['exercise_id'])
        db.update_cells(table='exercises_users', cells={'type': exercise['type']},
                        user_id=exercise_user['user_id'], exercise_id=exercise_user['exercise_id'])

    approaches = db.select_table(table='approaches')
    logger.debug(f'enter count_exercises_levels')
    # собираем словарь из таблицы подходов, ключ - кортеж (exercise_id, user_id)
    # значение - список [макс кол-во повторений, общее количество подходов в этом упражнении, сложность=1/повторения]
    exercises_users = {}
    for approach in approaches:
        ind = (approach['exercise_id'], approach['user_id'])
        if ind in exercises_users:
            # exercises_users[ind] = [max(exercises_users[ind][0], approach['dynamic']),
            #                         exercises_users[ind][1] + 1,
            #                         1 / max(exercises_users[ind][0], approach['dynamic'])]
            exercises_users[ind] = {'dynamic': max(exercises_users[ind]['dynamic'], approach['dynamic']),
                                    'approaches': exercises_users[ind]['approaches'] + 1,
                                    'level': 1 / max(exercises_users[ind]['dynamic'], approach['dynamic'])}
        else:
            # exercises_users[ind] = [approach['dynamic'], 1, 1 / approach['dynamic']]
            exercises_users[ind] = {'dynamic': approach['dynamic'], 'approaches': 1, 'level': 1 / approach['dynamic']}
    # собираем словарь пользователей, ключ - user_id
    # значение - общее количество подходов во всех упражнениях
    logger.debug(f'approaches counted count_exercises_levels')
    users = {}
    for ind in exercises_users:
        if ind[1] in users:
            users[ind[1]] += exercises_users[ind]['approaches']
        else:
            users[ind[1]] = exercises_users[ind]['approaches']
        exercise = db.select_rows('exercises', fetch='one', exercise_id=ind[0])
        db.update_cells(table='exercises_users',
                        cells={'arms': exercise['arms'] * exercises_users[ind]['level'],
                               'legs': exercise['legs'] * exercises_users[ind]['level'],
                               'chest': exercise['chest'] * exercises_users[ind]['level'],
                               'abs': exercise['abs'] * exercises_users[ind]['level'],
                               'back': exercise['back'] * exercises_users[ind]['level'],
                               'type': exercise['type']},
                        user_id=ind[1], exercise_id=ind[0])
    # собираем словарь упражнений, ключ - exercise_id
    # значение - список [сумма сложностей по всем пользователям, количество пользователей]
    logger.debug(f'exercises_users counted count_exercises_levels')
    exercises = {}
    for ind in exercises_users:
        if (users[ind[1]] > 100) and (exercises_users[ind]['approaches'] > 10):
            if ind[0] in exercises:
                # exercises[ind[0]] = [exercises[ind[0]][0] + exercises_users[ind]['level'], exercises[ind[0]][1] + 1]
                exercises[ind[0]] = {'sum_level': exercises[ind[0]]['sum_level'] + exercises_users[ind]['level'],
                                     'sum_user': exercises[ind[0]]['sum_user'] + 1}
            else:
                # exercises[ind[0]] = [exercises_users[ind]['level'], 1]
                exercises[ind[0]] = {'sum_level': exercises_users[ind]['level'], 'sum_user': 1}
    # в этом цикле рассчитываем сложность упражнений делением суммы сложностей на количество пользователей
    for exercise_id in exercises:
        exercise = db.select_rows('exercises', fetch='one', exercise_id=exercise_id)
        k = exercises[exercise_id]['sum_level'] / exercises[exercise_id]['sum_user']
        db.update_cells(table='exercises',
                        cells={'level_arms': exercise['arms'] * k,
                               'level_legs': exercise['legs'] * k,
                               'level_chest': exercise['chest'] * k,
                               'level_abs': exercise['abs'] * k,
                               'level_back': exercise['back'] * k},
                        exercise_id=exercise_id)
    # в этом цикле заполняем сложности упражнений в таблице exercises_users (если они пустые) значениями
    # из таблицы exercises
    logger.debug(f'exercises counted count_exercises_levels')
    exercises_users = db.select_table('exercises_users')
    exercises = db.select_table('exercises')
    cells = ['arms', 'legs', 'chest', 'abs', 'back']
    for exercise_user in exercises_users:
        for work in cells:
            if exercise_user[work] is not None:
                exercise_work = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_user['exercise_id'])
                db.update_cells(table='exercises_users', cells={work: exercise_work['level_' + work]},
                                user_id=exercise_user['user_id'], exercise_id=exercise_user['exercise_id'])
    logger.debug(f'{exercises_users=}')
    logger.debug(f'{users=}')
    logger.debug(f'{len(exercises)=}')
    return


async def generate_full_workout(db: SQLiteDatabase, user_id: int, black_list: list = None, old_ex: int = None):
    logger.debug('generate_full_workout')
    # Для начала выясним когда была последняя тренировка и была ли она вообще:
    last_approach = db.select_filtered_sorted_rows(table='approaches', fetch='one',
                                                   sql2=f' ORDER BY workout_id DESC',
                                                   user_id=user_id)
    month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    if last_approach:
        break_time = datetime.utcnow() - datetime.fromisoformat(last_approach['date'])
    else:
        break_time = timedelta(days=60)
    if break_time < timedelta(days=8):
        #  1. Находим в истории за последний месяц день с максимальной работой,
        #  получаем норму работы на новую тренировку.
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
        masses = [0.22, 0.51, 0.07, 0.07, 0.13]
        works = db.sum_filtered_sorted_rows(table='approaches', cells=cells, sql2=f' AND date > "{week_ago}"',
                                            tuple_=True, fetch='one', user_id=user_id)
        works = list(map(truediv, works, masses))
        cells = dict(zip(cells, works))
        min_cell = min(cells, key=cells.get)
    else:
        max_work = None
        min_cell = None
    #  3. Берём все упражнения и сортируем сначала в порядке убывания нагрузки на нужную группу,
    #  затем в порядке частоты встречаемости за последний месяц. Затем удаляем те, что в ЧС.
    #  Если min_cell = None, то повторяем последний воркаут
    exercises = (db.select_rows(table='exercises', fetch='all', type=1) +
                 db.select_rows(table='exercises', fetch='all', type=2))
    # ключ - exercise_id, значение -{частота встречаемости упражнения, процент использования нужных мышц, сложность}
    exercises_voc = {}
    cells = ['arms', 'legs', 'chest', 'abs', 'back']
    for exercise in exercises:
        muscles = {}
        exercises_users = db.select_rows(table='exercises_users', fetch='one',
                                         exercise_id=exercise['exercise_id'], user_id=user_id)
        master_level = 0
        for cell in cells:
            if exercises_users[cell] is not None and exercises_users[cell] > master_level:
                master_level = exercises_users[cell]
            muscles[cell] = {'load': exercise[cell], 'level': exercises_users[cell]}
        exercises_voc[exercise['exercise_id']] = {'frequency': 0, 'muscles': muscles, 'master_level': master_level}
    # for exercise in exercises:
    #     level = db.select_rows(table='exercises_users', fetch='one',
    #                            exercise_id=exercise['exercise_id'], user_id=user_id)[min_cell]
    #     exercises_voc[exercise['exercise_id']] = {'frequency': 0, 'muscle_load': exercise[min_cell], 'level': level}
    exercises = db.select_filtered_sorted_rows(table='approaches', fetch='all',
                                               sql2=f' AND date > "{month_ago}"',
                                               user_id=user_id)
    favourite_exercises = db.select_rows(table='exercises_users', fetch='all', user_id=user_id, list=1)
    favourite_exercises = [ex['exercise_id'] for ex in favourite_exercises]
    logger.debug(f'{favourite_exercises=}')
    blocked_exercises = db.select_rows(table='exercises_users', fetch='all', user_id=user_id, list=0)
    for exercise in exercises:
        if exercise['exercise_id'] in favourite_exercises:
            exercises_voc[exercise['exercise_id']]['frequency'] -= 0.5
        elif await is_good_level(exercise['exercise_id'], user_id, db):
            exercises_voc[exercise['exercise_id']]['frequency'] -= 1
        else:
            exercises_voc[exercise['exercise_id']]['frequency'] -= 2
    logger.warning(f'last months exercises {exercises_voc=}')
    if not black_list:
        black_list = []
    for exercise in blocked_exercises:
        if exercise['exercise_id'] not in black_list and exercise['exercise_id'] != old_ex:
            black_list.append(exercise['exercise_id'])
    logger.debug(f'{black_list=}')
    for ex in black_list:
        if len(exercises_voc) > 1 and ex != old_ex:
            exercises_voc.pop(ex, '')
    logger.debug(f'{old_ex=}')
    if old_ex is not None:
        exercises_voc[old_ex] = {'frequency': 1, 'muscles': exercises_voc[old_ex]['muscles'], 'master_level': 1}
        logger.debug(f'before sorted_workout {exercises_voc[old_ex]=}')
    sorted_workout = await get_workout_dic(exercises_voc, min_cell, old_ex)
    logger.warning(f'{sorted_workout=}')
    #  4. Создаём тренировку - список триплов упражнений из массива.
    wrkt = []
    for voc in sorted_workout:
        wrkt_el = await generate_short_split(db=db, user_id=user_id, exercise_id=sorted_workout[voc]['exercise_id'])
        wrkt += wrkt_el
    return wrkt, min_cell


async def get_workout_dic(voc, muscle: str = None, old_ex: int = None):
    """
    Если мышца не выбрана:
    1. Выбираем не менее 5 упражнений с максимальным frequency.
    2. Сортируем их по убыванию сложности. Сложность упражнения вычисляем, как максимальную сложность по всем мышцам.
    3. Остальные упражнения из базы сортируем по убыванию frequency.
    Если мышца выбрана:
    1. Выбираем все упражнения с muscle_load>=0.2
    2. Выбираем из них 5 упражнений с максимальным frequency.
    3. Сортируем 5 оставшихся упражнений по убыванию сложности.
    4. Остальные упражнения из базы сортируем по убыванию frequency.

    :param old_ex:
    :param muscle:
    :param voc: словарь всех допущенных до тренировки упражнений
    :return:
    """
    logger.debug(f'get_workout_dic {muscle=} {voc=}')
    if muscle:
        # выбираем упражнения с muscle_load>=0.2
        voc2 = {}
        for v in voc:
            if v == old_ex:
                voc2[v] = voc[v]
            elif voc[v]['muscles'][muscle]['load'] >= 0.2:
                voc[v]['master_level'] = voc[v]['muscles'][muscle]['level']
                if voc[v]['master_level'] is None:
                    voc[v]['master_level'] = 0
                voc2[v] = voc[v]
    else:
        voc2 = voc
    voc3 = [[voc2[d]['frequency'], voc2[d]['master_level'], voc2[d]['muscles'], d] for d in voc2]
    voc3 = sorted(voc3, key=lambda a: a[0], reverse=True)
    logger.debug(f'SEREDINA get_workout_dic {voc3=}')
    # выбираем не менее 5 упражнений с максимальным frequency
    voc2 = []
    for v in voc3:
        if len(voc2) < 5:
            voc2.append(v)
        elif voc2[-1][0] == v[0]:
            voc2.append(v)
        logger.debug(f'{voc2=}')
    # сортируем выбранные упражнения по убыванию сложности
    voc3 = sorted(voc2, key=lambda a: a[1], reverse=True)
    # теперь нужно добавить остальные упражнения из базы в порядке убывания frequency
    # для этого создаём список всех упражнений
    voc4 = [[voc[d]['frequency'], voc[d]['master_level'], voc[d]['muscles'], d] for d in voc]
    # удаляем повторяющиеся в другом списке
    for v in voc4:
        if v in voc3:
            logger.debug(f'remove from voc: {v=}')
            voc4.remove(v)
    # сортируем по убыванию frequency
    voc4 = sorted(voc4, key=lambda a: a[0], reverse=True)
    # объединяем списки
    voc3 = voc3 + voc4
    voc3 = {i: {'exercise_id': v[3], 'frequency': v[0], 'muscles': v[2], 'master_level': v[1]} for i, v in enumerate(voc3)}
    logger.debug(f'get_workout_dic end {voc3=}')
    return voc3


if __name__ == '__main__':
    # user_split = Split(*map(int, input('Input split: ').split()))
    # print(*user_split)
    # while True:
    #     time.sleep(1)
    #     user_split = generate_new_split(user_split)
    #     print(*user_split)

    # user_split = input('Input split: ')
    # while True:
    #     time.sleep(1)
    #     user_split = generate_new_split(user_split)
    #     print(user_split)

    print()
    # asyncio.run(generate_new_split([1,1,0,0,1]))
