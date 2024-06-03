import asyncio
import os
from datetime import timedelta, datetime
from pathlib import Path

import dateutil
from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, URLInputFile, InputMediaVideo, InputFile, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hide_link
from aiogram.utils.media_group import MediaGroupBuilder

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.db import MyUserDbFilter
from tg_bot.keyboards.trener import yesno, ready
from tg_bot.lexicon.life_calendar import LEXICON_RU
from tg_bot.states.trener import FSMTrener
from tg_bot.utils.life_calendar import generate_image_calendar
from tg_bot.states.life_calendar import FSMLifeCalendar
from tg_bot.utils.trener import generate_new_split, Split

# Инициализируем роутер уровня модуля
router = Router()


async def clear_delete_list(delete_list, bot, user_id):
    for message_id in set(delete_list):
        await bot.delete_message(chat_id=user_id, message_id=message_id)
    return []


async def auto_choose_exercise(user, db, black_list) -> int:
    """
    1. Находим в истории тренировку с максимальной работой за месяц, добавляем 10%, получаем норму работы на новую тренировку.
    2. Суммируем недельную работу по каждой мышце, выясняем у какой меньше всего, будем прорабатывать её.
    3. Находим упражнения на нужную мышечную группу, с загрузкой 0.3 и выше. Выбираем то, которое реже всего встречалось в
    истории тренировок.
    4. Проводим тренировку с найденным упражнением.
    5. Если осталась часть нормы работы, повторяем с пункта 2.
    :param black_list:
    :param user:
    :param db:
    :param data:
    :return:
    """
    month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    all_workouts = db.select_rows(table='workouts_short', user_id=user, new=True)
    all_workouts = sorted(all_workouts, key=lambda a: 0 if a[2] is None else a[2], reverse=True)
    max_job = 0
    for workout in all_workouts:
        if str(workout[8]) != 'None' and str(workout[8]) > month_ago:
            if workout[2]:
                max_job = workout[2]
                break
    logger.debug(f'{max_job=}')

    all_workouts = db.select_rows(table='workouts_long', user_id=user, new=True)
    all_workouts = sorted(all_workouts, key=lambda a: '0' if a[6] is None else a[6], reverse=True)
    work = {'Руки': 0, 'Ноги': 0, 'Грудь': 0, 'Живот': 0, 'Спина': 0}
    for workout in all_workouts:
        if str(workout[7]) != 'None' and str(workout[6]) != 'None' and str(workout[6]) > week_ago:
            work['Руки'] += workout[8]
            work['Ноги'] += workout[9]
            work['Грудь'] += workout[10]
            work['Живот'] += workout[11]
            work['Спина'] += workout[12]
    min_job_group = min(work, key=work.get)
    logger.debug(f'{min_job_group=}')

    exercises = sorted(db.select_rows(table='exercises_muscles_base', muscle_name=min_job_group, new=True))
    exercises_voc = {}
    for exercise in exercises:
        exercises_voc[exercise[0]] = [0, exercise[4]]
    exercises = db.select_rows(table='workouts_long', user_id=user, new=True)
    for exercise in exercises:
        exercises_voc[exercise[2]][0] += 1
    logger.debug(f'{black_list=}')
    for ex in black_list:
        exercises_voc.pop(ex, '')
    rare_exercise = min(exercises_voc, key=exercises_voc.get)
    logger.debug(f'{rare_exercise=}')
    return rare_exercise


async def award_user(user, db):
    """
    Проверяем, был ли в последнем воркауте максимум повторений:
    - находим максимальное повторение в последнем воркауте
    - находим максимальное повторение во всех подходах всех воркаутов упражнения
    - сравниваем и выдаем ответ
    Проверяем, была ли в воркауте выполнена максимальная работа:
    - считаем работу в последнем воркауте
    - считаем работу во всех воркаутах
    - сравниваем и выдаем ответ
    :param user:
    :param db:
    :return:
    """

    two_hours_ago = (datetime.utcnow() - timedelta(seconds=7200)).isoformat()
    # максимальный повтор упражнения
    all_workouts = sorted(db.select_rows(table='workouts_long', user_id=user, new=True), reverse=True)
    exercise = all_workouts[0][2]
    last_workout = sorted(db.select_rows(table='workouts_long', user_id=user, exercise_id=exercise,
                                         workout_id=all_workouts[0][0], new=True))
    all_workouts = sorted(db.select_rows(table='workouts_long', user_id=user, exercise_id=exercise, new=True))

    last_work = 0
    last_reps = 0
    for workout in last_workout:
        last_work += workout[7]
        last_reps = max(last_reps, workout[4])
    logger.debug(f'{last_work=}')
    logger.debug(f'{last_reps=}')
    all_workouts_voc = {}
    max_work = False
    max_reps = False
    for workout in all_workouts:
        if workout[0] in all_workouts_voc:
            if workout[7]:
                all_workouts_voc[workout[0]]['work'] += workout[7]
            all_workouts_voc[workout[0]]['reps'] = max(workout[4], all_workouts_voc[workout[0]]['reps'])
        else:
            all_workouts_voc[workout[0]] = {'work': 0, 'reps': 0}
            if workout[7]:
                all_workouts_voc[workout[0]]['work'] += workout[7]
            all_workouts_voc[workout[0]]['reps'] = max(workout[4], all_workouts_voc[workout[0]]['reps'])
    all_workouts_voc.pop(last_workout[0][0], False)
    for workout in all_workouts_voc:
        max_work = all_workouts_voc[workout]['work'] < last_work
        max_reps = all_workouts_voc[workout]['reps'] < last_reps
    return {'work': max_work, 'reps': exercise if max_reps else max_reps}


async def run_timer(data, db, message, bot):
    data['delete_list'].append(message.message_id)
    for message_id in data['delete_list']:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
    data['delete_list'] = []
    msg = await message.answer_animation(
        animation=db.select_row(table='multimedia', name='timer', new=True)[3],
        caption='Отдыхайте от 10 секунд до 5 минут...',
        reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await asyncio.sleep(2)
    msg = await message.answer(
        text=f'Выполните подход {data["approach"] + 1} из {data["new_workout"][data["approach"]]} повторений '
             f'и нажмите кнопку "Готово". Если вы сделали другое количество, напишите сколько.', reply_markup=ready)
    data['delete_list'].append(msg.message_id)
    return data


async def save_approach(data, db, message, approach):
    if message.text.isdigit():
        data['done_workout'].append(int(message.text))
    else:
        data['done_workout'].append(data['new_workout'][approach - 1])
    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    work = (data['done_workout'][approach - 1] * int(user[11]) / 100
            * db.select_row(table='exercises_base', exercise_id=data['exercise_id'], new=True)[4])
    arms_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=0, new=True)[4]
    legs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=1, new=True)[4]
    chest_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=2, new=True)[4]
    abs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=3, new=True)[4]
    back_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=4, new=True)[4]
    db.add_workout_new(workout_id=data['workout_number'], user_id=user[0], exercise_id=data['exercise_id'], approach=approach,
                       dynamic=data['done_workout'][approach - 1], static=0, date=datetime.utcnow().isoformat(),
                       work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs=abs_work, back=back_work, new=True)
    return data


@router.message(F.video)
@router.message(F.animation)
async def get_multimedia(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.caption == 'timer':
        db.update_cell(table='multimedia', cell='file_id',
                       cell_value=message.animation.file_id, key='name', key_value=message.caption, new=True)
        db.update_cell(table='multimedia', cell='file_unique_id',
                       cell_value=message.animation.file_unique_id, key='name', key_value=message.caption, new=True)
    if message.caption == 'warmup':
        db.update_cell(table='multimedia', cell='file_id',
                       cell_value=message.video.file_id, key='name', key_value=message.caption, new=True)
        db.update_cell(table='multimedia', cell='file_unique_id',
                       cell_value=message.video.file_unique_id, key='name', key_value=message.caption, new=True)
    if message.caption.isdigit():
        db.update_cell(table='exercises_base', cell='file_id', cell_value=message.animation.file_id,
                       key='exercise_id', key_value=int(message.caption), new=True)
        db.update_cell(table='exercises_base', cell='file_unique_id', cell_value=message.animation.file_unique_id,
                       key='exercise_id', key_value=int(message.caption), new=True)


@router.message(Command(commands='statistics'))
async def show_statistics(message: Message, state: FSMContext, db: SQLiteDatabase):
    workouts = db.select_rows(table='workouts_long', user_id=message.from_user.id, new=True)
    msg = ''
    statistics = {}
    for workout in workouts:
        if workout[3] == 1:
            statistics[workout[0]] = str(workout[0]) + ': ' + str(workout[6]) + ' #' + str(workout[2]) + '-' + str(workout[4])
        else:
            statistics[workout[0]] += '-' + str(workout[4])
    for workout in statistics:
        msg += statistics[workout] + '\n'
    await message.answer(text=msg)
    await state.clear()


@router.message(F.text.lower().strip() == 'запустить тренировку')
@router.message(Command(commands='fitness'), MyUserDbFilter(column='birth_date'), MyUserDbFilter(column='sex'))
async def warmup_07new(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    msg = await message.answer(
        text=f'Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
             f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
             f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
             f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.')
    data['delete_list'].append(msg.message_id)
    msg = await message.answer_video(
        video=db.select_row(table='Multimedia', name='warmup', new=True)[3],
        caption='Разминка 8 минут',
        reply_markup=ready)
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=[])
    await state.set_state(FSMTrener.show_exercises)


@router.message(Command(commands='fitness'), MyUserDbFilter(column='birth_date'))
@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMTrener.enter_data_06new))
async def check_data_04new(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    msg = await message.answer(text='Для правильного расчёта нагрузок, необходимо ввести ваш пол, рост и вес. '
                                    'Пол может быть только М или Ж, выберите, какой вам больше подходит. '
                                    'Рост и вес - ЦЕЛЫЕ положительные числа.\n'
                                    'Введите через пробел ваш пол, рост и вес, например Ж 170 70: ',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.enter_data_05new)


@router.message(Command(commands='fitness'))
@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMTrener.enter_bdate_03new))
async def check_bdate_01new(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    msg = await message.answer(text='Для учёта возраста при подборе тренировочной программы '
                                    'введите через пробел дату вашего рождения, в формате 22 06 1990: ',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.enter_bdate_02new)


#  подтверждаем правильность даты
@router.message(F.text, StateFilter(FSMTrener.enter_bdate_02new))
async def enter_bdate_02new(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    date = dateutil.parser.parse(message.text, fuzzy=True)
    msg = await message.answer(text=f'Подтвердите, ваша дата рождения {date.strftime("%d-%m-%Y")} ? '
                                    f'Исправить дату позже не получится.',
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    date = datetime.isoformat(date)
    await state.update_data(date=date)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.enter_bdate_03new)


@router.message(F.text.lower().strip() == 'да', StateFilter(FSMTrener.enter_bdate_03new))
async def enter_bdate_03new(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    db.update_cell(table='users_base_long', cell='birth_date', cell_value=data['date'],
                   key='user_id', key_value=message.from_user.id, new=True)
    msg = await message.answer(text='Данные сохранены')
    data['delete_list'].append(message.message_id)
    data['delete_list'].append(msg.message_id)
    await asyncio.sleep(1)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await state.update_data(delete_list=[])
    msg = await message.answer(text='Для правильного расчёта нагрузок, необходимо ввести ваш пол, рост и вес. '
                                    'Пол может быть только М или Ж, выберите, какой вам больше подходит. '
                                    'Рост и вес - ЦЕЛЫЕ положительные числа.\n'
                                    'Введите через пробел ваш пол, рост и вес, например Ж 170 70: ',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.enter_data_05new)


# проверяем пол, рост, вес
@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMTrener.enter_data_06new))
async def check_data_04new(message: Message, state: FSMContext, db: SQLiteDatabase):
    logger.debug(f'enter check_data_04new')
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    logger.debug(f'{data=}')
    logger.debug(f'dalee message')
    msg = await message.answer(text='Для правильного расчёта нагрузок, необходимо ввести ваш пол, рост и вес. '
                                    'Пол может быть только М или Ж, выберите, какой вам больше подходит. '
                                    'Рост и вес - ЦЕЛЫЕ положительные числа.\n'
                                    'Введите через пробел ваш пол, рост и вес, например Ж 170 70: ',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.enter_data_05new)


@router.message(F.text, StateFilter(FSMTrener.enter_data_05new))
async def enter_data_05new(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    user_data = message.text.lower().strip().split()
    msg = await message.answer(text=f'Подтвердите, ваша пол {user_data[0]}, рост {user_data[1]}, вес {user_data[2]} ? '
                                    f'Пол и рост исправить позже не получится.',
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(user_data=user_data)
    await state.set_state(FSMTrener.enter_data_06new)


@router.message(F.text.lower().strip() == 'да', StateFilter(FSMTrener.enter_data_06new))
async def enter_data_06new(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    db.update_cell(table='users_base_long', cell='sex', cell_value=data['user_data'][0],
                   key='user_id', key_value=message.from_user.id, new=True)
    db.update_cell(table='users_base_long', cell='height', cell_value=data['user_data'][1],
                   key='user_id', key_value=message.from_user.id, new=True)
    db.update_cell(table='users_base_long', cell='weight', cell_value=data['user_data'][2],
                   key='user_id', key_value=message.from_user.id, new=True)
    msg = await message.answer(text='Данные сохранены')
    data['delete_list'].append(message.message_id)
    data['delete_list'].append(msg.message_id)
    await asyncio.sleep(1)
    logger.debug(f'{data["delete_list"]=}')
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    msg = await message.answer(
        text=f'Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
             f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
             f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
             f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.')
    data['delete_list'].append(msg.message_id)
    msg = await message.answer_video(
        video=db.select_row(table='Multimedia', name='warmup', new=True)[3],
        caption='Разминка 8 минут',
        reply_markup=ready)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=[])
    await state.update_data(exercise_id=None)
    await state.set_state(FSMTrener.show_exercises)


@router.message(F.text.lower().strip() == 'да', StateFilter(FSMTrener.workout_end))
@router.message(F.text, StateFilter(FSMTrener.show_exercises))
@router.message(F.text.lower().strip() == 'заменить', StateFilter(FSMTrener.workout))
# @router.message(F.text.lower().strip() == 'выбрать автоматически', StateFilter(FSMTrener.workout))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    logger.debug('pered zamenit')
    if message.text.lower().strip() == 'заменить':
        data['black_list'].append(data['exercise_id'])
        if len(data['black_list']) > 27:
            data['black_list'] = []
        logger.debug(f'{data["black_list"]=}')

    data['exercise_id'] = await auto_choose_exercise(message.from_user.id, db, data['black_list'])
    logger.debug(f'{data["exercise_id"]=}')
    exercise = db.select_row(table='exercises_base', exercise_id=data['exercise_id'], new=True)
    if exercise[5]:
        # msg = await message.edit_media()
        msg = await message.answer_animation(
            animation=exercise[5],
            caption=f'{exercise[0]} {exercise[2]}',
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Заменить"), KeyboardButton(text="Оставить")],
                                                       [KeyboardButton(text="Выбрать из списка")]],
                                             one_time_keyboard=True, resize_keyboard=True))
    else:
        msg = await message.answer(text=exercise[2],
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Заменить"),
                                                                               KeyboardButton(text="Оставить")],
                                                                              [KeyboardButton(text="Выбрать из списка")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(exercise_id=data['exercise_id'])
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=data['black_list'])
    await state.set_state(FSMTrener.workout)


@router.message(F.text.lower().strip() == 'оставить', StateFilter(FSMTrener.workout))
@router.message(F.text.isdigit(), StateFilter(FSMTrener.workout))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if message.text.lower().strip() == 'оставить':
        exercise_id = data['exercise_id']
        data['delete_list'].pop() if data['delete_list'] else ''
    else:
        exercise_id = int(message.text)
        exercise = db.select_row(table='exercises_base', exercise_id=exercise_id, new=True)
        if exercise[5]:
            await message.answer_animation(
                animation=exercise[5],
                caption=f'{exercise[0]} {exercise[2]}',
                reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer(text=exercise[2], reply_markup=ReplyKeyboardRemove())

    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    time_start = datetime.utcnow().timestamp()
    workout_number = db.select_all_table(table='workouts_long', new=True)[-1][0] + 1
    last_workouts = db.select_last_workout_new(user_id=user[0], exercise_id=exercise_id)

    if last_workouts:
        for i in range(5 - len(last_workouts)):
            last_workouts.append((last_workouts[0][0], last_workouts[0][1], last_workouts[0][2],
                                  len(last_workouts) + i, 0, 0, last_workouts[0][2], 0, 0, 0, 0, 0, 0))
        new_workout = (str(last_workouts[0][4]) + ' ' + str(last_workouts[1][4]) + ' ' + str(last_workouts[2][4]) +
                       ' ' + str(last_workouts[3][4]) + ' ' + str(last_workouts[4][4]))
        new_workout = generate_new_split(new_workout)
    else:
        new_workout = '1 1 1 1 1'
    new_workout_split = list(map(int, new_workout.split()))
    msg = await message.answer(
        text=f'Если упражнение вам незнакомо или непонятно, найдите его в интернет и изучите самостоятельно.\n\n'
             f'Теперь вам нужно выполнить 5 подходов выбранного упражнения, с указанным количество повторений: '
             f'\n{new_workout}+\n'
             f'Повторения делайте в среднем темпе, паузу между подходами выбирайте самостоятельно, '
             f'руководствуясь собственными ощущениями. Обычно пауза длится от 10 секунд до 3 минут. '
             f'В последнем пятом подходе сделайте МАКСИМУМ повторений, для этого он обозначен '
             f'{new_workout_split[-1]}+.\n'
             f'Итак, выполните первый подход из {new_workout_split[0]} повторений и нажмите кнопку "Готово". '
             f'Если не удалось выполнить все необходимые повторения, напишите сколько удалось.',
        reply_markup=ready)

    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(exercise_id=exercise_id)
    await state.update_data(workout_number=workout_number)
    await state.update_data(time_start=time_start)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(new_workout=new_workout_split)
    await state.update_data(done_workout=[])
    await state.update_data(approach=1)
    await state.set_state(FSMTrener.workout_process)


@router.message(F.text.lower().strip() == 'выбрать из списка', StateFilter(FSMTrener.workout))
async def start_trener(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await asyncio.sleep(1)

    msg = await message.answer(text='Выберите упражнение из списка ниже и пришлите его номер ответным сообщением.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)

    await asyncio.sleep(1)
    exercises_table = db.select_all_table('exercises_base', new=True)
    if exercises_table:
        captions = []
        for exercise in exercises_table:
            captions.append(str(exercise[0]) + ' ' + exercise[2])
        msg = await message.answer(text='\n'.join(captions), reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.workout)
    else:
        msg = await message.answer(text='Сбой базы данных. Попробуйте еще раз или обратитесь к администратору',
                                   reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.show_exercises)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text, StateFilter(FSMTrener.workout_process))
async def workout_process(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    data = await save_approach(data, db, message, data['approach'])
    await state.update_data(done_workout=data['done_workout'])

    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    if data['approach'] == 1:
        msg_timer = await message.answer_animation(
            animation=db.select_row(table='multimedia', name='timer', new=True)[3],
            caption='Отдыхайте от 10 секунд до 5 минут...',
            reply_markup=ReplyKeyboardRemove())
        await state.update_data(msg_timer=msg_timer.message_id)
    await asyncio.sleep(2)
    msg = await message.answer(
        text=f'Выполните подход {data["approach"] + 1} из {data["new_workout"][data["approach"]]} повторений '
             f'и нажмите кнопку "Готово". Если вы сделали другое количество, напишите сколько.', reply_markup=ready)
    data['delete_list'].append(msg.message_id)
    if data['approach'] == 4:
        data['delete_list'].append(data['msg_timer'])
    # data = await run_timer(data, db, message, bot)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(approach=data["approach"] + 1)
    if data['approach'] == 4:
        await state.set_state(FSMTrener.workout_done)
    else:
        await state.set_state(FSMTrener.workout_process)


@router.message(F.text, StateFilter(FSMTrener.workout_done))
async def workout_done(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    data = await save_approach(data, db, message, data['approach'])
    await state.update_data(done_workout=data['done_workout'])

    await message.answer(text=f"Тренировка сохранена: упражнение №{data['exercise_id']}, подходы "
                              f"{' '.join(list(map(str, data['done_workout'])))}. "
                              f"Рекомендованный перерыв между тренировками одного упражнения - от 2 до 7 дней. "
                              f"Если перерыв будет более 7 дней, прогресс может отсутствовать.")
    awards = await award_user(message.from_user.id, db)
    if awards['reps']:
        if awards['work']:
            msg = await message.answer(
                text=f'Поздравляем, у вас новые достижения! Вы выполнили максимальную работу за тренировку, '
                     f'и побили рекорд повторений в упражнении №{awards["reps"]}.',
                reply_markup=ReplyKeyboardRemove())
        else:
            msg = await message.answer(
                text=f'Поздравляем, у вас новое достижение! Вы побили рекорд повторений в упражнении '
                     f'№{awards["reps"]}.', reply_markup=ReplyKeyboardRemove())
        data['delete_list'].append(msg.message_id)
    else:
        if awards['work']:
            msg = await message.answer(
                text=f'Поздравляем, у вас новое достижение! Вы выполнили максимальную работу за тренировку. ',
                reply_markup=ReplyKeyboardRemove())
            data['delete_list'].append(msg.message_id)
    msg = await message.answer(text=f"Если остались силы, можете выполнить ещё 5 подходов другого упражнения. Готовы?",
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.workout_end)


@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMTrener.workout_end))
async def end_workout(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    db.update_cell(table='users_base_long', cell='trener_sub', cell_value=datetime.utcnow().isoformat(),
                   key='user_id', key_value=message.from_user.id, new=True)
    msg = await message.answer(text='До новых встреч!', reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await asyncio.sleep(10)
    for message_id in data['delete_list']:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
    await state.update_data(delete_list=[])
    await state.clear()


@router.message(F.text.lower().strip() == 'напомнить через неделю')
async def remind_after_week(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    db.update_cell(table='users_base_long', cell='trener_sub', cell_value=datetime.utcnow().isoformat(),
                   key='user_id', key_value=message.from_user.id, new=True)
    await message.answer(text='Добавили вас в рассылку')

@router.message(F.text.lower().strip() == 'отписаться от напоминаний')
async def unsubscribe(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    await message.answer(text='Отписали вас. Если запустите тренировку самостоятельно, напоминания возобновятся.')
