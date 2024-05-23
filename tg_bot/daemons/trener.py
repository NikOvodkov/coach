# демон пробегается по бд пользователей и проверяет, не пора ли в соответствии с настройками
# послать данному пользоватлею очередной календарь жизни
# демон должен слать сообщения только в дневное время 12-00 до 18-00 по текущему часовому поясу
import asyncio
import os
from datetime import datetime, timedelta, time
from pathlib import Path

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile

from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.keyboards.life_calendar import yesno
from tg_bot.states.life_calendar import FSMLifeCalendar
from tg_bot.utils.life_calendar import generate_text_calendar, generate_image_calendar


def is_daytime(user):
    time_zone = user[6]
    if time(hour=10) < (datetime.utcnow() + timedelta(hours=int(time_zone or 0))).time() < time(hour=18):
        return True
    else:
        return False


async def auto_trener(db: SQLiteDatabase, bot: Bot, dp: Dispatcher):
    """Подготавливает тренировку, предварительно проанализировав проведенные ранее тренировки.
    Алгоритм: находим самую мало проработанную группу мышц за неделю по количеству выполненной ими относительной работы
    1) считаем 

    """
    while True:
        # records = db.select_all_users()
        records = db.select_all_table('Users')
        for row in records:
            if row[6] and is_daytime(row):
                if (datetime.now() - datetime.fromisoformat(row[6])) >= timedelta(days=7):
                    path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
                    lived_weeks = await generate_image_calendar(row[4], row[5], 'week', path)
                    if lived_weeks % 52 == 0:
                        year = round((lived_weeks * 7) / 365.25)
                        os.remove(path)
                        path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
                        await generate_image_calendar(row[4], row[5], 'year', path)
                        await bot.send_photo(row[0], photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                             caption=f'Очередная год закончился, встречайте год {year + 1}!')
                    elif lived_weeks % 5 == 0:
                        month = round((lived_weeks * 7) / 30.4375)
                        os.remove(path)
                        path = str(Path.cwd() / Path('tg_bot', 'utils', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
                        await generate_image_calendar(row[4], row[5], 'month', path)
                        await bot.send_photo(row[0], photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                             caption=f'Прошёл очередной месяц, встречайте месяц {month + 1}!')
                    else:
                        await bot.send_photo(row[0], photo=FSInputFile(path), reply_markup=ReplyKeyboardRemove(),
                                             caption=f'Очередная неделя подходит к концу, встречайте неделю {lived_weeks + 1}!')

                    db.update_cell(table='Users', cell='life_calendar', cell_value=None, key='user_id', key_value=row[0])
                    os.remove(path)
                    await dp.storage.set_state(StorageKey(bot_id=bot.id, chat_id=row[0], user_id=row[0]),
                                               state=FSMLifeCalendar.confirm_geo)
                    await bot.send_message(row[0], text='Прислать календарь через неделю? (Да/Нет)', reply_markup=yesno)

        await asyncio.sleep(300)
