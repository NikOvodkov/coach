from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from logging_settings import logger
from tg_bot.config import load_config
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.filters.db import MaterialType
from tg_bot.states.add import FSMAdd

router = Router()
# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


#  --ADD OR MOD--  ###############################################################################
@router.message(F.text.strip().lower() == 'да', StateFilter(FSMAdd.exit_add))
@router.message(Command(commands='add'))
async def start_add(message: Message, state: FSMContext):
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


@router.message(F.photo, StateFilter(FSMAdd.type_exercise_1_b))
async def type_exercise_1_b(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    file_unique_id = message.photo[-1].file_unique_id
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, exercise_id=data['exercise_id'],
                        file_id=message.photo[-1].file_id, file_unique_id=file_unique_id,
                        date=datetime.utcnow().isoformat())
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.photo[-1].file_id,
                        file_unique_id=file_unique_id, date=datetime.utcnow().isoformat())
    msg = await message.answer(text='Изображение сохранено. Пришлите ссылку на публичное видео с русской озвучкой, '
                                    'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                    'какие могут быть нюансы, ошибки и противопоказания:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
    await state.set_state(FSMAdd.type_exercise_2)


@router.message(F.animation, StateFilter(FSMAdd.type_exercise_1_a))
async def type_exercise_1_a(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    file_unique_id = message.animation.file_unique_id
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, exercise_id=data['exercise_id'],
                        file_id=message.animation.file_id, file_unique_id=file_unique_id,
                        date=datetime.utcnow().isoformat())
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.animation.file_id,
                        file_unique_id=file_unique_id, date=datetime.utcnow().isoformat())
    msg = await message.answer(text='Анимация сохранена. Пришлите ссылку на публичное видео с русской озвучкой, '
                                    'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                    'какие могут быть нюансы, ошибки и противопоказания:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
    await state.set_state(FSMAdd.type_exercise_2)


@router.message(F.animation, StateFilter(FSMAdd.type_exercise_1_b))
async def type_exercise_1_ba(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    file_unique_id = message.animation.file_unique_id
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, exercise_id=data['exercise_id'],
                        file_id=message.animation.file_id, file_unique_id=file_unique_id,
                        date=datetime.utcnow().isoformat())
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.animation.file_id,
                        file_unique_id=file_unique_id, date=datetime.utcnow().isoformat())
    msg = await message.answer(text='Анимация сохранена. Пришлите ссылку на публичное видео с русской озвучкой, '
                                    'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                    'какие могут быть нюансы, ошибки и противопоказания:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
    await state.set_state(FSMAdd.type_exercise_2)


#  --ONLY ADD--  ###############################################################################
@router.message(F.text.lower() == 'динамическое упражнение', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    msg = await message.answer(text='Пришлите анимацию в формате gif, которая демонстрирует выполнение упражнения. '
                                    'Желательно, чтобы задействованные мышцы были выделены. '
                                    'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                    'которое позволит найти это упражнение по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(type=1)
    await state.set_state(FSMAdd.type_exercise_1_a)


@router.message(F.text.lower() == 'статическое упражнение', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    msg = await message.answer(text='Пришлите анимацию в формате gif или изображение в совместимом с Телеграм формате, '
                                    'которые демонстрируют выполнение упражнения. '
                                    'Желательно, чтобы задействованные мышцы были выделены. '
                                    'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                    'которое позволит найти это упражнение по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(type=2)
    await state.set_state(FSMAdd.type_exercise_1_b)


#  --ONLY MOD--  ###############################################################################
@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[1]))
async def add_choose_type(message: Message, state: FSMContext, db: SQLiteDatabase, cell: int):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    # cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
    # if cell:
    #     await state.update_data(type=cell['type'])
    await state.update_data(exercise_id=int(message.text.strip()))
    msg = await message.answer(text='Пришлите анимацию в формате gif, которая демонстрирует выполнение упражнения. '
                                    'Желательно, чтобы задействованные мышцы были выделены. '
                                    'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                    'которое позволит найти это упражнение по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    logger.debug(f'{cell=}')
    await state.update_data(type=cell)
    await state.set_state(FSMAdd.type_exercise_1_a)


@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[2]))
async def add_choose_type(message: Message, state: FSMContext, db: SQLiteDatabase, cell: int):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    # cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
    # if cell:
    #     await state.update_data(type=cell['type'])
    await state.update_data(exercise_id=int(message.text.strip()))
    msg = await message.answer(text='Пришлите анимацию в формате gif или изображение в совместимом с Телеграм формате, '
                                    'которые демонстрируют выполнение упражнения. '
                                    'Желательно, чтобы задействованные мышцы были выделены. '
                                    'Если на анимации изображено похожее упражнение, а не именно это, оно не будет добавлено. '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название упражнения, '
                                    'которое позволит найти это упражнение по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    logger.debug(f'{cell=}')
    await state.update_data(type=cell)
    await state.set_state(FSMAdd.type_exercise_1_b)


@router.message(F.text.strip().lower() == 'пропустить', StateFilter(FSMAdd.type_exercise_1_b))
async def type_exercise_1_b(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    db.add_material(user_id=message.from_user.id, type_=data['type'], exercise_id=data['exercise_id'],
                    date=datetime.utcnow().isoformat())
    msg = await message.answer(text='Пришлите ссылку на публичное видео с русской озвучкой, '
                                    'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                    'какие могут быть нюансы, ошибки и противопоказания:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_exercise_2)


@router.message(F.text.strip().lower() == 'пропустить', StateFilter(FSMAdd.type_exercise_1_a))
async def type_exercise_1_a(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    db.add_material(user_id=message.from_user.id, type_=data['type'], exercise_id=data['exercise_id'],
                    date=datetime.utcnow().isoformat())
    msg = await message.answer(text='Пришлите ссылку на публичное видео с русской озвучкой, '
                                    'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                    'какие могут быть нюансы, ошибки и противопоказания:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_exercise_2)
