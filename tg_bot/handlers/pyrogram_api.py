from pyrogram import filters, Client
from pyrogram.types import Message

from logging_settings import logger
from tg_bot.config import load_config

RESULT_CHANNEL = -1001960729872  # паблик куда будем репостить
SOURCE_CHANNELS = [
    # список пабликов-доноров, откуда бот будет пересылать посты
    -1001664564489,
    -1001895721035,
    -1001362015263,
    -1002119768968
]


# config = load_config('.env')

# @Client.on_message(filters.text & filters.private)
# async def echo(client, message):
#     await message.reply(message.text)


# обработчик нового сообщения
# вызывается при появлении нового поста в одном из пабликов-доноров
@Client.on_message(filters.chat(SOURCE_CHANNELS))
async def new_channel_repost(client: Client, message: Message):
    logger.debug('репост начало')
    try:
        # автоматическая пересылка без обработки
        await message.copy(RESULT_CHANNEL)
    except Exception as e:
        logger.exception(e)
        if message.caption:
            caption_html = message.caption.html
        else:
            caption_html = None
        if message.video:
            obj = await message.download(in_memory=True)
            await client.send_video(chat_id=RESULT_CHANNEL, video=obj, caption=caption_html)
        elif message.photo:
            obj = await message.download(in_memory=True)
            await client.send_photo(chat_id=RESULT_CHANNEL, photo=obj, caption=caption_html)
        elif message.text:
            obj = message.text
            await client.send_message(chat_id=RESULT_CHANNEL, text=obj)
        elif message.document:
            obj = await message.download(in_memory=True)
            await client.send_document(chat_id=RESULT_CHANNEL, document=obj, caption=caption_html)
        elif message.video_note:
            obj = await message.download(in_memory=True)
            await client.send_video_note(chat_id=RESULT_CHANNEL, video_note=obj)
        elif message.voice:
            obj = await message.download(in_memory=True)
            await client.send_voice(chat_id=RESULT_CHANNEL, voice=obj, caption=caption_html)
        elif message.sticker:
            obj = await message.download(in_memory=True)
            await client.send_sticker(chat_id=RESULT_CHANNEL, sticker=obj)
        elif message.animation:
            obj = await message.download(in_memory=True)
            await client.send_animation(chat_id=RESULT_CHANNEL, animation=obj, caption=caption_html)
        elif message.audio:
            obj = await message.download(in_memory=True)
            await client.send_audio(chat_id=RESULT_CHANNEL, audio=obj, caption=caption_html)
    logger.debug('репост конец')


if __name__ == '__main__':
    logger.info('Atempt to run telegrabber')
    # client_pyrogram.run()  # эта строка запустит все обработчики
