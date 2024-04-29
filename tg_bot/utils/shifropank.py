from pyrogram import Client, filters  # телеграм клиент

import shelve  # файловая база данных

from pyrogram.types import Message

from logging_settings import logger
from tg_bot.config import load_config

db = shelve.open('data.db', writeback=True)  # заменить на sqlite

PRIVATE_PUBLIC = -1002119768968  # скрытый паблик для управления ботом
PUBLIC_PUBLIC = -1001960729872  # паблик куда будем репостить
SOURCE_PUBLICS = [
    # список пабликов-доноров, откуда бот будет пересылать посты
    -1001664564489,
    -1001895721035,
    -1001362015263
]

config = load_config('.env')

# client = Client(name='me_client', api_id=config.tg_bot.api_id, api_hash=config.tg_bot.api_hash)
# создаем клиент телеграм
app = Client("me_client", api_id=config.tg_bot.api_id, api_hash=config.tg_bot.api_hash)


# обработчик нового сообщения
# вызывается при появлении нового поста в одном из пабликов-доноров
@app.on_message(filters.chat(SOURCE_PUBLICS))
def new_channel_post(client: Client, message: Message):
    # сохраняем пост в базу (функцию add_post_to_db определим потом)
    post_id = add_post_to_db(message)
    # print(post_id)
    logger.debug(post_id)

    # автоматическая пересылка без обработки
    message.copy(PUBLIC_PUBLIC)

    # пересылаем пост в скрытый паблик
    message.forward(chat_id=PRIVATE_PUBLIC)
    # print('forwarded tu private')
    logger.debug('forwarded tu private')

    # в скрытый паблик отправляем присвоенный id поста
    client.send_message(PRIVATE_PUBLIC, post_id)
    # print('forwarded id')
    logger.debug('forwarded id')
    # потом для пересылки в публичный паблик админ должен отправить боту этот id


# функция сохранения поста в бд
# генерирует уникальный id для поста и возвратит этот id
def add_post_to_db(message):
    try:
        # генерируем уникальный id для поста, равен максимальному в базе + 1
        new_id = max(int(k) for k in db.keys()
                     if k.isdigit()) + 1
    except:
        # если постов еще нет в базе вылетит ошибка и мы попадем сюда
        # тогда id ставим = 1
        new_id = 1

    # запись в базу необходимой информации про пост
    # Обратите внимание, shelve поддеживает только строковые ключи
    db[str(new_id)] = {
        'username': message.chat.username,  # паблик-донор
        'message_id': message.id,  # внутренний id сообщения
    }
    # print(db[str(new_id)])
    logger.debug(db[str(new_id)])
    return new_id


# обработчик нового сообщения из скрытого паблика
# если админ пишет в паблик `132+` это значит переслать пост с id = 132 в публичный паблик
@app.on_message(filters.chat(PRIVATE_PUBLIC)
                & filters.regex(r'\d+\+')  # фильтр текста сообщения `{число}+`
                )
def post_request(client, message):
    # получаем id поста из сообщения (обрезаем "+" в конце)
    post_id = str(message.text).strip('+')
    # получаем из базы пост по этому id
    post = db.get(post_id)
    if post is None:
        # если нет в базе пишем в скрытый паблик ошибку
        client.send_message(PRIVATE_PUBLIC,
                            '`ERROR NO POST ID IN DB`')
        # и выходим
        return

    try:
        # по данным из базы, получаем pyrogram обьект сообщения
        msg = client.get_messages(post['username'], post['message_id'])
        # пересылаем его в паблик
        # as_copy=True значит, что мы не будем отображать паблик донор, будто это наш пост XD
        msg.copy(PUBLIC_PUBLIC)
        # отправляем сообщение в скрытый паблик о успехе
        client.send_message(PRIVATE_PUBLIC, f'`SUCCESS REPOST!`')
    except Exception as e:
        # если произойдет какая-то ошибка в 3 строчках выше - сообщим админу
        client.send_message(PRIVATE_PUBLIC, f'`ERROR {e}`')


if __name__ == '__main__':
    # print('Atempt to run telegrabber')
    logger.info('Atempt to run telegrabber')
    app.run()  # эта строка запустит все обработчики