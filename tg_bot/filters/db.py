from typing import Any

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


class MyUserDbFilter(BaseFilter):
    def __init__(self, column: str) -> None:
        self.column = column

    async def __call__(self, message: Message, db: SQLiteDatabase) -> bool | dict[str, Any]:
        cell = db.select_cell(table='users_base_long', column=self.column, user_id=message.from_user.id, new=True)[0]
        if cell:
            return {'cell': cell}
        return False
