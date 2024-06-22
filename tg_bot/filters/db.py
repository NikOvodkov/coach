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
        cell = db.select_rows(table='users', fetch='one', user_id=message.from_user.id)
        logger.debug(f'filter  {cell=}')
        if cell:
            return {'cell': cell[self.column]}
        return False


class MaterialType(BaseFilter):
    def __init__(self, types: list[int]) -> None:
        self.types = types

    async def __call__(self, message: Message, db: SQLiteDatabase) -> bool | dict[str, Any]:
        cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
        if cell and (cell['type'] in self.types):
            return {'cell': cell['type']}
        return False


class NeedModerating(BaseFilter):
    async def __call__(self, message: Message, db: SQLiteDatabase) -> bool | dict[str, Any]:
        table = db.select_table('materials')
        if table:
            logger.debug(f'{table[0]=}')
            return {'row': table[0]}
        return False
