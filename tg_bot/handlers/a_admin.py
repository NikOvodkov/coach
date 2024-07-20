import sqlite3
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommandScopeChat, CallbackQuery

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.keyboards.inline import keyboard
from tg_bot.services.setting_commands import set_admins_commands, set_chat_admins_commands
from tg_bot.config import load_config

router = Router()

# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


@router.message(Command('start'))
async def admin_start(message: Message, db: SQLiteDatabase, state: FSMContext):
    name = message.from_user.full_name
    user_id = message.from_user.id
    cur_state = await state.get_state()
    cur_data = await state.get_data()
    if cur_state or cur_data:
        await message.answer(text=f'State is not None: {cur_state} data= {cur_data}')
        logger.debug(f'{message=}')
        await state.clear()
    await set_admins_commands(message.bot, user_id)
    try:
        db.add_user(user_id=user_id, name=name)
    except sqlite3.IntegrityError as err:
        # print(err)
        logger.exception(f'User {name=} {user_id=} not added to db!')
    finally:
        count_users = db.count_rows('users')[0]
        await message.answer(
            '\n'.join([
                f'Привет, админ {message.from_user.full_name}!',
                f'Ты был занесён в базу',
                f'В базе <b>{count_users}</b> пользователей'
            ]), reply_markup=keyboard)


# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'big_button_1_pressed'
@router.callback_query(F.data == 'big_button_1_pressed')
async def process_button_1_press(callback: CallbackQuery):
    if callback.message.text != 'Была нажата БОЛЬШАЯ КНОПКА 1':
        await callback.message.edit_text(
            text='Была нажата БОЛЬШАЯ КНОПКА 1',
            reply_markup=callback.message.reply_markup
        )
    await callback.answer()


# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'big_button_2_pressed'
@router.callback_query(F.data == 'big_button_2_pressed')
async def process_button_2_press(callback: CallbackQuery):
    if callback.message.text != 'Была нажата БОЛЬШАЯ КНОПКА 2':
        await callback.message.edit_text(
            text='Была нажата БОЛЬШАЯ КНОПКА 2',
            reply_markup=callback.message.reply_markup
        )
    await callback.answer()

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
