import asyncio
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.keyboards.trener import choose_exercise, ready_end, ready
from tg_bot.services.ufuncs import clear_delete_list
from tg_bot.states.trener import FSMTrener
from tg_bot.utils.trener import fill_exercises_users, generate_full_workout, show_exercise, show_approach, save_approach, award_user, run_timer

router = Router()


@router.message(F.text.lower().strip() == 'заменить', StateFilter(FSMTrener.workout))
@router.message(F.text.isdigit(), StateFilter(FSMTrener.workout))
@router.message(F.text, StateFilter(FSMTrener.show_exercises))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    """
    Перед началом тренировки, нужно проверить и заполнить при необходимости таблицу exercises_users
    для данного пользователя.
    :param message:
    :param state:
    :param db:
    :param bot:
    :return:
    """
    data = await state.get_data()
    if 'delete_list' not in data:
        data['delete_list'] = []
    if 'black_list' not in data:
        data['black_list'] = []
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    logger.debug(f'before fill_exercises_users')

    await fill_exercises_users(user_id=message.from_user.id, db=db)
    # users = db.select_table(table='users')
    # for user in users:
    #     await fill_exercises_users(user_id=user['user_id'], db=db)

    logger.debug(f'after fill_exercises_users')
    if message.text.lower().strip() == 'заменить':
        data['black_list'].append(data['new_workout'][0][0])
        if len(data['black_list']) > 27:
            data['black_list'] = []
        logger.debug(f'{data["black_list"]=}')
    if message.text.lower().isdigit():
        # data['new_workout'] = await gnrt_wrkt(user_id=message.from_user.id, db=db, old_ex=int(message.text),
        #                                       black_list=data['black_list'])
        data['new_workout'], muscle = await generate_full_workout(db, message.from_user.id, data['black_list'], int(message.text))
    else:
        # data['new_workout'] = await gnrt_wrkt(user_id=message.from_user.id, db=db, black_list=data['black_list'])
        data['new_workout'], muscle = await generate_full_workout(db, message.from_user.id, data['black_list'])
    logger.debug(f'{data["new_workout"][0][0]=}')
    msg = await show_exercise(message, db, data["new_workout"][0][0], choose_exercise, muscle)
    data['delete_list'].append(msg.message_id)
    await state.update_data(new_workout=data["new_workout"])
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(black_list=data['black_list'])
    await state.update_data(change_exercise=True)
    await state.set_state(FSMTrener.workout)


@router.message(F.text.lower().strip() == 'оставить', StateFilter(FSMTrener.workout))
async def workout_process_1(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    logger.debug(f'workout_process 1')
    await state.update_data(approach_counter=1)
    await state.update_data(change_exercise=False)
    await state.set_state(FSMTrener.workout_process)
    data['delete_list'].pop()
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    msg = await message.answer(
        text=f'Выполните повторов: {data["new_workout"][0][1]}'
             f'{"+" if data["new_workout"][0][2] else ""}. '
             f'Нажмите "Продолжить" или напишите сколько сделали:', reply_markup=ready_end)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])


@router.message(F.text.isdigit(), StateFilter(FSMTrener.workout_process))
@router.message(F.text.lower().strip() == 'продолжить', StateFilter(FSMTrener.workout_process))
@router.message(F.text.lower().strip() == 'готово', StateFilter(FSMTrener.workout_process))
async def workout_process_2(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    data = await state.get_data()
    logger.debug(f'workout_process 2')
    await state.update_data(approach_counter=data['approach_counter'] + 1)
    data = await save_approach(data, db, message)
    await state.update_data(approach=len(data['done_approaches']))
    await state.update_data(workout_number=data["workout_number"])
    await state.update_data(done_approaches=data['done_approaches'])
    await state.update_data(new_workout=data["new_workout"])
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    msg = await message.answer(
        text=f'Сделано: {", ".join([str(app[0]) + "-" + str(app[1]) for app in data["done_approaches"]])} '
             f'Отдыхайте, затем выполните повторов: {data["new_workout"][0][1]}'
             f'{"+" if data["new_workout"][0][2] else ""}. ', reply_markup=ReplyKeyboardRemove())
    data['delete_list'].append(msg.message_id)
    data = await run_timer(data, db, message)
    await state.set_state(FSMTrener.workout_process)

    exercise = db.select_rows(table='exercises', fetch='one', exercise_id=data["new_workout"][0][0])
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    msg = await message.answer(
        text=f'Сделано: {", ".join([str(app[0]) + "-" + str(app[1]) for app in data["done_approaches"]])} '
             f'Выполните повторов: {data["new_workout"][0][1]}'
             f'{"+" if data["new_workout"][0][2] else ""}. '
             f'Нажмите "Продолжить" или напишите сколько сделали:', reply_markup=ready_end)

    data['delete_list'].append(msg.message_id)

    # добавить еще сохранение при смене упражнения в воркауте
    # if (len(data['new_workout']) == 1) or data['done_approaches'][-1][0] != data['new_workout'][0][0]:
    if len(data['new_workout']) == 1:
        logger.debug(f'workout_process exit {data["new_workout"]=}')
        await state.set_state(FSMTrener.workout_done)
    await state.update_data(delete_list=data['delete_list'])
    if data['approach_counter'] == 2:
        await state.set_state(FSMTrener.show_exercises_new)
    else:
        await state.set_state(FSMTrener.workout_process)
    logger.debug(f'workout_process exit {data["delete_list"]=}')


@router.message(F.text.isdigit(), StateFilter(FSMTrener.show_exercises_new))
@router.message(F.text.lower().strip() == 'продолжить', StateFilter(FSMTrener.show_exercises_new))
@router.message(F.text.lower().strip() == 'готово', StateFilter(FSMTrener.show_exercises_new))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    """
    Перед началом тренировки, нужно проверить и заполнить при необходимости таблицу exercises_users
    для данного пользователя.
    :param message:
    :param state:
    :param db:
    :param bot:
    :return:
    """
    data = await state.get_data()

    data = await save_approach(data, db, message)
    await state.update_data(approach=len(data['done_approaches']))
    await state.update_data(workout_number=data["workout_number"])
    await state.update_data(done_approaches=data['done_approaches'])
    await state.update_data(new_workout=data["new_workout"])

    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    msg = await message.answer(
        text=f'Сделано: {", ".join([str(app[0]) + "-" + str(app[1]) for app in data["done_approaches"]])} '
        , reply_markup=ReplyKeyboardRemove())
    data = await run_timer(data, db, message)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    await state.update_data(done_approaches=[])
    msg = await show_exercise(message, db, data["new_workout"][0][0], choose_exercise)
    data['delete_list'].append(msg.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.update_data(change_exercise=True)
    await state.set_state(FSMTrener.workout)


@router.message(F.text.lower().strip() == 'закончить тренировку', StateFilter(FSMTrener.workout))
@router.message(F.text.lower().strip() == 'закончить тренировку', StateFilter(FSMTrener.show_exercises_new))
@router.message(F.text.lower().strip() == 'закончить тренировку', StateFilter(FSMTrener.workout_process))
@router.message(F.text.lower().strip() == 'закончить тренировку', StateFilter(FSMTrener.workout_done))
async def workout_done(message: Message, state: FSMContext, db: SQLiteDatabase, bot: Bot):
    logger.debug(f'start workout_done')
    data = await state.get_data()
    data['delete_list'].append(message.message_id)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot, message.from_user.id)
    logger.debug(f'before last save_approaches')
    cur_state = await state.get_state()
    if cur_state != FSMTrener.workout:
        data = await save_approach(data, db, message)
        await state.update_data(workout_number=data["workout_number"])
        await state.update_data(done_approaches=data['done_approaches'])
        await state.update_data(new_workout=data["new_workout"])
    await message.answer(text=f"Тренировка сохранена: "
                              f"{', '.join(list(map(lambda app: f'№{str(app[0])}-{str(app[1])}', data['done_approaches'])))}\n"
                              f"Рекомендованный перерыв между тренировками одного упражнения - от 1 до 3 дней. "
                              f"Если перерыв будет более 7 дней, прогресс может отсутствовать.")
    awards = await award_user(message.from_user.id, db)
    logger.debug(f'{awards=}')
    if awards['reps']:
        if awards['work']:
            msg = await message.answer(
                text=f'🎉 Поздравляем, у вас новые достижения! 🏆🏆 Вы выполнили максимальную работу за тренировку, '
                     f'и побили рекорд повторений в упражнении(ях) {", ".join(awards["reps"])}.',
                reply_markup=ReplyKeyboardRemove())
        else:
            msg = await message.answer(
                text=f'🎉 Поздравляем, у вас новое достижение! 🏆 Вы побили рекорд повторений в упражнении(ях) '
                     f'{", ".join(awards["reps"])}.', reply_markup=ReplyKeyboardRemove())
        data['delete_list'].append(msg.message_id)
    else:
        if awards['work']:
            msg = await message.answer(
                text=f'🎉 Поздравляем, у вас новое достижение! 🏆 Вы выполнили максимальную работу за тренировку. ',
                reply_markup=ReplyKeyboardRemove())
            data['delete_list'].append(msg.message_id)

    db.update_cell(table='users', cell='coach_sub', cell_value=datetime.utcnow().isoformat(),
                   key='user_id', key_value=message.from_user.id)
    msg = await message.answer(text='До новых встреч!', reply_markup=ReplyKeyboardRemove())
    logger.debug(f'after do novyh vstrech')
    data['delete_list'].append(msg.message_id)
    await asyncio.sleep(10)
    data['delete_list'] = await clear_delete_list(data['delete_list'], bot=bot, user_id=message.from_user.id)
    logger.debug(f'after deleting list')
    await state.update_data(delete_list=data['delete_list'])
    await state.clear()


@router.message(F.text.lower().strip().startswith('изучить'), StateFilter(FSMTrener.workout))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    exercise_id = data["new_workout"][0][0]
    exercise = db.select_rows(table='exercises', fetch='one', exercise_id=exercise_id)
    msg = await message.answer(
        text=f'{exercise["name"]}\n'
             f'Описание:\n'
             f'{exercise["description"]}\n'
             f'Очень подробное описание по ссылке:\n'
             f'{exercise["description_text_link"]}\n'
             f'Обучающее видео:\n'
             f'{exercise["description_video_link"]}\n'
             f'Чтобы вернуться, нажмите кнопку Готово.',
        reply_markup=ready)
    # data['delete_list'].append(msg.message_id)
    data['delete_list'].append(message.message_id)
    await state.update_data(delete_list=data['delete_list'])
    await state.set_state(FSMTrener.show_exercises)


@router.message(F.text.lower().strip() == 'напомнить через неделю')
async def remind_after_week(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    db.update_cell(table='users', cell='coach_sub', cell_value=datetime.utcnow().isoformat(),
                   key='user_id', key_value=message.from_user.id)
    await message.answer(text='Добавили вас в рассылку')


@router.message(F.text.lower().strip() == 'отписаться от напоминаний')
async def unsubscribe(message: Message, bot: Bot, state: FSMContext, db: SQLiteDatabase):
    await message.answer(text='Отписали вас. Если запустите тренировку самостоятельно, напоминания возобновятся.')