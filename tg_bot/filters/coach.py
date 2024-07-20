from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import Message

from logging_settings import logger


class IsForwarded(BaseFilter):
    async def __call__(self, message: Message) -> bool | dict[str, Any]:
        user = message.forward_from
        if user:
            logger.debug(f'{user=}')
            return {'user': user}
        return False
