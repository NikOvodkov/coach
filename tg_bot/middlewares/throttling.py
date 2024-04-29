from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from cachetools import TTLCache

from tg_bot.config import Config

CACHE = TTLCache(maxsize=10_000, ttl=2)  # Максимальный размер кэша - 10000 ключей, а время жизни ключа - 2 секунды


class ThrottlingMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        tg_user: User = data.get('event_from_user')
        aiobot = data.get('bot')
        config: Config = data.get('config')
        if tg_user.id in CACHE:
            await event.message.answer(f'От вас слишком много запросов. Пауза 3 секунды...')
            await aiobot.send_message(config.tg_bot.admin_ids[0],
                                      text=f'Пользователь {event.message.from_user.id} {event.message.from_user.username} '
                                           f'замедлен.')
            return

        CACHE[tg_user.id] = True

        return await handler(event, data)
