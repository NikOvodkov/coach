from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logging_settings import logger
from tg_bot.lexicon.a_other import LEXICON_RU

# Инициализируем роутер уровня модуля
router = Router()


# Этот хэндлер будет срабатывать на любые необрабатываемае сообщения в состоянии
@router.message(StateFilter(None))
async def send_echo_no_state(message: Message):
    try:
        await message.send_copy(chat_id=message.chat.id)
        await message.answer(text=LEXICON_RU['echo_no_state'])
        logger.debug(f'{message=}')
    except TypeError:
        await message.reply(text=LEXICON_RU['no_echo'])


# Этот хэндлер будет срабатывать на любые необрабатываемае сообщения в состоянии
@router.message()
async def send_echo_state(message: Message, state: FSMContext):
    try:
        await message.send_copy(chat_id=message.chat.id)
        await message.answer(text=f'{LEXICON_RU["echo_state"]}: {str(await state.get_state())}')
        logger.debug(f'{message=}')
    except TypeError:
        await message.reply(text=LEXICON_RU['no_echo'])
