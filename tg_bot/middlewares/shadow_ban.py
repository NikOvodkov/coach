from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from logging_settings import logger
from tg_bot.config import Config
from tg_bot.database.sqlite import SQLiteDatabase


class ShadowBanMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        db: SQLiteDatabase = data.get('db')
        aiobot = data.get('bot')
        config: Config = data.get('config')
        tg_user: User = data.get('event_from_user')
        db_user = db.select_rows(table='users', fetch='one', user_id=tg_user.id)
        # await event.message.answer(f'тест ансвера {db_user[9]}')
        # await event.message.forward(config.tg_bot.admin_ids[0])
        logger.debug('Enter shadow_ban')
        # Ниже 4 строки - бот присылает уведомление, если кто-то с ним общается
        # if event.message and event.message.from_user.id != config.tg_bot.admin_ids[0]:
        #     await aiobot.send_message(config.tg_bot.admin_ids[0],
        #                               text=f'Пользователь {event.message.from_user.id} {event.message.from_user.username} '
        #                                    f'общается с ботом')
        logger.debug('AfterIF shadow_ban')
        if db_user is not None:
            db_user = db.select_rows(table='users', fetch='one', user_id=tg_user.id)
            if db_user['status'] == 0:
                logger.debug('user blocked')
                return
            logger.debug('user active')
        return await handler(event, data)
