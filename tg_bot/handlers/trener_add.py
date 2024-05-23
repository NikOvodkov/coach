from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logging_settings import logger
from tg_bot.config import load_config
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.filters.admin import IsAdmin
from tg_bot.states.trener import FSMTrener

router = Router()
# вешаем фильтр на роутер
router.message.filter(IsAdmin(load_config('.env').tg_bot.admin_ids))


@router.message(Command(commands='add_exercise'))
async def add_exercise(message: Message, state: FSMContext, db: SQLiteDatabase):
    logger.debug('add_exercise')
    delete_list = []
    msg = await message.answer(text='Введите упражнение в следующем формате:\n')
                                    # '"<№>,<название>,<руки>,<ноги>,<грудь>,<живот>,<спина>"\n')
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)
    await state.set_state(FSMTrener.add_exercise)


@router.message(F.text, StateFilter(FSMTrener.add_exercise))
async def add_exercise_process(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    message_list = message.text.split(',')
    logger.debug(message_list)
    exercise_id = message_list[0]
    user_id = message.from_user.id
    exercise_name = message_list[1]
    if exercise_id.isdigit():
        # обновляем таблицу Exercises_base
        table_str = db.select_table(table='exercises_base', exercise_id=exercise_id, new=True)
        logger.debug(f'{table_str[2]=}')
        exercise_name = table_str[2]
        exercise_id = table_str[0]
        # обновляем таблицу Muscles_exercises_base
        table_str = db.select_table(table='exercises_muscles_base', exercise_id=exercise_id, muscle_group_id=0, new=True)
        if not table_str:
            db.add_muscles_exercises(exercise_id=exercise_id, exercise_name=exercise_name, muscle_group_id=0,
                                     muscle_group_name='Руки', load=float(message_list[2]), new=True)
        table_str = db.select_table(table='exercises_muscles_base', exercise_id=exercise_id, muscle_group_id=1, new=True)
        if not table_str:
            db.add_muscles_exercises(exercise_id=exercise_id, exercise_name=exercise_name, muscle_group_id=1,
                                     muscle_group_name='Ноги', load=float(message_list[3]), new=True)
        table_str = db.select_table(table='exercises_muscles_base', exercise_id=exercise_id, muscle_group_id=2, new=True)
        if not table_str:
            db.add_muscles_exercises(exercise_id=exercise_id, exercise_name=exercise_name, muscle_group_id=2,
                                     muscle_group_name='Грудь', load=float(message_list[4]), new=True)
        table_str = db.select_table(table='exercises_muscles_base', exercise_id=exercise_id, muscle_group_id=3, new=True)
        if not table_str:
            db.add_muscles_exercises(exercise_id=exercise_id, exercise_name=exercise_name, muscle_group_id=3,
                                     muscle_group_name='Живот', load=float(message_list[5]), new=True)
        table_str = db.select_table(table='exercises_muscles_base', exercise_id=exercise_id, muscle_group_id=4, new=True)
        if not table_str:
            db.add_muscles_exercises(exercise_id=exercise_id, exercise_name=exercise_name, muscle_group_id=4,
                                     muscle_group_name='Спина', load=float(message_list[6]), new=True)
    else:
        db.add_exercise_base_new(user_id=user_id, name=exercise_name, new=True)

    msg = await message.answer(
        text=f'Упражнение добавлено'
    )
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)
    await state.clear()
