import sqlite3
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommandScopeChat, ReplyKeyboardRemove
from openai import OpenAI

from tg_bot.filters.admin import IsAdmin
from tg_bot.keyboards.trener import ready, yesno
from tg_bot.lexicon.ai import AI
from tg_bot.services.setting_commands import set_admins_commands, set_chat_admins_commands
from tg_bot.config import load_config, Config
from tg_bot.states.trener import FSMCoach, FSMAi
from tg_bot.utils.trener import get_names_from_content

router = Router()

# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


# @router.message(Command('start'))
# async def admin_start(message: Message, db: SQLiteDatabase, state: FSMContext):
#     name = message.from_user.full_name
#     user_id = message.from_user.id
#     cur_state = await state.get_state()
#     cur_data = await state.get_data()
#     if cur_state or cur_data:
#         await message.answer(text=f'State is not None: {cur_state} data= {cur_data}')
#         logger.debug(f'{message=}')
#         await state.clear()
#     await set_admins_commands(message.bot, user_id)
#     try:
#         db.add_user(user_id=user_id, name=name)
#     except sqlite3.IntegrityError as err:
#         # print(err)
#         logger.exception(f'User {name=} {user_id=} not added to db!')
#     finally:
#         count_users = db.count_rows('users')[0]
#         await message.answer(
#             '\n'.join([
#                 f'Привет, админ {message.from_user.full_name}!',
#                 f'Ты был занесён в базу',
#                 f'В базе <b>{count_users}</b> пользователей'
#             ]), reply_markup=keyboard)


def quote_html(arg):
    pass


@router.message(Command('ai'))
async def start_ai(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text='Введите задачу для ИИ (system content):', reply_markup=ready)
    await state.set_state(FSMAi.get_task)


@router.message(F.text, StateFilter(FSMAi.get_task))
async def get_task(message: Message, state: FSMContext):
    if message.text.lower().strip() == 'готово':
        await state.update_data(system_content=AI['system_content'])
    else:
        await state.update_data(system_content=message.text)
    await message.answer(text='Введите предысторию разговора (не более 4000 символов):', reply_markup=ready)
    await state.set_state(FSMAi.get_context)


@router.message(F.text.lower().strip() == 'готово', StateFilter(FSMAi.get_context))
@router.message(F.text.lower().strip() == 'да', StateFilter(FSMAi.run))
async def run_ai(message: Message, state: FSMContext, ai: OpenAI):
    data = await state.get_data()
    # if data['system_content']
    if message.text.lower().strip() == 'готово' and state == FSMAi.get_context:
        user_content = []
    else:
        user_content = get_user_content(message.text)
        await state.update_data(system_content=message.text)
    completion = ai.chat.completions.create(
        model="gpt-3.5-turbo",  # max_tokens=100000,
        messages=[
            {"role": "system", "content": },
            {"role": "user", "content": "Прочитайте предыдущую переписку с женщиной и продолжайте её таким образом, чтобы женщине очень захотелось "
                                        "с вами встретиться. "}
        ]
    )
    await message.answer(text=completion.choices[0].message.content)


@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMAi.run))
@router.message(F.text, StateFilter(FSMAi.get_context))
async def get_task(message: Message, state: FSMContext):
    if message.text.lower().strip() != 'нет':
        await state.update_data(user_content=message.text)
    data = await state.get_data()
    names = get_names_from_content(data['user_content'])
    await message.answer(text=f'Имена собеседников: {names}?', reply_markup=yesno)
    await state.set_state(FSMAi.run)


@router.message(Command('get_commands'))
async def message_get_commands(message: Message):
    no_lang = await message.bot.get_my_commands(scope=BotCommandScopeChat(chat_id=message.from_user.id))
    no_args = await message.bot.get_my_commands()
    en_lang = await message.bot.get_my_commands(scope=BotCommandScopeChat(chat_id=message.from_user.id),
                                                language_code='en')
    await message.reply('\n\n'.join(
        f'<pre>{quote_html(arg)=}</>' for arg in (no_lang, no_args, en_lang)
    ))


@router.message(Command('reset_commands'))
async def message_reset_commands(message: Message):
    await message.bot.delete_my_commands(BotCommandScopeChat(chat_id=message.from_user.id), language_code='en')
    await message.reply('Команды были удалены')


@router.message(Command('change_commands'))
async def change_admin_commands(message: Message):
    await set_chat_admins_commands(message.bot, message.chat.id)
    await message.answer('Команды администраторов для этого чата были изменены.')
