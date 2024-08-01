from __future__ import annotations

from datetime import datetime
from typing import Any

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase


class MyUserDbFilter(BaseFilter):
    def __init__(self, columns: list[str]) -> None:
        self.columns = columns

    async def __call__(self, message: Message, db: SQLiteDatabase) -> bool | dict[str, Any]:
        table = dict(db.select_rows(table='users', fetch='one', user_id=message.from_user.id))
        logger.debug(f'filter  {table=}')
        cells = {}
        if table:
            for column in self.columns:
                if column in table and table[column] is not None:
                    cells[column] = table[column]
        logger.debug(f'filter  {cells=}')
        if len(cells) == len(self.columns):
            return {'cells': cells}
        return False


class FirstDayLaunch(BaseFilter):
    async def __call__(self, message: Message, db: SQLiteDatabase) -> bool | dict[str, Any]:
        today = datetime.today().isoformat()
        last_approach = db.select_filtered_sorted_rows(table='approaches', sql2=f' AND date > "{today}" ORDER BY date DESC',
                                                             fetch='one', user_id=message.from_user.id)
        if last_approach:
            logger.debug("IT ISN'T 1ST LAUNCH TODAY")
            return False
        else:
            logger.debug("IT'S 1ST LAUNCH TODAY")
            return True


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
