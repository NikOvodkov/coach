from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logging_settings import logger
from tg_bot.config import load_config
from tg_bot.database.sqlite2 import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.states.update_db import FSMUpdateDb

router = Router()

# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


@router.message(Command(commands='email'))
async def add_email(message: Message, state: FSMContext):
    await message.answer('Пришли мне свой имейл')
    await state.set_state(FSMUpdateDb.email)


@router.message(StateFilter(FSMUpdateDb.email))
async def enter_email(message: Message, state: FSMContext, db: SQLiteDatabase):
    email = message.text
    db.update_cell(table='users', cell='email', cell_value=email, key='user_id', key_value=message.from_user.id)
    # user = db.select_user(user_id=message.from_user.id)
    user = db.select_rows(table='users', fetch='one', tuple_=True, user_id=message.from_user.id)
    await message.answer(f'Данные были обновлены. Запись в бд: {user}')
    await state.clear()


@router.message(Command(commands='sql_db'))
async def update_db(message: Message, state: FSMContext, db: SQLiteDatabase):
    await message.answer('Введите SQL команду: ')
    await state.set_state(FSMUpdateDb.update_db)


@router.message(Command(commands='show_table'))
async def update_db(message: Message, state: FSMContext, db: SQLiteDatabase):
    await message.answer('Введите имя таблицы: ')
    await state.set_state(FSMUpdateDb.show_table)


@router.message(StateFilter(FSMUpdateDb.update_db))
async def execute_sql(message: Message, state: FSMContext, db: SQLiteDatabase):
    db.execute_through_sql(message.text)
    await message.answer('Данные были обновлены.')
    await state.clear()


@router.message(StateFilter(FSMUpdateDb.show_table))
async def execute_sql(message: Message, state: FSMContext, db: SQLiteDatabase):
    table = db.select_table(message.text, tuple_=True)
    table = list(map(str, table))
    logger.debug(table)
    await message.answer('\n'.join(table))
    await state.clear()
