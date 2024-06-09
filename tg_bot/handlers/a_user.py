import sqlite3

from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ChatMemberUpdated
from aiogram.filters import Command, CommandStart, StateFilter, ChatMemberUpdatedFilter, KICKED, MEMBER

from logging_settings import logger
from tg_bot.config import Config
from tg_bot.database.sqlite2 import SQLiteDatabase
from tg_bot.lexicon.a_user import LEXICON_RU
from tg_bot.services.setting_commands import set_starting_commands
from tg_bot.states.user import FSMUser

# Инициализируем роутер уровня модуля
router = Router()


# Этот хэндлер срабатывает на команду /start
@router.message(CommandStart())
async def process_start_command(message: Message, db: SQLiteDatabase, state: FSMContext, config: Config):

    await state.clear()
    await set_starting_commands(message.bot, message.from_user.id)
    name = message.from_user.full_name
    user_id = message.from_user.id
    try:
        db.add_user(user_id=user_id, name=name)
        await message.forward(config.tg_bot.admin_ids[0])
    except sqlite3.IntegrityError as err:
        # print(err)
        logger.exception(f'User {name=} {user_id=} not added to db!')
    finally:
        await message.answer(text=LEXICON_RU['/start'], reply_markup=ReplyKeyboardRemove())


# Этот хэндлер срабатывает на команду /about
@router.message(Command(commands='about'))
async def process_about_command(message: Message):
    await message.answer(text=LEXICON_RU['/about'], reply_markup=ReplyKeyboardRemove())


# Этот хэндлер срабатывает на команду /help
@router.message(Command(commands='help'))
async def process_help_command(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_RU['/help'], reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMUser.user_help)


@router.message(StateFilter(FSMUser.user_help))
async def enter_message(message: Message, state: FSMContext, config: Config):
    await message.forward(config.tg_bot.admin_ids[0])
    await message.answer(text=LEXICON_RU['help'])
    await state.clear()


# Этот хэндлер будет срабатывать на блокировку бота пользователем
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated, bot: Bot, config: Config, db: SQLiteDatabase):
    await bot.send_message(config.tg_bot.admin_ids[0],
                           text=f'Пользователь {event.from_user.id} {event.from_user.username} заблокировал бота')
    try:
        db.update_cell(table='users', cell='status', cell_value=0, key='user_id', key_value=event.from_user.id)
    except sqlite3.IntegrityError as err:
        # print(err)
        logger.exception(err)


# Этот хэндлер будет срабатывать на разблокировку бота пользователем
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def process_user_unblocked_bot(event: ChatMemberUpdated, bot: Bot, config: Config, db: SQLiteDatabase):
    await bot.send_message(config.tg_bot.admin_ids[0],
                           text=f'Пользователь {event.from_user.id} {event.from_user.username} разблокировал бота')
    try:
        db.update_cell(table='users', cell='status', cell_value=1, key='user_id', key_value=event.from_user.id)
    except sqlite3.IntegrityError as err:
        # print(err)
        logger.exception(err)
