# Инициализируем роутер уровня модуля
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tg_bot.utils.gsheet import gsheets

router = Router()


@router.message(Command('gsheet'))
async def process_gsheet(message: Message):
    logs = await gsheets(file='Example',
                         worksheet='Finsburg',
                         google_docs_key=str(Path.cwd() / Path('tg_bot', 'keys', 'gsheet.json')))
    await message.answer(', '.join(logs))
