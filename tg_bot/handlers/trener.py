import asyncio
import os
from datetime import timedelta, datetime
from pathlib import Path
from typing import Any

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
from tg_bot.keyboards.trener import yesno, ready, choose_exercise, nokeyboard, ready_end
from tg_bot.lexicon.life_calendar import LEXICON_RU
from tg_bot.services.ufuncs import clear_delete_list
from tg_bot.states.trener import FSMTrener
from tg_bot.utils.life_calendar import generate_image_calendar
from tg_bot.states.life_calendar import FSMLifeCalendar
from tg_bot.utils.trener import Approach, show_exercise, award_user, save_approach, fill_exercises_users, show_approach, generate_full_workout, run_warmup

# Инициализируем роутер уровня модуля
router = Router()


@router.message(Command(commands='statistics'))
async def show_statistics(message: Message, state: FSMContext, db: SQLiteDatabase):
    workouts = db.select_rows(table='approaches', fetch='all', user_id=message.from_user.id)
    logger.debug(f'{workouts=}')
    msg = ''
    statistics = {}
    for workout in workouts:
        if workout['workout_id'] in statistics:
            statistics[workout['workout_id']] += ' #' + str(workout['exercise_id']) + '-' + str(workout['dynamic'])
        else:
            if workout['date']:
                logger.debug(f'{workout["date"]=}')
                date = datetime.fromisoformat(workout['date']).strftime('%d.%m')
            else:
                date = ''
            statistics[workout['workout_id']] = (date + ' #' + str(workout['exercise_id'])
                                                 + '-' + str(workout['dynamic']))
    logger.debug(f'{statistics=}')
    i = 1
    msg = {1: ''}
    for workout in statistics:
        if len(msg[i]) > 4000:
            await message.answer(text=msg[i])
            i += 1
            msg[i] = ''
        msg[i] += statistics[workout] + '\n'
    await message.answer(text=msg[i], reply_markup=ReplyKeyboardRemove())
    await state.clear()


@router.message(F.text.lower().strip() == 'запустить тренировку')
@router.message(Command(commands='fitness'), MyUserDbFilter(column='birth_date'), MyUserDbFilter(column='sex'))
async def warmup_07new(message: Message, state: FSMContext, db: SQLiteDatabase, cell: Any):
    logger.debug(f'{cell=}')
    if message.text == '/fitness':
        await state.clear()
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    logger.debug(f'{data["delete_list"]=}')
    data = await run_warmup(data, db, message)
    # msg = await message.answer(
    #     text=f'Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
    #          f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
    #          f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
    #          f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.',
    #     reply_markup=ReplyKeyboardRemove())
    # data['delete_list'].append(msg.message_id)
    # msg = await message.answer_video(
    #     video=db.select_rows(table='multimedia', fetch='one', name='warmup')['file_id'],
    #     caption='Разминка 8 минут',
    #     reply_markup=ready)
    # data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    logger.debug(f'{data["delete_list"]=}')
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=[])
    await state.set_state(FSMTrener.show_exercises)


@router.message(Command(commands='fitness'), MyUserDbFilter(column='birth_date'))
@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMTrener.enter_data_06new))
async def check_data_04new(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.text == '/fitness':
        await state.clear()
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
    if message.text == '/fitness':
        await state.clear()
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
        data['black_list'] = []
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
    db.update_cell(table='users', cell='birth_date', cell_value=data['date'],
                   key='user_id', key_value=message.from_user.id)
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
    db.update_cell(table='users', cell='sex', cell_value=data['user_data'][0],
                   key='user_id', key_value=message.from_user.id)
    db.update_cell(table='users', cell='height', cell_value=data['user_data'][1],
                   key='user_id', key_value=message.from_user.id)
    db.update_cell(table='users', cell='weight', cell_value=data['user_data'][2],
                   key='user_id', key_value=message.from_user.id)
    msg = await message.answer(text='Данные сохранены')
    data['delete_list'].append(message.message_id)
    data['delete_list'].append(msg.message_id)
    await asyncio.sleep(1)
    logger.debug(f'{data["delete_list"]=}')
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    data = await run_warmup(data, db, message)
    # msg = await message.answer(
    #     text=f'Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
    #          f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
    #          f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
    #          f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.')
    # data['delete_list'].append(msg.message_id)
    # msg = await message.answer_video(
    #     video=db.select_rows(table='multimedia', fetch='one', name='warmup')['file_id'],
    #     caption='Разминка 8 минут',
    #     reply_markup=ready)
    # data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=[])
    await state.update_data(new_workout=[])
    await state.set_state(FSMTrener.show_exercises)


@router.message(F.text.lower().strip() == 'изучить подробно', StateFilter(FSMTrener.workout))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    exercise_id = data["new_workout"][0][0]
    exercise = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id)
    msg = await message.answer(
        text=f'{exercise["name"]}\n'
             f'Описание:\n'
             f'{exercise["description"]}\n'
             f'Очень подробное описание по ссылке:\n'
             f'{exercise["description_text_link"]}\n'
             f'Обучающее видео:\n'
             f'{exercise["description_video_link"]}\n'
             f'Чтобы вернуться, нажмите кнопку Готово.',
        reply_markup=ready)
    # data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.show_exercises)


@router.message(F.text.lower().strip() == 'напомнить через неделю')
async def remind_after_week(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    db.update_cell(table='users', cell='coach_sub', cell_value=datetime.utcnow().isoformat(),
                   key='user_id', key_value=message.from_user.id)
    await message.answer(text='Добавили вас в рассылку')


@router.message(F.text.lower().strip() == 'отписаться от напоминаний')
async def unsubscribe(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    await message.answer(text='Отписали вас. Если запустите тренировку самостоятельно, напоминания возобновятся.')
