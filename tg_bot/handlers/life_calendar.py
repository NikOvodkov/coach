import asyncio
import os
from datetime import timedelta, datetime
from pathlib import Path

import dateutil
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, ReplyKeyboardMarkup, KeyboardButton

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.keyboards.life_calendar import yesno, geono
from tg_bot.lexicon.life_calendar import LEXICON_RU
from tg_bot.utils.life_calendar import generate_image_calendar
from tg_bot.states.life_calendar import FSMLifeCalendar

# Инициализируем роутер уровня модуля
router = Router()


@router.message(Command(commands='life_calendar'))
async def start_life_calendar(message: Message, state: FSMContext, db: SQLiteDatabase):
    # при входе в сервис Календарь жизни отправляем приветствие
    await message.answer(text=LEXICON_RU['life_calendar_0'])
    # находим пользователя в бд
    user = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
    # если в бд указана дата рождения, то просим её подтвердить
    if user['birth_date']:
        date = datetime.fromisoformat(user['birth_date']).strftime('%d-%m-%Y')
        await message.answer(f'{LEXICON_RU["life_calendar_1"]}{date}{LEXICON_RU["life_calendar_2"]}', reply_markup=yesno)
        await state.set_state(FSMLifeCalendar.confirm_date)
        await asyncio.sleep(1)  # иначе следующий хэндлер может не успеть сработать
    else:
        # иначе просим её ввести
        await message.answer(text=LEXICON_RU['life_calendar_3'], reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMLifeCalendar.enter_date)


@router.message(StateFilter(FSMLifeCalendar.confirm_date))
async def confirm_date(message: Message, state: FSMContext):
    # если дата рождения в бд подтверждена, предлагаем отправить календарь
    if message.text.lower().strip() == 'да':
        await message.answer(text=LEXICON_RU['confirm_date_0'], reply_markup=yesno)
        await state.set_state(FSMLifeCalendar.no_enter_date)
    else:
        # иначе просим ввести дату рождения
        await message.answer(text=LEXICON_RU['confirm_date_11'], reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMLifeCalendar.enter_date)


@router.message(F.text.lower().strip() == 'да', StateFilter(FSMLifeCalendar.no_enter_date))
async def no_enter_date(message: Message, state: FSMContext, db: SQLiteDatabase):
    # если пользователь согласен получить календарь, формируем его, отправляем и удаляем с сервера
    user = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
    path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
    logger.debug(f'{path=}')
    lived_weeks = await generate_image_calendar(user['birth_date'], user['life_date'], 'week', path)
    # если пользователь подписан на еженедельную рассылку календаря, обнуляем состояние
    if user['life_calendar_sub']:
        await message.answer_photo(photo=FSInputFile(path), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Запустить тренировку')]],
            one_time_keyboard=True, resize_keyboard=True),
                                   caption=f'Сейчас идёт неделя {lived_weeks + 1}')
        os.remove(path)
        await state.clear()
    # если нет, предлагаем подписаться
    else:
        await message.answer_photo(photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                   caption=f'Сейчас идёт неделя {lived_weeks + 1}')
        os.remove(path)
        # если в бд есть координаты пользователя, просим его подтвердить часовой пояс
        if user['time_zone']:
            await state.set_state(FSMLifeCalendar.confirm_geo)
            await message.answer(text=LEXICON_RU['no_enter_date_0'], reply_markup=yesno)
        # иначе просим отправить координаты
        else:
            await state.set_state(FSMLifeCalendar.everyweek_order)
            await message.answer(text=LEXICON_RU['no_enter_date_1'], reply_markup=geono)


@router.message(StateFilter(FSMLifeCalendar.enter_date))
async def enter_date(message: Message, state: FSMContext, db: SQLiteDatabase):
    # обрабатываем полученную дату рождения и сохраняем её в бд
    user = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
    # date = '-'.join(message.text.split())
    # дату можно считать одним из двух парсеров, но оба не поддерживают дату без разделителей типа '22071999'
    date = dateutil.parser.parse(message.text, fuzzy=True)
    # date = list(datefinder.find_dates(message.text))[0]
    # date = date.strftime('%Y-%m-%d')
    date = datetime.isoformat(date)
    # print(date)
    logger.debug(date)
    # date = datetime.strptime(date, '%d-%m-%Y').strftime('%Y-%m-%d')
    db.update_cell(table='users', cell='birth_date', cell_value=date, key='user_id', key_value=message.from_user.id)
    # вычисляем возраст пользователя в днях
    age_days = (datetime.now() - datetime.fromisoformat(date)).days
    # если больше 59 лет, записываем конечную дату как +10 лет к текущей
    if age_days > 21700:
        life_date = datetime.isoformat(timedelta(weeks=520) + datetime.now())
    else:
        life_date = datetime.isoformat(timedelta(weeks=3652) + datetime.fromisoformat(date))
    db.update_cell(table='users', cell='life_date', cell_value=life_date, key='user_id', key_value=message.from_user.id)
    # await message.answer(text=LEXICON_RU['enter_date_0'])
    await message.answer(text=LEXICON_RU['enter_date_00'])
    await state.set_state(FSMLifeCalendar.oldster_enter_date)


@router.message(F.text.lower().strip() == 'да', StateFilter(FSMLifeCalendar.enter_date_opt))
async def enter_date(message: Message, state: FSMContext, db: SQLiteDatabase):
    await message.answer(text='Сколько ещё лет активной жизни вы для себя планируете? Напишите число: ')
    await state.set_state(FSMLifeCalendar.oldster_enter_date)


@router.message(StateFilter(FSMLifeCalendar.oldster_enter_date))
async def oldster_enter_date(message: Message, state: FSMContext, db: SQLiteDatabase):
    user = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
    date = user['birth_date']
    life_date = message.text.strip()
    if life_date.isdigit():
        life_date = datetime.isoformat(timedelta(weeks=int(life_date) * 52.1786) + datetime.now())
        db.update_cell(table='users', cell='life_date', cell_value=life_date, key='user_id', key_value=message.from_user.id)
        path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
        logger.debug(f'{path=}')
        lived_weeks = await generate_image_calendar(date, life_date, 'week', path)
        if user['life_calendar_sub']:
            await message.answer_photo(photo=FSInputFile(path), reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text='Запустить тренировку')]],
                one_time_keyboard=True, resize_keyboard=True),
                                       caption=f'Сейчас идёт неделя {lived_weeks + 1}')
            os.remove(path)
            await state.clear()
        else:
            await message.answer_photo(photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                       caption=f'Сейчас идёт неделя {lived_weeks + 1}')
            os.remove(path)
            if user['time_zone']:
                await state.set_state(FSMLifeCalendar.confirm_geo)
                await message.answer(text=LEXICON_RU['oldster_enter_date_0'], reply_markup=yesno)
            else:
                await state.set_state(FSMLifeCalendar.everyweek_order)
                await message.answer(text=LEXICON_RU['oldster_enter_date_1'], reply_markup=geono)

    else:
        await state.clear()
        await message.answer(text=LEXICON_RU['oldster_enter_date_2'], reply_markup=ReplyKeyboardRemove())


@router.message(StateFilter(FSMLifeCalendar.confirm_geo))
async def confirm_geo(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.text.lower().strip() == 'да':
        user = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
        await state.set_state(FSMLifeCalendar.confirm_geo_process)
        await message.answer(text=f'{LEXICON_RU["confirm_geo_0"]}{user["time_zone"]}{LEXICON_RU["confirm_geo_1"]}', reply_markup=yesno)
    else:
        db.update_cell(table='users', cell='life_calendar_sub', cell_value=None, key='user_id', key_value=message.from_user.id)
        await message.answer(text=LEXICON_RU["confirm_geo_2"], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Запустить тренировку')]],
            one_time_keyboard=True, resize_keyboard=True))
        await state.clear()


@router.message(StateFilter(FSMLifeCalendar.confirm_geo_process))
async def confirm_geo_process(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.text.lower().strip() == 'да':
        db.update_cell(table='users', cell='life_calendar_sub',
                       cell_value=datetime.now().isoformat(),
                       key='user_id', key_value=message.from_user.id)
        await message.answer(text=LEXICON_RU["confirm_geo_process_0"], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Запустить тренировку')]],
            one_time_keyboard=True, resize_keyboard=True))
        await state.clear()
    else:
        await message.answer(text=LEXICON_RU['confirm_geo_process_1'], reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMLifeCalendar.change_timezone)


@router.message(StateFilter(FSMLifeCalendar.change_timezone))
async def change_timezone(message: Message, state: FSMContext, db: SQLiteDatabase):
    time_zone = int(message.text)
    db.update_cell(table='users', cell='time_zone', cell_value=time_zone, key='user_id', key_value=message.from_user.id)
    db.update_cell(table='users', cell='life_calendar_sub',
                   cell_value=datetime.now().isoformat(),
                   key='user_id', key_value=message.from_user.id)
    await message.answer(text=LEXICON_RU["change_timezone"], reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Запустить тренировку')]],
        one_time_keyboard=True, resize_keyboard=True))
    await state.clear()


@router.message(StateFilter(FSMLifeCalendar.everyweek_order), F.location)
async def everyweek_order_geo(message: Message, state: FSMContext, db: SQLiteDatabase):
    time_zone = round(message.location.longitude / 15)
    db.update_cell(table='users', cell='time_zone', cell_value=time_zone, key='user_id', key_value=message.from_user.id)
    db.update_cell(table='users', cell='latitude', cell_value=message.location.latitude,
                   key='user_id', key_value=message.from_user.id)
    db.update_cell(table='users', cell='longitude', cell_value=message.location.longitude,
                   key='user_id', key_value=message.from_user.id)
    await state.set_state(FSMLifeCalendar.confirm_geo_process)
    await message.answer(text=f'{LEXICON_RU["everyweek_order_0"]}{time_zone}{LEXICON_RU["everyweek_order_1"]}',
                         reply_markup=yesno)
    # db.update_life_calendar(life_calendar=datetime.now().strftime('%Y-%m-%d'), id=message.from_user.id)
    # await message.answer('Включили вас в рассылку.')
    # await state.reset_state(with_data=False)


@router.message(StateFilter(FSMLifeCalendar.everyweek_order))
async def everyweek_order_repeat_no(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.text.lower().strip() == 'да':
        db.update_cell(table='users', cell='life_calendar_sub',
                       cell_value=datetime.now().isoformat(),
                       key='user_id', key_value=message.from_user.id)
        await message.answer(text=LEXICON_RU['everyweek_order_2'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Запустить тренировку')]],
            one_time_keyboard=True, resize_keyboard=True))
    else:
        db.update_cell(table='users', cell='life_calendar_sub', cell_value=None, key='user_id', key_value=message.from_user.id)
        await message.answer(text=LEXICON_RU['everyweek_order_3'], reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Запустить тренировку')]],
            one_time_keyboard=True, resize_keyboard=True))
    await state.clear()
