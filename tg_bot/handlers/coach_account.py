import asyncio

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.coach import IsForwarded
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
        msg = await message.answer(text='\n'.join(captions + captions_timer + captions_warmup),
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
    exercises_users = db.select_rows(table='exercises_users', fetch='one', exercise_id=exercise_id, user_id=message.from_user.id)
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


@router.message(Command(commands='choose_coach'))
async def choose_coach(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.text == '/fitness':
        await state.clear()
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    logger.debug(f'{data["delete_list"]=}')
    await state.set_state(FSMTrener.show_exercises)


@router.message(F.text, IsForwarded())
async def is_forwarded(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot, user):
    """Если у пользователя нет реферера, предлагаем добавить реферера или тренера.
    Если есть реферер, предлагаем добавить только тренера.
    :param bot:
    :param state:
    :param message:
    :param db:
    :param user:
    :return:
    """
    logger.debug(f'{user=}')
    logger.debug(f'{dict(user)=}')
    db_user = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
    db_referrer = db_user['referrer']
    db_trener = db_user['coach_id']
    logger.debug(f'{db_trener=} {db_referrer=}')
    if db_trener:
        logger.debug(f'db_trener not None')
        trener = await bot.get_chat(db_trener)
        await message.answer(text=f'{message.from_user.username}, ваш текущий тренер:\n'
                                  f'username = {trener.username}\n'
                                  f'first_name = {trener.first_name}\n'
                                  f'last_name = {trener.last_name}\n'
                                  f'id = {trener.id}',
                             reply_markup=ReplyKeyboardRemove())
    if db_referrer:
        logger.debug(f'db_referrer not None')
        await message.answer(text=f'{message.from_user.username}, назначить этого пользователя вашим тренером?\n'
                                  f'username = {user.username}\n'
                                  f'first_name = {user.first_name}\n'
                                  f'last_name = {user.last_name}\n'
                                  f'id = {user.id}',
                             reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назначить')],
                                                                        [KeyboardButton(text='Нет')]],
                                                              one_time_keyboard=True, resize_keyboard=True))
    else:
        logger.debug(f'before message')
        await message.answer(text=f'{message.from_user.username}, назначить этого пользователя вашим реферером или тренером? '
                                  f'Тренера можно сменить, реферера нельзя.\n'
        # f'bot.get_chat = {await bot.get_chat(user.id)}\n'
                                  f'username = {user.username}\n'
                                  f'first_name = {user.first_name}\n'
                                  f'last_name = {user.last_name}\n'
                                  f'id = {user.id}',
                             reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Тренером')],
                                                                        [KeyboardButton(text='Реферером')],
                                                                        [KeyboardButton(text='Отменить')]],
                                                              one_time_keyboard=True, resize_keyboard=True))
    logger.debug(f'after message')
    await state.update_data(trener=dict(user))
    await state.set_state(FSMTrener.is_forwarded)


@router.message(F.text, StateFilter(FSMTrener.is_forwarded))
async def is_forwarded_1(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    logger.debug(f'enter is_forwarded_1 {data=}')
    if (message.text == 'Тренером') or (message.text == 'Назначить'):
        db.update_cells(table='users', cells={'coach_id': data["trener"]["id"]}, user_id=message.from_user.id)
        await message.answer(text=f'Ваш новый тренер:\n'
                                  f'username = {data["trener"]["username"]}\n'
                                  f'first_name = {data["trener"]["first_name"]}\n'
                                  f'last_name = {data["trener"]["last_name"]}\n'
                                  f'id = {data["trener"]["id"]}',
                             reply_markup=ReplyKeyboardRemove())
    elif message.text == 'Реферером':
        db.update_cells(table='users', cells={'referrer': data["trener"]["id"]}, user_id=message.from_user.id)
        await message.answer(text=f'Ваш реферер:\n'
                                  f'username = {data["trener"]["username"]}\n'
                                  f'first_name = {data["trener"]["first_name"]}\n'
                                  f'last_name = {data["trener"]["last_name"]}\n'
                                  f'id = {data["trener"]["id"]}',
                             reply_markup=ReplyKeyboardRemove())
    elif (message.text == 'Отменить') or (message.text == 'Нет'):
        await message.answer(text=f'Действие отменено.\n',
                             reply_markup=ReplyKeyboardRemove())
    await state.clear()
