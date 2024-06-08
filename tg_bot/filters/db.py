from typing import Any

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logging_settings import logger
from tg_bot.database.sqlite2 import SQLiteDatabase


class MyUserDbFilter(BaseFilter):
    def __init__(self, column: str) -> None:
        self.column = column

    async def __call__(self, message: Message, db: SQLiteDatabase) -> bool | dict[str, Any]:
        cell = db.select_rows(table='users_base_long', fetch='one', user_id=message.from_user.id)[self.column]
        logger.debug(f'{cell=}')
        if cell:
            return {'cell': cell}
        return False
