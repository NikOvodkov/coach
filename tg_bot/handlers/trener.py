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
from tg_bot.utils.trener import Approach, show_exercise, award_user, save_approach, fill_exercises_users, show_approach, generate_full_workout

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
    msg = await message.answer(
        text=f'Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
             f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
             f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
             f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.',
        reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    msg = await message.answer_video(
        video=db.select_rows(table='multimedia', fetch='one', name='warmup')['file_id'],
        caption='Разминка 8 минут',
        reply_markup=ready)
    data['delete_list'].append(msg.message_id)
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
    msg = await message.answer(
        text=f'Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
             f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
             f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
             f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.')
    data['delete_list'].append(msg.message_id)
    msg = await message.answer_video(
        video=db.select_rows(table='multimedia', fetch='one', name='warmup')['file_id'],
        caption='Разминка 8 минут',
        reply_markup=ready)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=[])
    await state.update_data(new_workout=[])
    await state.set_state(FSMTrener.show_exercises)


# # @router.message(F.text.lower().strip() == 'да', StateFilter(FSMTrener.workout_end))
# @router.message(F.text.lower().strip() == 'заменить', StateFilter(FSMTrener.workout))
# @router.message(F.text.isdigit(), StateFilter(FSMTrener.workout))
# @router.message(F.text, StateFilter(FSMTrener.show_exercises))
# # @router.message(F.text.lower().strip() == 'выбрать автоматически', StateFilter(FSMTrener.workout))
# async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
#     """
#     Перед началом тренировки, нужно проверить и заполнить при необходимости таблицу exercises_users
#     для данного пользователя.
#     :param message:
#     :param state:
#     :param db:
#     :param bot:
#     :return:
#     """
#     data = await state.get_data()
#     if 'delete_list' not in data:
#         data['delete_list'] = []
#     data['delete_list'].append(message.message_id)
#     data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
#     logger.debug(f'before fill_exercises_users')
#
#     await fill_exercises_users(user_id=message.from_user.id, db=db)
#     # users = db.select_table(table='users')
#     # for user in users:
#     #     await fill_exercises_users(user_id=user['user_id'], db=db)
#
#     logger.debug(f'after fill_exercises_users')
#     if message.text.lower().strip() == 'заменить':
#         data['black_list'].append(data['new_workout'][0][0])
#         if len(data['black_list']) > 27:
#             data['black_list'] = []
#         logger.debug(f'{data["black_list"]=}')
#     if message.text.lower().isdigit():
#         # data['new_workout'] = await gnrt_wrkt(user_id=message.from_user.id, db=db, old_ex=int(message.text),
#         #                                       black_list=data['black_list'])
#         data['new_workout'] = await generate_full_workout(db, message.from_user.id, data['black_list'], int(message.text))
#     elif 'new_workout' not in data:
#         # data['new_workout'] = await gnrt_wrkt(user_id=message.from_user.id, db=db, black_list=data['black_list'])
#         data['new_workout'] = await generate_full_workout(db, message.from_user.id, data['black_list'])
#     logger.debug(f'{data["new_workout"][0][0]=}')
#     msg = await show_exercise(message, db, data["new_workout"][0][0], choose_exercise)
#     data['delete_list'].append(msg.message_id)
#     await state.update_data(new_workout=data["new_workout"])
#     await state.update_data(delete_list=data['delete_list'])
#     await state.update_data(black_list=data['black_list'])
#     await state.update_data(change_exercise=True)
#     await state.set_state(FSMTrener.workout)


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


# @router.message(F.text.lower().strip() == 'оставить', StateFilter(FSMTrener.workout))
# @router.message(F.text, StateFilter(FSMTrener.workout_process))
# async def workout_process(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
#     data = await state.get_data()
#     data['delete_list'].append(message.message_id)
#     data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
#     if 'done_approaches' not in data:
#         data['done_approaches'] = []
#     if 'approach' not in data:
#         data['approach'] = 0
#         approach = 0
#     else:
#         approach = data['approach']
#     if len(data['done_approaches']) > 0 and data['done_approaches'][-1][0] != data['new_workout'][0][0]:
#         logger.debug(f'STATE CHANGED TO FSMTrener.show_exercises')
#         await state.set_state(FSMTrener.show_exercises)
#     if data['change_exercise']:
#     # if approach == 0:
#         # time_start = datetime.utcnow().timestamp()
#         # await state.update_data(time_start=time_start)
#         await state.update_data(approach=1)
#         await state.update_data(change_exercise=False)
#         await state.set_state(FSMTrener.workout_process)
#
#         logger.debug(f'before 1st show_approach')
#         msg = await show_approach(data, message, db, ready_end, bot)
#         data['delete_list'].append(msg.message_id)
#     else:
#         data = await save_approach(data, db, message)
#         await state.update_data(approach=len(data['done_approaches']))
#         await state.update_data(workout_number=data["workout_number"])
#         await state.update_data(done_approaches=data['done_approaches'])
#         await state.update_data(new_workout=data["new_workout"])
#         await state.update_data(approach=approach + 1)
#         msg = await message.answer_animation(
#             animation=db.select_rows(table='multimedia', fetch='one', name='timer')['file_id'],
#             caption='Отдыхайте от 10 секунд до 5 минут...',
#             reply_markup=ReplyKeyboardRemove())
#         data['delete_list'].append(msg.message_id)
#         await asyncio.sleep(3)
#         cur_state = await state.get_state()
#         logger.warning(f'{cur_state=}')
#         if cur_state != FSMTrener.show_exercises:
#             await state.set_state(FSMTrener.workout_process)
#             msg = await show_approach(data, message, db, ready_end, bot)
#             data['delete_list'].append(msg.message_id)
#
#         # добавить еще сохранение при смене упражнения в воркауте
#         # if (len(data['new_workout']) == 1) or data['done_approaches'][-1][0] != data['new_workout'][0][0]:
#         if len(data['new_workout']) == 1:
#             logger.debug(f'workout_process exit {data["new_workout"]=}')
#             await state.set_state(FSMTrener.workout_done)
#     await state.update_data(delete_list=data['delete_list'])
#     logger.debug(f'workout_process exit {data["delete_list"]=}')


# @router.message(F.text, StateFilter(FSMTrener.workout_done))
# async def workout_done(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
#     logger.debug(f'start workout_done')
#     data = await state.get_data()
#     data['delete_list'].append(message.message_id)
#     data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
#     logger.debug(f'before last save_approaches')
#     data = await save_approach(data, db, message)
#     logger.debug(f'after last save_approaches')
#     await state.update_data(workout_number=data["workout_number"])
#     await state.update_data(done_approaches=data['done_approaches'])
#     await state.update_data(new_workout=data["new_workout"])
#     logger.debug(f'before workout saved {data["done_approaches"]=}')
#     await message.answer(text=f"Тренировка сохранена: "
#                               f"{', '.join(list(map(lambda app: f'№{str(app[0])}-{str(app[1])}', data['done_approaches'])))}\n"
#                               f"Рекомендованный перерыв между тренировками одного упражнения - от 2 до 7 дней. "
#                               f"Если перерыв будет более 7 дней, прогресс может отсутствовать.")
#     awards = await award_user(message.from_user.id, db)
#     logger.debug(f'{awards=}')
#     if awards['reps']:
#         if awards['work']:
#             msg = await message.answer(
#                 text=f'🎉 Поздравляем, у вас новые достижения! 🏆🏆 Вы выполнили максимальную работу за тренировку, '
#                      f'и побили рекорд повторений в упражнении №{awards["reps"]}.',
#                 reply_markup=ReplyKeyboardRemove())
#         else:
#             msg = await message.answer(
#                 text=f'🎉 Поздравляем, у вас новое достижение! 🏆 Вы побили рекорд повторений в упражнении '
#                      f'№{awards["reps"]}.', reply_markup=ReplyKeyboardRemove())
#         data['delete_list'].append(msg.message_id)
#     else:
#         if awards['work']:
#             msg = await message.answer(
#                 text=f'🎉 Поздравляем, у вас новое достижение! 🏆 Вы выполнили максимальную работу за тренировку. ',
#                 reply_markup=ReplyKeyboardRemove())
#             data['delete_list'].append(msg.message_id)
#     # msg = await message.answer(text=f"Если остались силы, можете выполнить ещё 5 подходов другого упражнения. Готовы?",
#     #                            reply_markup=yesno)
#     # data['delete_list'].append(msg.message_id)
#     await state.update_data(delete_list=data['delete_list'])
#     await state.set_state(FSMTrener.workout_end)


# @router.message(F.text.lower().strip() == 'закончить', StateFilter(FSMTrener.workout_end))
# async def end_workout(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
#     data = await state.get_data()
#     db.update_cell(table='users', cell='coach_sub', cell_value=datetime.utcnow().isoformat(),
#                    key='user_id', key_value=message.from_user.id)
#     msg = await message.answer(text='До новых встреч!', reply_markup=ReplyKeyboardRemove())
#     logger.debug(f'after do novyh vstrech')
#     data['delete_list'].append(msg.message_id)
#     data['delete_list'].append(message.message_id)
#     await asyncio.sleep(10)
#     data['delete_list'] = await clear_delete_list(data['delete_list'], bot=bot, user_id=message.from_user.id)
#     logger.debug(f'after deleting list')
#     await state.update_data(delete_list=data['delete_list'])
#     await state.clear()


@router.message(F.text.lower().strip() == 'выбрать из списка', StateFilter(FSMTrener.workout))
@router.message(F.text.lower().strip() == 'обновить список', StateFilter(FSMTrener.workout))
async def start_trener(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await asyncio.sleep(1)
    exercises_table = db.select_table('exercises')
    if exercises_table:
        captions = []
        for exercise in exercises_table:
            exercise_list = db.select_rows(table='exercises_users', fetch='one',
                                           exercise_id=exercise['exercise_id'], user_id=message.from_user.id)
            exercise_type = db.select_rows(table='exercises', fetch='one', exercise_id=exercise['exercise_id'])
            logger.debug(f'{exercise_list=}')
            if exercise_type and exercise_type['type'] in [1, 2]:
                if exercise_list:
                    if exercise_list['list'] == 1:
                        captions.append(('💚' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    elif exercise_list['list'] == 0:
                        captions.append(('⛔' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    else:
                        captions.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
                else:
                    captions.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
        msg = await message.answer(text='\n'.join(captions), reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.workout)
    else:
        msg = await message.answer(text='Сбой базы данных. Попробуйте еще раз или обратитесь к администратору',
                                   reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.show_exercises)
    data['delete_list'].append(msg.message_id)
    msg = await message.answer(text='КОМАНДЫ:\n'
                                    'пришлите номер чтобы ВЫПОЛНИТЬ упражнение;\n'
                                    '!-номер, если вы НЕ МОЖЕТЕ делать упражнение;\n'
                                    '!+номер, если вы ЛЮБИТЕ упражнение;\n'
                                    '!=номер, чтобы СБРОСИТЬ пометки.\n',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text.startswith('!='), F.text.strip()[2:].isdigit(), StateFilter(FSMTrener.workout))
async def add_white_list(message: Message, state: FSMContext, db: SQLiteDatabase):
    """
    :param message:
    :param state:
    :param db:
    :return:
    1. Ищем упражнение в базе
    2. Если оно есть, меняем поле list на нужное
    3. Если его нет, добавляем с нужным полем list
    """
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    exercise_id = int(message.text.strip()[2:])
    exercises_users = db.select_rows(table='exercises_users', fetch='one', exercise_id=exercise_id, user_id=message.from_user.id)
    if exercises_users:
        db.update_cell_new(table='exercises_users', cell='list', cell_value=None,
                           exercise_id=exercise_id, user_id=message.from_user.id)
    else:
        db.add_exercise_user(user_id=message.from_user.id, exercise_id=exercise_id)
    msg = await message.answer(text='Данные сохранены.',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Обновить список')]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text.startswith('!+'), F.text.strip()[2:].isdigit(), StateFilter(FSMTrener.workout))
async def add_white_list(message: Message, state: FSMContext, db: SQLiteDatabase):
    """
    :param message:
    :param state:
    :param db:
    :return:
    1. Ищем упражнение в базе
    2. Если оно есть, меняем поле list на нужное
    3. Если его нет, добавляем с нужным полем list
    """
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    exercise_id = int(message.text.strip()[2:])
    exercises_users = db.select_rows(table='exercises_users', fetch='one', exercise_id=exercise_id, user_id=message.from_user.id)
    if exercises_users:
        logger.debug(f'{exercises_users=}')
        db.update_cell_new(table='exercises_users', cell='list', cell_value=1,
                           exercise_id=exercise_id, user_id=message.from_user.id)
    else:
        db.add_exercise_user(user_id=message.from_user.id, exercise_id=exercise_id, list_=1)
    msg = await message.answer(text='Данные сохранены, упражнение будет предлагаться чаще.',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Обновить список')]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text.startswith('!-'), F.text.strip()[2:].isdigit(), StateFilter(FSMTrener.workout))
async def add_white_list(message: Message, state: FSMContext, db: SQLiteDatabase):
    """
    :param message:
    :param state:
    :param db:
    :return:
    1. Ищем упражнение в базе
    2. Если оно есть, меняем поле list на нужное
    3. Если его нет, добавляем с нужным полем list
    """
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    exercise_id = int(message.text.strip()[2:])
    exercises_users = db.select_rows(table='exercises_users', fetch='one', exercise_id=exercise_id, user_id=message.from_user.id)
    if exercises_users:
        db.update_cell_new(table='exercises_users', cell='list', cell_value=0,
                           exercise_id=exercise_id, user_id=message.from_user.id)
    else:
        db.add_exercise_user(user_id=message.from_user.id, exercise_id=exercise_id, list_=0)
    msg = await message.answer(text='Данные сохранены, упражнение не будет предлагаться.',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Обновить список')]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text.lower().strip() == 'напомнить через неделю')
async def remind_after_week(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    db.update_cell(table='users', cell='coach_sub', cell_value=datetime.utcnow().isoformat(),
                   key='user_id', key_value=message.from_user.id)
    await message.answer(text='Добавили вас в рассылку')


@router.message(F.text.lower().strip() == 'отписаться от напоминаний')
async def unsubscribe(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    await message.answer(text='Отписали вас. Если запустите тренировку самостоятельно, напоминания возобновятся.')
