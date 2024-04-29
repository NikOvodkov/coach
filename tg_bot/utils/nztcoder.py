import asyncio
import time
from typing import AsyncGenerator

from pyrogram import Client
from pyrogram.enums import ChatAction
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from tg_bot.config import load_config

# config = load_config('.env')
# client = Client(name='me_client', api_id=config.tg_bot.api_id, api_hash=config.tg_bot.api_hash)


async def clone_content(donor_channel_id: int, my_channel_id: int):
    config = load_config('.env')
    client = Client(name='me_client', api_id=config.tg_bot.api_id, api_hash=config.tg_bot.api_hash)
    await client.start()

    messages: AsyncGenerator[Message, None] = client.get_chat_history(chat_id=donor_channel_id, limit=3)
    async for message in messages:
        await message.copy(chat_id=my_channel_id)


async def all_message():
    config = load_config('.env')
    client = Client(name='me_client', api_id=config.tg_bot.api_id, api_hash=config.tg_bot.api_hash)
    await client.start()
    messages: AsyncGenerator[Message, None] = client.get_chat_history(chat_id='nihaudiniho', limit=3)
    async for message in messages:
        await message.copy(chat_id='nihaudiniho')


# client.run()
# client.start()
# client.send_message('me', 'Test_message')
# client.stop()

if __name__ == '__main__':
    asyncio.run(clone_content(donor_channel_id=-1001112562459, my_channel_id=-1001960729872))
    # asyncio.run(all_message())
