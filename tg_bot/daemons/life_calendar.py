# демон пробегается по бд пользователей и проверяет, не пора ли в соответствии с настройками
# послать данному пользоватлею очередной календарь жизни
# демон должен слать сообщения только в дневное время 12-00 до 18-00 по текущему часовому поясу
import asyncio
import os
from datetime import datetime, timedelta, time
from pathlib import Path

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, ReplyKeyboardMarkup, KeyboardButton

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.keyboards.life_calendar import yesno
from tg_bot.states.life_calendar import FSMLifeCalendar
from tg_bot.utils.life_calendar import generate_text_calendar, generate_image_calendar


def is_daytime(user):
    time_zone = user[6]
    if time(hour=10) < (datetime.utcnow() + timedelta(hours=int(time_zone or 0))).time() < time(hour=20):
        return True
    else:
        return False


async def send_life_calendar(db: SQLiteDatabase, bot: Bot, dp: Dispatcher):
    while True:
        logger.debug(f'enter_while_life_calendar')
        records = db.select_all_table('users_base_long', new=True)
        for row in records:
            if row[10] and is_daytime(row) and row[3] == 1:
                if (datetime.now() - datetime.fromisoformat(row[10])) >= timedelta(days=7):
                    db.update_cell(table='users_base_long', cell='trener_sub', cell_value=None,
                                   key='user_id', key_value=row[0], new=True)
                    await bot.send_message(row[0],
                                           text='Вы не занимались уже 7 дней, достигнутый прогресс скоро начнёт уходить!',
                                           reply_markup=ReplyKeyboardMarkup(
                                               keyboard=[[KeyboardButton(text="Запустить тренировку")],
                                                         [KeyboardButton(text="Напомнить через неделю")],
                                                         [KeyboardButton(text="Отписаться от напоминаний")]],
                                               one_time_keyboard=True, resize_keyboard=True))
                    # await dp.storage.set_state(StorageKey(bot_id=bot.id, chat_id=row[0], user_id=row[0]),
                    #                            state=FSMLifeCalendar.confirm_geo)
            if row[9] and is_daytime(row) and row[3] == 1:
                if (datetime.now() - datetime.fromisoformat(row[9])) >= timedelta(days=7):
                    path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
                    lived_weeks = await generate_image_calendar(row[7], row[8], 'week', path)
                    if lived_weeks % 52 == 0:
                        year = round((lived_weeks * 7) / 365.25)
                        os.remove(path)
                        path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
                        await generate_image_calendar(row[7], row[8], 'year', path)
                        await bot.send_photo(row[0], photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                             caption=f'Очередной год закончился, встречайте год {year + 1}!')
                    elif lived_weeks % 5 == 0:
                        month = round((lived_weeks * 7) / 30.4375)
                        os.remove(path)
                        path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
                        await generate_image_calendar(row[7], row[8], 'month', path)
                        await bot.send_photo(row[0], photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                             caption=f'Прошёл очередной месяц, встречайте месяц {month + 1}!')
                    else:
                        await bot.send_photo(row[0], photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                             caption=f'Очередная неделя подходит к концу, встречайте неделю {lived_weeks + 1}!')

                    db.update_cell(table='users_base_long', cell='life_calendar_sub', cell_value=None,
                                   key='user_id', key_value=row[0], new=True)
                    os.remove(path)
                    await dp.storage.set_state(StorageKey(bot_id=bot.id, chat_id=row[0], user_id=row[0]),
                                               state=FSMLifeCalendar.confirm_geo)
                    await bot.send_message(row[0], text='Прислать календарь через неделю? (Да/Нет)', reply_markup=yesno)
        # await asyncio.sleep(10)
        await asyncio.sleep(300)
