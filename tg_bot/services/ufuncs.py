import aiohttp

from logging_settings import logger


async def clear_delete_list(delete_list, bot, user_id):
    logger.debug(f'{delete_list=}')
    for message_id in set(delete_list):
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except:
            logger.warning('Messages not deleted!')
    return []


async def url_available(url: str) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=1) as response:
            logger.debug(f'{url=} {response.status=}')
            return True if response.status == 200 else False
