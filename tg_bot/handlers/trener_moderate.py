import asyncio
from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from logging_settings import logger
from tg_bot.config import load_config
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.filters.db import NeedModerating
from tg_bot.keyboards.trener import yesno
from tg_bot.services.ufuncs import clear_delete_list
from tg_bot.states.add import FSMAdd
from tg_bot.utils.trener import count_exercises_levels

router = Router()
# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


@router.message(Command(commands='update_levels'))
async def update_levels(message: Message, state: FSMContext, db: SQLiteDatabase):
    await count_exercises_levels(db=db)


@router.message(F.text.strip().lower() == 'да', StateFilter(FSMAdd.exit_moderate), NeedModerating())
@router.message(Command(commands='moderate_material'), NeedModerating())
async def moderate_material(message: Message, state: FSMContext, db: SQLiteDatabase, row: Any):
    logger.debug('moderate_material_enter')
    data = await state.get_data()
    logger.debug(f'{data=}')
    data['delete_list'] = []
    data['delete_list'].append(message.message_id)
    logger.debug(f'{row["exercise_id"]=}')
    # data['row'] = db.select_table('materials')[0]
    if row['exercise_id'] is not None:
        oldrow = db.select_rows(table='exercises', fetch='one', exercise_id=row['exercise_id'])
        if row["file_id"]:
            if oldrow['media_type'] == 'photo':
                msg = await message.answer_photo(photo=oldrow["file_id"], caption='Текущая версия')
            else:
                msg = await message.answer_document(document=oldrow["file_id"], caption='Текущая версия')
            data['delete_list'].append(msg.message_id)
            if row['media_type'] == 'photo':
                msg = await message.answer_photo(photo=row["file_id"], caption='На модерацию')
            else:
                msg = await message.answer_document(document=row["file_id"], caption='На модерацию')
            data['delete_list'].append(msg.message_id)
        msg = await message.answer(text=f'Текущая версия:\n'
                                        f'{oldrow["type"]=} {oldrow["name"]=} \n{oldrow["description"]=} \n'
                                        f'{oldrow["description_text_link"]=} {oldrow["description_video_link"]=}'
                                        f'\nНа модерацию:\n'
                                        f'{row["type"]=} {row["name"]=} \n{row["description"]=} \n'
                                        f'{row["description_text_link"]=} {row["description_video_link"]=}\n'
                                        f'Принимаем, отклоняем, принимаем частично указанные столбцы?',
                                   reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMAdd.moderate_update)
    else:
        logger.debug(f'before_answer_doc {row["media_type"]=}')
        if row['media_type'] == 'photo':
            msg = await message.answer_photo(row["file_id"])
        else:
            msg = await message.answer_document(row["file_id"])
        data['delete_list'].append(msg.message_id)
        msg = await message.answer(text=f'{row["type"]=} {row["name"]=} \n{row["description"]=} \n'
                                        f'{row["description_text_link"]=} {row["description_video_link"]=}\n'
                                        f'Принимаем или отклоняем?',
                                   reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMAdd.moderate_new)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(row=dict(row))
    state_ = await state.get_state()
    logger.debug(f'{state_=}')


@router.message(F.text, StateFilter(FSMAdd.moderate_new))
async def moderate_new(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    logger.debug('moderate_new')
    data = await state.get_data()
    row = data['row']
    data['delete_list'] = []
    data['delete_list'].append(message.message_id)
    # materials = db.select_table('materials')
    if message.text.strip().lower().startswith('принимаем'):
        logger.debug(f'{data["row"]=}')
        await bot.send_message(chat_id=data['row']['user_id'], text=message.text)
        db.add_exercise(user_id=row['user_id'], type_=row['type'], name=row['name'], description=row['description'],
                        description_text_link=row['description_text_link'], description_video_link=row['description_video_link'],
                        file_id=row['file_id'], file_unique_id=row['file_unique_id'], media_type=row['media_type'],
                        arms=row['arms'], legs=row['legs'], chest=row['chest'], abs_=row['abs'], back=row['back'])
        if (row['type'] == 1) or (row['type'] == 2):
            msg = await message.answer(text='Посчитайте и введите работу для нового динамического упражнения:',
                                       reply_markup=ReplyKeyboardRemove())
            await state.set_state(FSMAdd.moderate_add_work)
        else:
            msg = await message.answer(text='Материал внесен в базу, проверить наличие других обновлений на модерацию?',
                                       reply_markup=yesno)
            await state.set_state(FSMAdd.exit_moderate)
        exercise = db.select_rows(table='exercises', fetch='one', file_unique_id=row['file_unique_id'])
        if exercise:
            logger.debug(f'delete moderated material')
            db.delete_rows(table='materials', material_id=row['material_id'])
        else:
            logger.debug(f'moderated material not added')
        data['delete_list'].append(msg.message_id)
    elif message.text.strip().lower().startswith('отклоняем'):
        logger.debug(f'row["user_id"]=')
        await bot.send_message(chat_id=row['user_id'], text=message.text)
        msg = await message.answer(text='Материал отклонен, проверить наличие других обновлений на модерацию?',
                                   reply_markup=yesno)
        db.delete_rows(table='materials', material_id=row['material_id'])
        data['delete_list'].append(msg.message_id)
        await state.set_state(FSMAdd.exit_moderate)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text.strip().lower(), StateFilter(FSMAdd.moderate_add_work))
async def moderate_add_work(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    logger.debug(f'moderate_add_work {data["row"]["exercise_id"]=}')
    data['delete_list'].append(message.message_id)
    db.update_cells(table='exercises', cells={'work': float(message.text.strip())}, file_unique_id=data['row']['file_unique_id'])
    msg = await message.answer(text='Работа внесена в базу, проверить наличие других обновлений на модерацию?',
                               reply_markup=yesno)
    data['delete_list'].append(msg.message_id)
    await state.set_state(FSMAdd.exit_moderate)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text, StateFilter(FSMAdd.moderate_update))
async def moderate_new(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    logger.debug('moderate_update')
    data = await state.get_data()
    row = data['row']
    data['delete_list'] = []
    data['delete_list'].append(message.message_id)
    # materials = db.select_table('materials')
    if message.text.strip().lower().startswith('принимаем частично'):
        await bot.send_message(chat_id=row['user_id'], text=message.text)
        cells = {}
        for cell in message.text.split():
            if cell in row:
                cells[cell] = row[cell]
        db.update_cells('exercises', cells=cells, exercise_id=row['exercise_id'])
        msg = await message.answer(text='Материал внесен в базу, проверить наличие других обновлений на модерацию?',
                                   reply_markup=yesno)
        await state.set_state(FSMAdd.exit_moderate)
        db.delete_rows(table='materials', material_id=row['material_id'])
        data['delete_list'].append(msg.message_id)
    elif message.text.strip().lower().startswith('принимаем'):
        await bot.send_message(chat_id=row['user_id'], text=message.text)
        cells = {}
        for cell in row:
            if row[cell] is not None:
                if type(row[cell]) is str:
                    # cells[cell] = f"'{row[cell]}'"
                    cells[cell] = row[cell]
                else:
                    cells[cell] = row[cell]
        logger.debug(f'{cells=}')
        db.update_cells('exercises', cells=cells, exercise_id=row['exercise_id'])
        # update_cellss(db=db, table='exercises', cells=cells, exercise_id=row['exercise_id'])
        msg = await message.answer(text='Материал внесен в базу, проверить наличие других обновлений на модерацию?',
                                   reply_markup=yesno)
        await state.set_state(FSMAdd.exit_moderate)
        db.delete_rows(table='materials', material_id=row['material_id'])
        data['delete_list'].append(msg.message_id)
    elif message.text.strip().lower().startswith('отклоняем'):
        await bot.send_message(chat_id=row['user_id'], text=message.text)
        msg = await message.answer(text='Материал отклонен, проверить наличие других обновлений на модерацию?',
                                   reply_markup=yesno)
        db.delete_rows(table='materials', material_id=row['material_id'])
        data['delete_list'].append(msg.message_id)
        await state.set_state(FSMAdd.exit_moderate)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text.strip().lower() == 'нет', StateFilter(FSMAdd.exit_moderate))
async def exit_add(message: Message, state: FSMContext, bot: Bot):
    logger.debug('exit_moderate')
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await state.clear()


@router.message(F.text.strip().lower() == 'да', StateFilter(FSMAdd.exit_moderate))
@router.message(Command(commands='moderate_material'))
async def no_materials(message: Message, state: FSMContext, bot: Bot):
    logger.debug('enter_no_materials')
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    data['delete_list'].append(message.message_id)
    msg = await message.answer(text='Материалов на модерацию не обнаружено!',
                               reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(3)
    data['delete_list'].append(msg.message_id)
    await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await state.clear()
