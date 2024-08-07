import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from openai import OpenAI
from pyrogram import Client

from autorun import return_bot_status, print_telegram
from logging_settings import logger
from tg_bot.config import load_config, Config
from tg_bot.daemons.life_calendar import send_life_calendar

from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.handlers import a_user, a_other, a_admin, atomy, gsheet, life_calendar, update_db_sqlite, energy_balance, trener_moderate, coach_add, coach_workout, coach_account, coach_registration
from tg_bot.middlewares.shadow_ban import ShadowBanMiddleware
from tg_bot.middlewares.throttling import ThrottlingMiddleware
from tg_bot.services.setting_commands import force_reset_all_commands, set_default_commands, set_admins_commands, set_all_groups_commands, set_all_chat_admins_commands, set_all_private_commands
from aiogram.fsm.storage.redis import RedisStorage, Redis


async def set_all_default_commands(bot: Bot, config: Config):
    await force_reset_all_commands(bot)
    await set_default_commands(bot)
    await set_admins_commands(bot, config.tg_bot.admin_ids[0])
    await set_all_groups_commands(bot)
    await set_all_chat_admins_commands(bot)
    await set_all_private_commands(bot)


async def on_startup_notify(bot: Bot, config: Config):
    for admin in config.tg_bot.admin_ids:
        try:
            await bot.send_message(admin, "Бот Запущен и готов к работе", reply_markup=ReplyKeyboardRemove())
        except Exception as err:
            logger.exception(err)


async def daemons(bot, db, dp):
    await send_life_calendar(db, bot, dp)


async def writelog(dp: Dispatcher):
    while True:
        await asyncio.sleep(120)
        logger.info('Bot is working.')
        dp['autorun_was_working'] = dp['autorun_is_working']
        dp['autorun_is_working'] = return_bot_status('autorun.txt', 300)
        if dp['autorun_is_working'] != dp['autorun_was_working']:
            if dp['autorun_is_working']:
                logger.info('Nib: autorun zarabotal')
                await print_telegram('Nib: autorun zarabotal')
            else:
                logger.info('Nib: autorun ostanovilsya')
                await print_telegram('Nib: autorun ostanovilsya')


def get_storage(config):
    """
    Return storage based on the provided configuration.

    Args:
        config (Config): The configuration object.

    Returns:
        Storage: The storage object based on the configuration.

    """
    if config.tg_bot.use_redis:
        return RedisStorage(redis=Redis(host='localhost'))
    else:
        return MemoryStorage()


async def main():
    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')
    # Загружаем конфиг в переменную config
    config: Config = load_config('.env')
    # Инициализируем объект хранилища
    storage = get_storage(config)
    # Инициализируем бот и диспетчер
    aiobot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)
    ai = OpenAI(api_key=config.ai.token, base_url="https://api.proxyapi.ru/openai/v1")
    # Инициализируем другие объекты (пул соединений с БД, кеш и т.п.)
    db = SQLiteDatabase()
    try:
        logger.info('Создаём подключение к базе данных')

        # разовые коррекции БД:
        # db.regenerate_approaches()

        # db.delete_table('exercises_muscles')
        # db.update_cells(table='exercises', cells={'type': 2}, exercise_id=2)
        # db.update_cells(table='exercises', cells={'type': 2}, exercise_id=6)
        # db.update_cells(table='exercises', cells={'type': 2}, exercise_id=7)
        # db.update_cells(table='exercises', cells={'type': 2}, exercise_id=9)
        # db.update_cells(table='exercises', cells={'type': 2}, exercise_id=26)
        # db.add_type_exercises_users()

    except Exception as e:
        logger.exception(e)
    # создаем клиент пирограм
    pyrobot = Client("me_client",
                     api_id=config.tg_bot.api_id,
                     api_hash=config.tg_bot.api_hash,
                     phone_number=config.tg_bot.phone_number,
                     plugins=dict(root='tg_bot/handlers'))
    # Помещаем нужные объекты в workflow_data диспетчера
    dp['config'] = config
    dp['db'] = db
    dp['bot'] = aiobot
    dp['ai'] = ai
    if return_bot_status('autorun.txt', 300):
        logger.info('Nib: autorun rabotaet')
        await print_telegram('Nib: autorun rabotaet')
        dp['autorun_is_working'] = True
    else:
        logger.info('Nib: autorun ne rabotaet')
        await print_telegram('Nib: autorun ne rabotaet')
        dp['autorun_is_working'] = False
    # Настраиваем главное меню бота
    # await set_main_menu(bot)
    await set_all_default_commands(aiobot, config)
    # Регистриуем роутеры
    logger.info('Подключаем роутеры')
    dp.include_routers(a_admin.router,
                       trener_moderate.router,
                       coach_add.router,
                       update_db_sqlite.router,
                       energy_balance.router,
                       a_user.router,
                       atomy.router,
                       gsheet.router,
                       life_calendar.router,
                       coach_account.router,
                       coach_workout.router,
                       coach_registration.router,
                       a_other.router)
    # Регистрируем миддлвари
    logger.info('Подключаем миддлвари')
    dp.update.middleware(ShadowBanMiddleware())
    dp.update.middleware(ThrottlingMiddleware())
    await on_startup_notify(aiobot, config)
    # print(await aiobot.get_webhook_info())

    task1 = asyncio.create_task(dp.start_polling(aiobot))
    task2 = asyncio.create_task(writelog(dp=dp))
    task3 = asyncio.create_task(daemons(bot=aiobot, db=db, dp=dp))
    task4 = asyncio.create_task(pyrobot.start())

    await task1
    await task2
    await task3
    await task4


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error('Bot stopped!')
