import asyncio

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.services.ufuncs import clear_delete_list
from tg_bot.states.trener import FSMTrener

router = Router()


@router.message(F.text.lower().strip() == 'вернуться', StateFilter(FSMTrener.workout))
@router.message(F.text.lower().strip() == 'выбрать из списка', StateFilter(FSMTrener.workout))
@router.message(F.text.lower().strip() == 'обновить список', StateFilter(FSMTrener.workout))
async def start_trener(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await asyncio.sleep(1)
    exercises_table = db.select_table('exercises')
    if exercises_table:
        captions = ['----------УПРАЖНЕНИЯ-----']
        captions_timer = ['----------ТАЙМЕРЫ-----']
        captions_warmup = ['----------РАЗМИНКИ-----']
        captions_cooldown = ['----------ЗАМИНКИ-----']
        captions_workout = ['----------ТРЕНИРОВКИ-----']
        for exercise in exercises_table:
            exercise_list = db.select_rows(table='exercises_users', fetch='one',
                                           exercise_id=exercise['exercise_id'], user_id=message.from_user.id)
            exercise_type = db.select_rows(table='exercises', fetch='one', exercise_id=exercise['exercise_id'])['type']
            # exercise_type = exercise_list['type'] if exercise_list else None
            logger.debug(f'{exercise_list=}')
            # формируем список упражнений
            if exercise_type in [1, 2]:
                if exercise_list:
                    if exercise_list['list'] == 1:
                        captions.append(('💚' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    elif exercise_list['list'] == 0:
                        captions.append(('⛔' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    else:
                        captions.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
                else:
                    captions.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
            # формируем список таймеров
            logger.debug(f'before timer list {captions=}')
            if exercise_type in [8]:
                if exercise_list:
                    if exercise_list['list'] == 1:
                        captions_timer.append(('✅' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    elif exercise_list['list'] == 0:
                        captions_timer.append(('  ' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    else:
                        captions_timer.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
                else:
                    captions_timer.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
            logger.debug(f'after timer list {captions_timer=}')
            # формируем список разминок
            if exercise_type in [5]:
                if exercise_list:
                    if exercise_list['list'] == 1:
                        captions_warmup.append(('✅' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    elif exercise_list['list'] == 0:
                        captions_warmup.append(('  ' + str(exercise['exercise_id'])).rjust(3, '⠀') + ' ' + exercise['name'])
                    else:
                        captions_warmup.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
                else:
                    captions_warmup.append('  ' + str(exercise['exercise_id']).rjust(3, '⠀') + ' ' + exercise['name'])
        # i = 1
        # msg_ = {1: ''}
        # statistics = captions + captions_timer
        # logger.debug(f'{statistics=}')
        # for workout in statistics:
        #     if len(msg_[i]) > 4000:
        #         msg = await message.answer(text=msg_[i])
        #         data['delete_list'].append(msg.message_id)
        #         i += 1
        #         msg_[i] = ''
        #     msg_[i] += statistics[workout] + '\n'
        # msg = await message.answer(text=msg_[i], reply_markup=ReplyKeyboardRemove())
        # data['delete_list'].append(msg.message_id)
        msg = await message.answer(text='\n'.join(captions+captions_timer+captions_warmup),
                                   reply_markup=ReplyKeyboardRemove())
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
    msg = await message.answer(text='Данные сохранены.',
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
    exercises_users = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id, user_id=message.from_user.id)
    if exercises_users:
        if exercises_users['type'] in [5, 6, 8]:
            msg = await message.answer(text='Таймер, разминку и заминку нельзя заблокировать!',
                                       reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Вернуться')]],
                                                                        one_time_keyboard=True, resize_keyboard=True))
        else:
            db.update_cell_new(table='exercises_users', cell='list', cell_value=0,
                               exercise_id=exercise_id, user_id=message.from_user.id)
            msg = await message.answer(text='Данные сохранены, материал не будет предлагаться.',
                                       reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Обновить список')]],
                                                                        one_time_keyboard=True, resize_keyboard=True))
        data['delete_list'].append(msg.message_id)
    # else:
    #     if exercises_users['type'] in [8]:
    #         db.add_exercise_user(user_id=message.from_user.id, exercise_id=exercise_id, list_=None)
    #         msg = await message.answer(text='Таймер нельзя заблокировать!',
    #                                    reply_markup=ReplyKeyboardRemove())
    #     else:
    #         db.add_exercise_user(user_id=message.from_user.id, exercise_id=exercise_id, list_=0)
    #         msg = await message.answer(text='Данные сохранены, материал не будет предлагаться.',
    #                                    reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Обновить список')]],
    #                                                                     one_time_keyboard=True, resize_keyboard=True))
    # data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
