import sqlite3
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommandScopeChat

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.services.setting_commands import set_admins_commands, set_chat_admins_commands
from tg_bot.config import load_config

router = Router()

# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


@router.message(Command('start'))
async def admin_start(message: Message, db: SQLiteDatabase, state: FSMContext):
    cur_state = await state.get_state()
    if cur_state:
        await message.answer(text=f'State is not None: {cur_state}')
        await state.clear()
    await set_admins_commands(message.bot, message.from_user.id)
    name = message.from_user.full_name
    try:
        db.add_user(user_id=message.from_user.id, name=name)
    except sqlite3.IntegrityError as err:
        # print(err)
        logger.exception(err)
    # count_users = db.count_users()[0]
    count_users = db.count_rows('Users')[0]
    await message.answer(
        '\n'.join([
            f'Привет, админ {message.from_user.full_name}!',
            f'Ты был занесён в базу',
            f'В базе <b>{count_users}</b> пользователей'
        ]))


def quote_html(arg):
    pass


@router.message(Command('get_commands'))
async def message_get_commands(message: Message):
    no_lang = await message.bot.get_my_commands(scope=BotCommandScopeChat(chat_id=message.from_user.id))
    no_args = await message.bot.get_my_commands()
    en_lang = await message.bot.get_my_commands(scope=BotCommandScopeChat(chat_id=message.from_user.id),
                                                language_code='en')
    await message.reply('\n\n'.join(
        f'<pre>{quote_html(arg)=}</>' for arg in (no_lang, no_args, en_lang)
    ))


@router.message(Command('reset_commands'))
async def message_reset_commands(message: Message):
    await message.bot.delete_my_commands(BotCommandScopeChat(chat_id=message.from_user.id), language_code='en')
    await message.reply('Команды были удалены')


@router.message(Command('change_commands'))
async def change_admin_commands(message: Message):
    await set_chat_admins_commands(message.bot, message.chat.id)
    await message.answer('Команды администраторов для этого чата были изменены.')
