from typing import Any

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase


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
        if message.text.strip().isdigit():
            cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
            if cell and (cell['type'] in self.types):
                return {'cell': cell['type']}
        elif message.text.lower().strip().startswith('динамическое непарное') and 1 in self.types:
            return {'cell': 1}
        elif message.text.lower().strip().startswith('динамическое парное') and 2 in self.types:
            return {'cell': 2}
        elif message.text.lower().strip().startswith('статическое непарное') and 3 in self.types:
            return {'cell': 3}
        elif message.text.lower().strip().startswith('статическое парное') and 4 in self.types:
            return {'cell': 4}
        elif message.text.lower().strip().startswith('разминка') and 5 in self.types:
            return {'cell': 5}
        elif message.text.lower().strip().startswith('заминка') and 6 in self.types:
            return {'cell': 6}
        elif message.text.lower().strip().startswith('тренировка') and 7 in self.types:
            return {'cell': 7}
        elif message.text.lower().strip().startswith('таймер') and 8 in self.types:
            return {'cell': 8}
        return False


class NeedModerating(BaseFilter):
    async def __call__(self, message: Message, db: SQLiteDatabase) -> bool | dict[str, Any]:
        table = db.select_table('materials')
        if table:
            logger.debug(f'{table[0]=}')
            return {'row': table[0]}
        return False
