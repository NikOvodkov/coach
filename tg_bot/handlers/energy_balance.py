# Инициализируем роутер уровня модуля
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tg_bot.database.sqlite import SQLiteDatabase

router = Router()


@router.message(Command(commands='energy_balance'))
async def start_life_calendar(message: Message, state: FSMContext, db: SQLiteDatabase):
    # при входе в сервис Календарь жизни отправляем приветствие
    await message.answer(text='Здесь ведётся учет потребеления и расхода килокалорий энергии.')

