"""
Задача модуля регистрации:
1) получить данные от пользователя;
2) ограничить число пользователей и создать воронку продаж

ВОРОНКА ПРОДАЖ
10 бесплатных активных пользователей (неактивных более 2 месяцев переводить на платный тариф)
3 бесплатных активных тренера и по 10 бесплатных активных пользователей у каждого
остальным предлагать подождать бесплатный слот или заплатить 100р/месяц или 1000р/год
"""
import asyncio
import sqlite3
from datetime import datetime, timedelta

import dateutil
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

from logging_settings import logger
from tg_bot.config import Config
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.db import MyUserDbFilter, FirstDayLaunch
from tg_bot.keyboards.trener import yesno
from tg_bot.states.life_calendar import FSMLifeCalendar
from tg_bot.states.trener import FSMCoach, FSMTrener
from tg_bot.utils.trener import run_warmup

router = Router()


@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMLifeCalendar.enter_date_opt))
@router.message(F.text.lower().strip() == 'запустить тренировку')
@router.message(Command(commands='fitness'), MyUserDbFilter(columns=['time_zone', 'birth_date', 'weight', 'height', 'sex']))
# @router.message(Command(commands='fitness'), MyUserDbFilter(columns=['time_zone', 'birth_date', 'weight', 'height', 'sex']), FirstDayLaunch())
async def warmup_07new(message: Message, state: FSMContext, db: SQLiteDatabase):
    logger.debug(f'enter command fitness')
    if message.text == '/fitness':
        await state.clear()
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    logger.debug(f'{data["delete_list"]=}')
    data = await run_warmup(data, db, message)
    data['delete_list'].append(message.message_id)
    logger.debug(f'{data["delete_list"]=}')
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=[])
    await state.set_state(FSMTrener.show_exercises)


@router.message(Command(commands='fitness'))
@router.message(CommandStart())
async def coach_start(message: Message, command: CommandObject, db: SQLiteDatabase, state: FSMContext, config: Config):
    args = command.args
    logger.warning(f'enter_coach_start {args=}')
    user_id = message.from_user.id
    name = message.from_user.full_name
    # if message.text.startswith('/start'):
    #     await message.answer(text=f'Ваши аргументы: {args=}', reply_markup=ReplyKeyboardRemove())
    try:
        user_db = db.select_rows(table='users', fetch='one', user_id=user_id)
        if user_db:
            if args.isdigit() and user_db['referrer'] is None:
                db.update_cells(table='users', cells={'referrer': args}, user_id=message.from_user.id)
            await state.clear()
            if message.text.startswith('/start'):
                await message.answer(text='Приложение сброшено в исходное состояние.', reply_markup=ReplyKeyboardRemove())
            if not (user_db['weight'] and user_db['height'] and user_db['sex']
                    and user_db['time_zone'] and user_db['birth_date']):
                await message.answer(text='Не хватает данных для работы приложения!',
                                     reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Ввести')]],
                                                                      one_time_keyboard=True, resize_keyboard=True))
                await state.set_state(FSMCoach.input_shw)
        else:
            db.add_user(user_id=user_id, name=name)
            if args.isdigit():
                db.update_cells(table='users', cells={'referrer': args}, user_id=message.from_user.id)
            await message.forward(config.tg_bot.admin_ids[0])
            await message.answer(text='Приветствуем вас! Для работы с приложением потребуется пройти короткую регистрацию.',
                                 reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Хорошо')]],
                                                                  one_time_keyboard=True, resize_keyboard=True))
            await state.set_state(FSMCoach.input_shw)
    except sqlite3.IntegrityError as err:
        logger.exception(f'User {name=} {user_id=} has error with db: {err}')
        await message.answer(text='Произошла ошибка БД, обратитесь к администратору!', reply_markup=ReplyKeyboardRemove())


@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMCoach.input_birth_date))
@router.message(F.text.strip().lower() == 'хорошо', StateFilter(FSMCoach.input_shw))
@router.message(F.text.strip().lower() == 'ввести', StateFilter(FSMCoach.input_shw))
async def input_shw(message: Message, state: FSMContext):
    await message.answer(text='Для индивидуального расчёта нагрузок необходимо ввести ваш пол, рост и вес. '
                              'Пол может быть только М или Ж, выберите, какой вам больше подходит. '
                              'Рост и вес - ЦЕЛЫЕ положительные числа.\n'
                              'Введите через пробел ваш пол, рост и вес, например Ж 170 70: ',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMCoach.input_shw_2)


@router.message(F.text, StateFilter(FSMCoach.input_shw_2))
async def enter_data_05new(message: Message, state: FSMContext):
    shw = message.text.upper().strip().split()
    await asyncio.sleep(1)
    await message.answer(text=f'Подтвердите, ваш пол {shw[0]}, рост {shw[1]}, вес {shw[2]} : ',
                         reply_markup=yesno)
    await state.update_data(shw=shw)
    await state.set_state(FSMCoach.input_birth_date)


@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMCoach.input_geo))
@router.message(F.text.lower().strip() == 'да', StateFilter(FSMCoach.input_birth_date))
async def input_birth_date(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'shw' in data:
        db.update_cells(table='users', cells={'sex': data['shw'][0],
                                              'height': data['shw'][1],
                                              'weight': data['shw'][2]},
                        user_id=message.from_user.id)
    await message.answer(text='Для учёта возраста при подборе тренировочной программы '
                              'введите через пробел дату вашего рождения, в формате 22 06 1990: ',
                         reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(1)
    await state.set_state(FSMCoach.input_birth_date_2)


@router.message(F.text, StateFilter(FSMCoach.input_birth_date_2))
async def input_birth_date_2(message: Message, state: FSMContext):
    birth_date = dateutil.parser.parse(message.text, fuzzy=True)
    await message.answer(text=f'Подтвердите, ваша дата рождения {birth_date.strftime("%d-%m-%Y")} ? ',
                         reply_markup=yesno)
    await asyncio.sleep(1)
    await state.update_data(birth_date=datetime.isoformat(birth_date))
    await state.set_state(FSMCoach.input_geo)


@router.message(F.text.lower().strip() == 'да', StateFilter(FSMCoach.input_geo))
async def input_geo(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'birth_date' in data:
        # добавим также дату жизни
        # для этого вычисляем возраст пользователя в днях
        age_days = (datetime.now() - datetime.fromisoformat(data['birth_date'])).days
        # если больше 59 лет, записываем конечную дату как +15 лет к текущей
        if age_days > 21700:
            life_date = datetime.isoformat(timedelta(weeks=780) + datetime.now())
        else:
            life_date = datetime.isoformat(timedelta(weeks=3652) + datetime.fromisoformat(data['birth_date']))
        db.update_cells(table='users', cells={'birth_date': data['birth_date'], 'life_date': life_date},
                        user_id=message.from_user.id)
    await message.answer(text='Чтобы уведомления от приложения приходили в дневное время, для расчёта вашего часового пояса '
                              'потребуется подтвердить своё местоположение (геопозицию). \n',
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text='Подтвердить', request_location=True)],
                                       [KeyboardButton(text='Ввести часовой пояс вручную')]],
                             one_time_keyboard=True, resize_keyboard=True))
    await asyncio.sleep(1)
    await state.set_state(FSMCoach.input_geo_2)


@router.message(F.location, StateFilter(FSMCoach.input_geo_2))
async def input_geo_2(message: Message, state: FSMContext):
    time_zone = round(message.location.longitude / 15)
    await message.answer(text=f'Ваш часовой пояс {time_zone}? Если вы не знаете, нажмите "Да".', reply_markup=yesno)
    await asyncio.sleep(1)
    await state.update_data(time_zone=time_zone)
    await state.set_state(FSMCoach.input_geo_3)


@router.message(F.text.lower().strip() == 'да', StateFilter(FSMCoach.input_geo_3))
async def input_geo_31(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    if 'time_zone' in data:
        if message.location:
            db.update_cells(table='users', cells={'time_zone': data['time_zone'],
                                                  'latitude': message.location.latitude,
                                                  'longitude': message.location.longitude},
                            user_id=message.from_user.id)
        else:
            db.update_cells(table='users', cells={'time_zone': data['time_zone']},
                            user_id=message.from_user.id)
    await message.answer(text=f'Хотите увидеть календарь жизни, сгенерированный на основе вашей даты рождения?',
                         reply_markup=yesno)
    await state.set_state(FSMLifeCalendar.enter_date_opt)
    # data = await run_warmup(data, db, message)
    # await state.update_data(delete_list=data['delete_list'])
    # await state.update_data(black_list=[])
    # await state.update_data(new_workout=[])
    # await state.set_state(FSMTrener.show_exercises)


@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMCoach.input_geo_3))
@router.message(F.text.lower().strip() == 'ввести часовой пояс вручную', StateFilter(FSMCoach.input_geo_2))
async def input_geo_32(message: Message, state: FSMContext):
    await message.answer(text=f'Введите ваш часовой пояс:', reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMCoach.input_geo_4)


@router.message(F.text.strip().isdigit(), StateFilter(FSMCoach.input_geo_4))
async def input_geo_4(message: Message, state: FSMContext):
    time_zone = int(message.text.strip())
    await message.answer(text=f'Подтвердите, ваш часовой пояс  {time_zone}?', reply_markup=yesno)
    await asyncio.sleep(1)
    await state.update_data(time_zone=time_zone)
    await state.set_state(FSMCoach.input_geo_3)
