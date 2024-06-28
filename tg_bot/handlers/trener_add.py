import datetime
from typing import Any

import aiohttp
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from logging_settings import logger
from tg_bot.config import load_config, Config
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.filters.db import MaterialType
from tg_bot.keyboards.trener import yesno
from tg_bot.services.ufuncs import url_available, clear_delete_list
from tg_bot.states.add import FSMAdd
from tg_bot.states.trener import FSMTrener

router = Router()
# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


# done
@router.message(F.text.strip().lower() == 'да', StateFilter(FSMAdd.exit_add))
@router.message(Command(commands='add'))
async def start_add(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.text == '/add':
        await state.clear()
    data = await state.get_data()
    data['delete_list'] = []
    logger.debug(f'{data=}')
    data['delete_list'].append(message.message_id)
    msg = await message.answer(text='Выберите тип материала, который хотите добавить и нажмите соответствующую кнопку. '
                                    'В случае добавления нового материала должны быть заполнены ВСЕ поля, '
                                    'иначе материал не пройдёт модерацию. \n'
                                    'Для выборочного редактирования полей существующего материала, напишите его номер:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Динамическое упражнение')],
                                                                          [KeyboardButton(text='Статическое упражнение')],
                                                                          [KeyboardButton(text='Разминка'),
                                                                           KeyboardButton(text='Заминка')],
                                                                          [KeyboardButton(text='Тренировка'),
                                                                           KeyboardButton(text='Таймер')]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.add_choose_type)
    logger.debug('exit_start_add')


# done
@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[1]))
@router.message(F.text.lower() == 'динамическое упражнение', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    if message.text.strip().isdigit():
        cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
        if cell:
            await state.update_data(type=cell['type'])
        await state.update_data(exercise_id=int(message.text.strip()))
        msg = await message.answer(text='Пришлите анимацию в формате gif, которая демонстрирует выполнение упражнения. '
                                        'Желательно, чтобы задействованные мышцы были выделены. '
                                        'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                        'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                        'которое позволит найти это упражнение по описанию среди сотен других.',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
    else:
        if message.text.strip().lower() == 'динамическое упражнение':
            await state.update_data(type=1)
        msg = await message.answer(text='Пришлите анимацию в формате gif, которая демонстрирует выполнение упражнения. '
                                        'Желательно, чтобы задействованные мышцы были выделены. '
                                        'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                        'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                        'которое позволит найти это упражнение по описанию среди сотен других.',
                                   reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_exercise_1_a)


# done
@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[2]))
@router.message(F.text.lower() == 'статическое упражнение', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    if message.text.strip().isdigit():
        cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
        if cell:
            await state.update_data(type=cell['type'])
        await state.update_data(exercise_id=int(message.text.strip()))
        msg = await message.answer(text='Пришлите анимацию в формате gif или изображение в совместимом с Телеграм формате, '
                                        'которые демонстрируют выполнение упражнения. '
                                        'Желательно, чтобы задействованные мышцы были выделены. '
                                        'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                        'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                        'которое позволит найти это упражнение по описанию среди сотен других.',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
    else:
        if message.text.strip().lower() == 'статическое упражнение':
            await state.update_data(type=2)
        msg = await message.answer(text='Пришлите анимацию в формате gif или изображение в совместимом с Телеграм формате, '
                                        'которые демонстрируют выполнение упражнения. '
                                        'Желательно, чтобы задействованные мышцы были выделены. '
                                        'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                        'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                        'которое позволит найти это упражнение по описанию среди сотен других.',
                                   reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_exercise_1_b)


# done
@router.message(F.text.strip().lower() == 'пропустить', StateFilter(FSMAdd.type_exercise_1_b))
@router.message(F.photo, StateFilter(FSMAdd.type_exercise_1_b))
async def type_exercise_1_b(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()

    if message.photo:
        file_unique_id = message.photo[-1].file_unique_id
        if 'exercise_id' in data:
            db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, exercise_id=data['exercise_id'],
                            file_id=message.photo[-1].file_id, file_unique_id=file_unique_id,
                            date=datetime.datetime.utcnow().isoformat())
        else:
            db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.photo[-1].file_id,
                            file_unique_id=file_unique_id, date=datetime.datetime.utcnow().isoformat())
        msg = await message.answer(text='Изображение сохранено. Пришлите ссылку на публичное видео с русской озвучкой, '
                                        'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                        'какие могут быть нюансы, ошибки и противопоказания:',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        await state.update_data(file_unique_id=file_unique_id)
        data['delete_list'].append(msg.message_id)
    elif message.text:
        if 'exercise_id' in data:
            db.add_material(user_id=message.from_user.id, type_=data['type'], exercise_id=data['exercise_id'],
                            date=datetime.datetime.utcnow().isoformat())
        else:
            db.add_material(user_id=message.from_user.id, type_=data['type'],
                            date=datetime.datetime.utcnow().isoformat())
        msg = await message.answer(text='Пришлите ссылку на публичное видео с русской озвучкой, '
                                        'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                        'какие могут быть нюансы, ошибки и противопоказания:',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        data['delete_list'].append(msg.message_id)
        data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_exercise_2)


# done
@router.message(F.animation, StateFilter(FSMAdd.type_exercise_1_b))
async def type_exercise_1_ba(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    file_unique_id = message.animation.file_unique_id
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, exercise_id=data['exercise_id'],
                        file_id=message.animation.file_id, file_unique_id=file_unique_id,
                        date=datetime.datetime.utcnow().isoformat())
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.animation.file_id,
                        file_unique_id=file_unique_id, date=datetime.datetime.utcnow().isoformat())
    msg = await message.answer(text='Анимация сохранена. Пришлите ссылку на публичное видео с русской озвучкой, '
                                    'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                    'какие могут быть нюансы, ошибки и противопоказания:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    await state.update_data(file_unique_id=file_unique_id)
    data['delete_list'].append(msg.message_id)

    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_exercise_2)


# done
@router.message(F.text.strip().lower() == 'пропустить', StateFilter(FSMAdd.type_exercise_1_a))
@router.message(F.animation, StateFilter(FSMAdd.type_exercise_1_a))
async def type_exercise_1_a(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()

    if message.animation:
        file_unique_id = message.animation.file_unique_id
        if 'exercise_id' in data:
            db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, exercise_id=data['exercise_id'],
                            file_id=message.animation.file_id, file_unique_id=file_unique_id,
                            date=datetime.datetime.utcnow().isoformat())
        else:
            db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.animation.file_id,
                            file_unique_id=file_unique_id, date=datetime.datetime.utcnow().isoformat())
        msg = await message.answer(text='Анимация сохранена. Пришлите ссылку на публичное видео с русской озвучкой, '
                                        'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                        'какие могут быть нюансы, ошибки и противопоказания:',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        await state.update_data(file_unique_id=file_unique_id)
        data['delete_list'].append(msg.message_id)
    elif message.text:
        if 'exercise_id' in data:
            db.add_material(user_id=message.from_user.id, type_=data['type'], exercise_id=data['exercise_id'],
                            date=datetime.datetime.utcnow().isoformat())
        else:
            db.add_material(user_id=message.from_user.id, type_=data['type'],
                            date=datetime.datetime.utcnow().isoformat())
        msg = await message.answer(text='Пришлите ссылку на публичное видео с русской озвучкой, '
                                        'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                        'какие могут быть нюансы, ошибки и противопоказания:',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        data['delete_list'].append(msg.message_id)
        data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_exercise_2)


@router.message(F.text, StateFilter(FSMAdd.type_exercise_2))
async def type_exercise_2(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    if message.text.strip().lower() == 'пропустить':
        msg = await message.answer(text='Пришлите ссылку на публичный русскоязычный пост или статью, '
                                        'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                        'какие могут быть нюансы, ошибки и противопоказания:',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        await state.set_state(FSMAdd.type_exercise_3)
    else:
        db.update_cell_new(table='materials', cell='description_video_link', cell_value=message.text.strip(),
                           file_unique_id=data['file_unique_id'])
        msg = await message.answer(text='Ссылка сохранена. Пришлите ссылку на публичный русскоязычный пост или статью, '
                                        'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                        'какие могут быть нюансы, ошибки и противопоказания:',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        await state.set_state(FSMAdd.type_exercise_3)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text, StateFilter(FSMAdd.type_exercise_3))
async def type_exercise_3(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    if message.text.strip().lower() == 'пропустить':
        msg = await message.answer(text='Коротко опишите технику выполнения и важные нюансы упражнения. '
                                        'Старайтесь писать грамотно, можно подготовить текст заранее и скопировать сюда.',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        await state.set_state(FSMAdd.type_exercise_4)
    else:
        db.update_cell_new(table='materials', cell='description_text_link', cell_value=message.text.strip(),
                           file_unique_id=data['file_unique_id'])
        msg = await message.answer(text='Ссылка сохранена. Коротко опишите технику выполнения и важные нюансы упражнения. '
                                        'Старайтесь писать грамотно, можно подготовить текст заранее и скопировать сюда.',
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                    one_time_keyboard=True, resize_keyboard=True))
        await state.set_state(FSMAdd.type_exercise_4)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text, StateFilter(FSMAdd.type_exercise_4))
async def type_exercise_4(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot, config: Config):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    if message.text.strip().lower() == 'пропустить':
        msg = await message.answer(text='Материал отправлен на модерацию. Добавить ещё материал?',
                                   reply_markup=yesno)
    else:
        db.update_cell_new(table='materials', cell='description', cell_value=message.text.strip(),
                           file_unique_id=data['file_unique_id'])
        msg = await message.answer(text='Описание сохранено. Материал отправлен на модерацию. Добавить ещё материал?',
                                   reply_markup=yesno)
    await bot.send_message(config.tg_bot.admin_ids[0], text='Новый материал на модерацию: /moderate_material')
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.exit_add)


@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[3, 4, 5]))
@router.message(F.text.lower() == 'разминка', StateFilter(FSMAdd.add_choose_type))
@router.message(F.text.lower() == 'заминка', StateFilter(FSMAdd.add_choose_type))
@router.message(F.text.lower() == 'тренировка', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    logger.debug(f'razminka {data=}')
    data['delete_list'].append(message.message_id)
    if message.text.strip().isdigit():
        cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
        if cell:
            await state.update_data(type=cell['type'])
        await state.update_data(exercise_id=int(message.text.strip()))
    elif message.text.strip().lower() == 'разминка':
        await state.update_data(type=3)
    elif message.text.strip().lower() == 'заминка':
        await state.update_data(type=4)
    elif message.text.strip().lower() == 'тренировка':
        await state.update_data(type=5)
    msg = await message.answer(text='Пришлите русскоязычное видео в формате, совместимом с Телеграм, которое '
                                    'демонстрирует последовательность упражнений в формате "повторяй за мной". '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название, '
                                    'которое позволит найти видео по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_workout_1)


@router.message(F.video, StateFilter(FSMAdd.type_workout_1))
async def type_workout_1(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    logger.debug(f'enter type_workout_1 {data=}')
    file_unique_id = message.video.file_unique_id
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        exercise_id=data['exercise_id'], file_id=message.video.file_id, file_unique_id=file_unique_id,
                        date=datetime.datetime.utcnow().isoformat())
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        file_id=message.video.file_id, file_unique_id=file_unique_id,
                        date=datetime.datetime.utcnow().isoformat())
    msg = await message.answer(text='Видео сохранено. Коротко опишите содержание и особенности упражнений в видео. '
                                    'Старайтесь писать грамотно, можно подготовить текст заранее и скопировать сюда.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
    await state.set_state(FSMAdd.type_workout_2)


@router.message(F.text, StateFilter(FSMAdd.type_workout_2))
async def type_workout_2(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot, config: Config):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    db.update_cell_new(table='materials', cell='description', cell_value=message.text.strip(),
                       file_unique_id=data['file_unique_id'])
    await bot.send_message(config.tg_bot.admin_ids[0], text='Новый материал на модерацию: /moderate_material')
    msg = await message.answer(text='Описание сохранено. Материал отправлен на модерацию. Добавить ещё материал?',
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.exit_add)


@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[0]))
@router.message(F.text.strip().lower() == 'таймер', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext):
    logger.debug('enter_timer')
    data = await state.get_data()
    await state.update_data(type=0)
    data['delete_list'].append(message.message_id)
    logger.debug(f'{data=}')
    if message.text.strip().isdigit():
        await state.update_data(exercise_id=int(message.text.strip()))
    msg = await message.answer(text='Пришлите анимацию в формате gif с изображением таймера, отсчитывающего время. '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название таймера, '
                                    'которое позволит найти его по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_timer)


@router.message(F.animation, StateFilter(FSMAdd.type_timer))
async def type_timer(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot, config: Config):
    data = await state.get_data()
    date = datetime.datetime.utcnow().isoformat()
    file_unique_id = message.animation.file_unique_id
    logger.debug(f'{date=} {file_unique_id=} {message.caption=}')
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        exercise_id=data['exercise_id'], file_id=message.animation.file_id, file_unique_id=file_unique_id,
                        date=date)
    else:
        logger.debug('enter_add_timer_to_db')
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        file_id=message.animation.file_id, file_unique_id=file_unique_id,
                        date=date)
    logger.debug('before_message')
    await bot.send_message(config.tg_bot.admin_ids[0], text='Новый материал на модерацию: /moderate_material')
    msg = await message.answer(text='Анимация сохранена. Материал отправлен на модерацию. Добавить ещё материал?',
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
    await state.set_state(FSMAdd.exit_add)


@router.message(F.text.strip().lower() == 'нет', StateFilter(FSMAdd.exit_add))
async def exit_add(message: Message, state: FSMContext, bot: Bot, db: SQLiteDatabase):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await state.clear()
