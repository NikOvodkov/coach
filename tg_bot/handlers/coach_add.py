import asyncio
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from logging_settings import logger
from tg_bot.config import load_config, Config
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.filters.db import MaterialType
from tg_bot.keyboards.trener import yesno
from tg_bot.services.ufuncs import clear_delete_list
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
                               reply_markup=ReplyKeyboardMarkup(
                                   keyboard=[[KeyboardButton(text='Динамическое НЕпарное упр-е'),
                                             KeyboardButton(text='Динамическое ПАРНОЕ упр-е')],
                                             [KeyboardButton(text='Статическое НЕпарное упр-е'),
                                             KeyboardButton(text='Статическое ПАРНОЕ упр-е')],
                                             [KeyboardButton(text='Разминка'), KeyboardButton(text='Заминка')],
                                             [KeyboardButton(text='Тренировка'), KeyboardButton(text='Таймер')]],
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
                        date=datetime.utcnow().isoformat(), media_type='photo')
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.photo[-1].file_id,
                        file_unique_id=file_unique_id, date=datetime.utcnow().isoformat(), media_type='photo')
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
                        date=datetime.utcnow().isoformat(), media_type='animation')
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.animation.file_id,
                        file_unique_id=file_unique_id, date=datetime.utcnow().isoformat(), media_type='animation')
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
                        date=datetime.utcnow().isoformat(), media_type='animation')
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption, file_id=message.animation.file_id,
                        file_unique_id=file_unique_id, date=datetime.utcnow().isoformat(), media_type='animation')
    msg = await message.answer(text='Анимация сохранена. Пришлите ссылку на публичное видео с русской озвучкой, '
                                    'где подробно объясняется и показывается, как выполняется данное упражнение, '
                                    'какие могут быть нюансы, ошибки и противопоказания:',
                               reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]],
                                                                one_time_keyboard=True, resize_keyboard=True))
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
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


@router.message(F.text.strip().lower() == 'нет', StateFilter(FSMAdd.add_work_2))
@router.message(F.text, StateFilter(FSMAdd.type_exercise_4))
async def type_exercise_4(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    if (message.text.strip().lower() != 'нет') and (message.text.strip().lower() != 'пропустить'):
        db.update_cell_new(table='materials', cell='description', cell_value=message.text.strip(),
                           file_unique_id=data['file_unique_id'])
    msg = await message.answer(text='Укажите примерное распределение нагрузки на разные группы мышц в добавленном '
                                    'упражнении/тренировке. Например, в классических отжиманиях от пола примерно 40% нагрузки '
                                    'приходится на руки, около 30% на грудь, и по 10% на живот, спину и ноги. В комплексных '
                                    'упражнениях и тренировках распределение может быть около 20% на каждую группу мышц.\n'
                                    'Укажите ЦЕЛОЕ число процентов от 0 до 100, приходящихся на руки (arms):',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(work={})
    await state.update_data(keys=['arms', 'legs', 'chest', 'abs', 'back'])
    await state.set_state(FSMAdd.add_work_1)


@router.message(F.video, StateFilter(FSMAdd.type_workout_1))
async def type_workout_1(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    logger.debug(f'enter type_workout_1 {data=}')
    file_unique_id = message.video.file_unique_id
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        exercise_id=data['exercise_id'], file_id=message.video.file_id, file_unique_id=file_unique_id,
                        date=datetime.utcnow().isoformat(), media_type='video')
    else:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        file_id=message.video.file_id, file_unique_id=file_unique_id,
                        date=datetime.utcnow().isoformat(), media_type='video')
    msg = await message.answer(text='Видео сохранено. Коротко опишите содержание и особенности упражнений в видео. '
                                    'Старайтесь писать грамотно, можно подготовить текст заранее и скопировать сюда.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
    await state.set_state(FSMAdd.type_workout_2)


@router.message(F.text.strip().lower() == 'нет', StateFilter(FSMAdd.add_work_2))
@router.message(F.text, StateFilter(FSMAdd.type_workout_2))
async def type_workout_2(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    if message.text.strip().lower() != 'нет':
        db.update_cell_new(table='materials', cell='description', cell_value=message.text.strip(),
                           file_unique_id=data['file_unique_id'])
    msg = await message.answer(text='Укажите примерное распределение нагрузки на разные группы мышц в добавленном '
                                    'упражнении/тренировке. Например, в классических отжиманиях от пола примерно 40% нагрузки '
                                    'приходится на руки, около 30% на грудь, и по 10% на живот, спину и ноги. В комплексных '
                                    'упражнениях и тренировках распределение может быть около 20% на каждую группу мышц.\n'
                                    'Укажите ЦЕЛОЕ число процентов от 0 до 100, приходящихся на руки (arms):',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(work={})
    await state.update_data(keys=['arms', 'legs', 'chest', 'abs', 'back'])
    await state.set_state(FSMAdd.add_work_1)


@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_work_1))
async def add_work_1(message: Message, state: FSMContext):
    data = await state.get_data()
    data['work'][data['keys'][0]] = int(message.text)
    data['keys'].pop(0)
    data['delete_list'].append(message.message_id)
    await asyncio.sleep(1)
    if len(data['keys']) > 0:
        logger.debug(f'{data["keys"]=}')
        msg = await message.answer(text=f'Укажите ЦЕЛОЕ число процентов от 0 до 100, приходящихся на {data["keys"][0]}:',
                                   reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMAdd.add_work_1)
    else:
        logger.debug(f'summiruem {data["work"]=}')
        msg = await message.answer(text=f'{", ".join([key + "-" + str(data["work"][key]) for key in data["work"]])}, '
                                        f'итого в сумме {sum(data["work"].values())}%. Верно?',
                                   reply_markup=yesno)
        await state.set_state(FSMAdd.add_work_2)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(keys=data['keys'])
    await state.update_data(work=data['work'])


@router.message(F.text.strip().lower() == 'да', StateFilter(FSMAdd.add_work_2))
async def add_work_2(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot, config: Config):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    db.update_cells(table='materials', cells={'arms': data['work']['arms'] / 100,
                                              'legs': data['work']['legs'] / 100,
                                              'chest': data['work']['chest'] / 100,
                                              'abs': data['work']['abs'] / 100,
                                              'back': data['work']['back'] / 100}, file_unique_id=data['file_unique_id'])
    await bot.send_message(config.tg_bot.admin_ids[0], text='Новый материал на модерацию: /moderate_material')
    await asyncio.sleep(1)
    msg = await message.answer(text='Материал отправлен на модерацию. Добавить ещё материал?',
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(work=data['work'])
    await state.set_state(FSMAdd.exit_add)


@router.message(F.animation, StateFilter(FSMAdd.type_timer))
async def type_timer(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot, config: Config):
    data = await state.get_data()
    date = datetime.utcnow().isoformat()
    file_unique_id = message.animation.file_unique_id
    logger.debug(f'{date=} {file_unique_id=} {message.caption=}')
    if 'exercise_id' in data:
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        exercise_id=data['exercise_id'], file_id=message.animation.file_id, file_unique_id=file_unique_id,
                        date=date, media_type='animation')
    else:
        logger.debug('enter_add_timer_to_db')
        db.add_material(user_id=message.from_user.id, type_=data['type'], name=message.caption,
                        file_id=message.animation.file_id, file_unique_id=file_unique_id,
                        date=date, media_type='animation')
    logger.debug('before_message')
    await bot.send_message(config.tg_bot.admin_ids[0], text='Новый материал на модерацию: /moderate_material')
    msg = await message.answer(text='Анимация сохранена. Материал отправлен на модерацию. Добавить ещё материал?',
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(file_unique_id=file_unique_id)
    await state.set_state(FSMAdd.exit_add)


@router.message(F.text.strip().lower() == 'нет', StateFilter(FSMAdd.exit_add))
async def exit_add(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await state.clear()


#  --ONLY ADD--  ###############################################################################
@router.message(F.text.lower().strip().startswith('динамическое'), StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext):
    logger.debug('enter add_choose_type dynamic')
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
    if message.text.lower().strip().startswith('динамическое непарное'):
        await state.update_data(type=1)
    elif message.text.lower().strip().startswith('динамическое парное'):
        await state.update_data(type=2)
    await state.set_state(FSMAdd.type_exercise_1_a)


@router.message(F.text.lower().strip().startswith('статическое'), StateFilter(FSMAdd.add_choose_type))
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
    if message.text.lower().strip().startswith('статическое непарное'):
        await state.update_data(type=3)
    elif message.text.lower().strip().startswith('статическое парное'):
        await state.update_data(type=4)
    await state.set_state(FSMAdd.type_exercise_1_b)


@router.message(F.text.lower() == 'разминка', StateFilter(FSMAdd.add_choose_type))
@router.message(F.text.lower() == 'заминка', StateFilter(FSMAdd.add_choose_type))
@router.message(F.text.lower() == 'тренировка', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.debug(f'razminka {data=}')
    data['delete_list'].append(message.message_id)
    if message.text.strip().lower() == 'разминка':
        await state.update_data(type=5)
    elif message.text.strip().lower() == 'заминка':
        await state.update_data(type=6)
    elif message.text.strip().lower() == 'тренировка':
        await state.update_data(type=7)
    msg = await message.answer(text='Пришлите русскоязычное видео в формате, совместимом с Телеграм, которое '
                                    'демонстрирует последовательность упражнений в формате "повторяй за мной". '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название, '
                                    'которое позволит найти видео по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMAdd.type_workout_1)


@router.message(F.text.strip().lower() == 'таймер', StateFilter(FSMAdd.add_choose_type))
async def add_choose_type(message: Message, state: FSMContext):
    logger.debug('enter_timer')
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    logger.debug(f'{data=}')
    msg = await message.answer(text='Пришлите анимацию в формате gif с изображением таймера, отсчитывающего время. '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название таймера, '
                                    'которое позволит найти его по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(type=8)
    await state.set_state(FSMAdd.type_timer)


#  --ONLY MOD--  ###############################################################################
@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[1, 2]))
async def add_choose_type(message: Message, state: FSMContext, cell: int):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
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


@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[3, 4]))
async def add_choose_type(message: Message, state: FSMContext, cell: int):
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
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


@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[5, 6, 7]))
async def add_choose_type(message: Message, state: FSMContext, cell: int):
    data = await state.get_data()
    logger.debug(f'MaterialType 5 6 7 {cell=}')
    data['delete_list'].append(message.message_id)
    # cell = db.select_rows(table='exercises', fetch='one', exercise_id=int(message.text.strip()))
    # if cell:
    #     await state.update_data(type=cell['type'])
    await state.update_data(exercise_id=int(message.text.strip()))
    msg = await message.answer(text='Пришлите русскоязычное видео в формате, совместимом с Телеграм, которое '
                                    'демонстрирует последовательность упражнений в формате "повторяй за мной". '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название, '
                                    'которое позволит найти видео по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(type=cell)
    await state.set_state(FSMAdd.type_workout_1)


@router.message(F.text.strip().isdigit(), StateFilter(FSMAdd.add_choose_type), MaterialType(types=[8]))
async def add_choose_type(message: Message, state: FSMContext):
    logger.debug('enter_timer')
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    logger.debug(f'{data=}')
    await state.update_data(exercise_id=int(message.text.strip()))
    msg = await message.answer(text='Пришлите анимацию в формате gif с изображением таймера, отсчитывающего время. '
                                    'В поле "Подпись/Caption" укажите короткое, ёмкое, понятное название таймера, '
                                    'которое позволит найти его по описанию среди сотен других.',
                               reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(type=8)
    await state.set_state(FSMAdd.type_timer)
