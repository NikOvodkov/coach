import asyncio
import os
from datetime import timedelta, datetime
from pathlib import Path
from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, URLInputFile, InputMediaVideo, InputFile, CallbackQuery
from aiogram.utils.markdown import hide_link
from aiogram.utils.media_group import MediaGroupBuilder

from logging_settings import logger
from tg_bot.database.sqlite import SQLiteDatabase
from tg_bot.keyboards.trener import yesno, ready
from tg_bot.lexicon.life_calendar import LEXICON_RU
from tg_bot.states.trener import FSMTrener
from tg_bot.utils.life_calendar import generate_image_calendar
from tg_bot.states.life_calendar import FSMLifeCalendar
from tg_bot.utils.trener import generate_new_split, Split

# Инициализируем роутер уровня модуля
router = Router()


# @router.message(F.video)
# @router.message(F.animation)
async def get_multimedia(message: Message, state: FSMContext, db: SQLiteDatabase):
    if message.caption == 'timer':
        db.update_cell(table='Multimedia', cell='file_id',
                       cell_value=message.animation.file_id, key='name', key_value=message.caption, new=True)
        db.update_cell(table='Multimedia', cell='file_unique_id',
                       cell_value=message.animation.file_unique_id, key='name', key_value=message.caption, new=True)
    if message.caption == 'warmup':
        db.update_cell(table='Multimedia', cell='file_id',
                       cell_value=message.video.file_id, key='name', key_value=message.caption, new=True)
        db.update_cell(table='Multimedia', cell='file_unique_id',
                       cell_value=message.video.file_unique_id, key='name', key_value=message.caption, new=True)
    if message.caption.isdigit():
        db.update_cell(table='exercises_base', cell='file_id', cell_value=message.animation.file_id,
                       key='exercise_id', key_value=int(message.caption), new=True)
        db.update_cell(table='exercises_base', cell='file_unique_id', cell_value=message.animation.file_unique_id,
                       key='exercise_id', key_value=int(message.caption), new=True)


@router.message(Command(commands='statistics'))
async def show_statistics(message: Message, state: FSMContext, db: SQLiteDatabase):
    workouts = db.select_rows(table='workouts_long', user_id=message.from_user.id, new=True)
    msg = ''
    statistics = {}
    for workout in workouts:
        if workout[3] == 1:
            statistics[workout[0]] = str(workout[0]) + ': ' + str(workout[6]) + ' #' + str(workout[2]) + '-' + str(workout[4])
        else:
            statistics[workout[0]] += '-' + str(workout[4])
    for workout in statistics:
        msg += statistics[workout] + '\n'
    await message.answer(text=msg)
    await state.clear()


@router.message(Command(commands='fitness'))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase):
    delete_list = []
    user = db.select_table('users_base_long', user_id=message.from_user.id, new=True)
    if user[11] is None:
        msg = await message.answer(text='Введите свой вес (целое число): ',
                                   reply_markup=ReplyKeyboardRemove())
        delete_list.append(msg.message_id)
        await state.set_state(FSMTrener.enter_weight)
    else:
        msg = await message.answer(
            text=f'Личный тренер приветствует вас!\n Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
                 f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
                 f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
                 f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.')
        delete_list.append(msg.message_id)
        msg = await message.answer_video(
            video=db.select_row(table='Multimedia', name='warmup', new=True)[3],
            caption='Разминка 8 минут',
            reply_markup=ready)
        delete_list.append(msg.message_id)
        await state.set_state(FSMTrener.show_exercises)

    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)


@router.message(F.text, StateFilter(FSMTrener.enter_weight))
async def enter_weight(message: Message, state: FSMContext, db: SQLiteDatabase):
    delete_list = []
    if message.text.isdigit():
        db.update_cell(table='users_base_long', cell='weight', cell_value=int(message.text),
                       key='user_id', key_value=message.from_user.id, new=True)
    # msg = await message.answer(text=f'Личный тренер приветствует вас! Сперва выполните разминку: \n'
    #                                 f'{hide_link("https://www.youtube.com/watch?v=mU2K1Z17yLg")}', reply_markup=ready)
    msg = await message.answer(
        text=f'Личный тренер приветствует вас!\n Выполните разминку из видео ниже, вы можете делать упражнения в удобном для вас темпе: '
             f'быстрее или медленнее чем показано в видео. Обратите внимание, красным цветом выделены '
             f'мышцы, на которые делается акцент в упражнении. Вы можете выполнить другую разминку, '
             f'вместо представленной, но важно, чтобы она разогревала все мышцы и связки от шеи до ступней.')
    delete_list.append(msg.message_id)
    msg = await message.answer_video(
        video=db.select_row(table='Multimedia', name='warmup', new=True)[3],
        caption='Разминка 8 минут',
        reply_markup=ready)
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)
    await state.set_state(FSMTrener.show_exercises)


@router.message(F.text, StateFilter(FSMTrener.show_exercises))
@router.message(F.text.lower().strip() == 'да', StateFilter(FSMTrener.workout_end))
async def start_trener(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    msg = await message.answer(text='Выберите упражнение из списка ниже и пришлите его номер ответным сообщением.',
                               reply_markup=ReplyKeyboardRemove())
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await asyncio.sleep(1)
    exercises_table = db.select_all_table('exercises_base', new=True)
    if exercises_table:
        captions = []
        for exercise in exercises_table:
            captions.append(str(exercise[0]) + ' ' + exercise[2])
        msg = await message.answer(text='\n'.join(captions), reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.workout)
    else:
        msg = await message.answer(text='Сбой базы данных. Попробуйте еще раз или обратитесь к администратору',
                                   reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.show_exercises)
    delete_list.append(msg.message_id)
    await state.update_data(delete_list=delete_list)


@router.callback_query(F.data == 'yes', StateFilter(FSMTrener.workout_end))
@router.callback_query(F.data == 'ready', StateFilter(FSMTrener.show_exercises))
async def start_trener_callback(callback: CallbackQuery, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    msg = await callback.answer(text='Выберите упражнение из списка ниже и пришлите его номер ответным сообщением.',
                                reply_markup=ReplyKeyboardRemove())
    # delete_list.append(msg. .message_id)
    delete_list.append(callback.message_id)
    await asyncio.sleep(1)
    exercises_table = db.select_all_table('exercises_base', new=True)
    if exercises_table:
        captions = []
        for exercise in exercises_table:
            captions.append(str(exercise[0]) + ' ' + exercise[2])
        msg = await callback.answer(text='\n'.join(captions), reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.workout)
    else:
        msg = await callback.answer(text='Сбой базы данных. Попробуйте еще раз или обратитесь к администратору',
                                    reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMTrener.show_exercises)
    delete_list.append(msg.message_id)
    await state.update_data(delete_list=delete_list)


@router.message(StateFilter(FSMTrener.workout))
async def start_workout(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    workout_number = db.select_all_table(table='workouts_long', new=True)[-1][0] + 1
    logger.debug(f'{workout_number=}')
    await state.update_data(exercise_id=int(message.text))
    time_start = datetime.utcnow().timestamp()
    last_workouts = db.select_last_workout_new(user_id=user[0], exercise_id=int(message.text))
    exercise = db.select_row(table='exercises_base', exercise_id=int(message.text), new=True)

    await message.answer_animation(
        animation=exercise[5],
        caption=exercise[2],
        reply_markup=ReplyKeyboardRemove())

    if last_workouts:
        new_workout = (str(last_workouts[-5][4]) + ' ' + str(last_workouts[-4][4]) + ' ' + str(last_workouts[-3][4]) +
                       ' ' + str(last_workouts[-2][4]) + ' ' + str(last_workouts[-1][4]))
        logger.debug(f'{new_workout=}')
        new_workout = generate_new_split(new_workout)
    else:
        new_workout = '1 1 1 1 1'
    new_workout_split = list(map(int, new_workout.split()))
    msg = await message.answer(
        text=f'Если упражнение вам незнакомо или непонятно, найдите его в интернет и изучите самостоятельно.\n\n'
             f'Теперь вам нужно выполнить 5 подходов выбранного упражнения, с указанным количество повторений: '
             f'\n{new_workout}+\n'
             f'Повторения делайте в среднем темпе, паузу между подходами выбирайте самостоятельно, '
             f'руководствуясь собственными ощущениями. Обычно пауза длится от 10 секунд до 3 минут. '
             f'В последнем пятом подходе сделайте МАКСИМУМ повторений, для этого он обозначен '
             f'{new_workout_split[-1]}+.\n'
             f'Итак, выполните первый подход из {new_workout_split[0]} повторений и нажмите кнопку "Готово". '
             f'Если не удалось выполнить все необходимые повторения, напишите сколько удалось.',
        reply_markup=ready)
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(workout_number=workout_number)
    await state.update_data(time_start=time_start)
    await state.update_data(delete_list=delete_list)
    await state.update_data(new_workout=new_workout_split)
    data = await state.get_data()
    logger.debug(f'{data=}')
    await state.set_state(FSMTrener.workout_process_1)


@router.message(F.text, StateFilter(FSMTrener.workout_process_1))
async def workout_process_1(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    if message.text.isdigit():
        data['done_workout'] = [int(message.text)]
    else:
        data['done_workout'] = [data['new_workout'][0]]
    await state.update_data(done_workout=data['done_workout'])

    msg = await message.answer_animation(
        animation=db.select_row(table='Multimedia', name='timer', new=True)[3],
        caption='Отдыхайте...',
        reply_markup=ReplyKeyboardRemove())
    delete_list.append(msg.message_id)
    await asyncio.sleep(10)

    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    logger.debug(f'{data["done_workout"][0]=}')
    work = (data['done_workout'][0] * int(user[11]) / 100
            * db.select_row(table='exercises_base', exercise_id=data['exercise_id'], new=True)[4])
    arms_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=0, new=True)[4]
    legs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=1, new=True)[4]
    chest_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=2, new=True)[4]
    abs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=3, new=True)[4]
    back_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=4, new=True)[4]
    logger.debug(f'{work=}')
    db.add_workout_new(workout_id=data['workout_number'], user_id=user[0], exercise_id=data['exercise_id'],
                       approach=1, dynamic=data['done_workout'][0], static=0, date=datetime.utcnow().isoformat(),
                       work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs=abs_work, back=back_work, new=True)

    msg = await message.answer(
        text=f'После того, как отдохнёте, выполните второй подход из {data["new_workout"][1]} повторений '
             f'и нажмите кнопку "Готово". Если не удалось выполнить все необходимые повторения, '
             f'напишите сколько удалось.', reply_markup=ready)
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)
    await state.set_state(FSMTrener.workout_process_2)


@router.message(F.text, StateFilter(FSMTrener.workout_process_2))
async def workout_process_2(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    if message.text.isdigit():
        data['done_workout'].append(int(message.text))
    else:
        data['done_workout'].append(data['new_workout'][1])
    await state.update_data(done_workout=data['done_workout'])
    msg = await message.answer_animation(
        animation=db.select_row(table='Multimedia', name='timer', new=True)[3],
        caption='Отдыхайте...',
        reply_markup=ReplyKeyboardRemove())
    # mmedia = db.select_row(table='Multimedia', multimedia_id=1)
    # path = str(Path.cwd() / Path('tg_bot', 'handlers', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
    # with open(path, 'wb') as file:
    #     file.write(mmedia[2])
    # msg = await message.answer_animation(animation=FSInputFile(path), caption='Отдыхайте...', reply_markup=ReplyKeyboardRemove())
    delete_list.append(msg.message_id)
    # os.remove(path)
    await asyncio.sleep(10)

    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    work = (data['done_workout'][1] * int(user[11]) / 100
            * int(db.select_row(table='exercises_base', exercise_id=data['exercise_id'], new=True)[4]))
    arms_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=0, new=True)[4]
    legs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=1, new=True)[4]
    chest_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=2, new=True)[4]
    abs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=3, new=True)[4]
    back_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=4, new=True)[4]
    db.add_workout_new(workout_id=data['workout_number'], user_id=user[0], exercise_id=data['exercise_id'],
                       approach=2, dynamic=data['done_workout'][1], static=0, date=datetime.utcnow().isoformat(),
                       work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs=abs_work, back=back_work, new=True)

    msg = await message.answer(
        text=f'После того, как отдохнёте, выполните третий подход из {data["new_workout"][2]} повторений '
             f'и нажмите кнопку "Готово". Если не удалось выполнить все необходимые повторения, '
             f'напишите сколько удалось.', reply_markup=ready)
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)
    await state.set_state(FSMTrener.workout_process_3)


@router.message(F.text, StateFilter(FSMTrener.workout_process_3))
async def workout_process_3(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    if message.text.isdigit():
        data['done_workout'].append(int(message.text))
    else:
        data['done_workout'].append(data['new_workout'][2])
    await state.update_data(done_workout=data['done_workout'])
    msg = await message.answer_animation(
        animation=db.select_row(table='Multimedia', name='timer', new=True)[3],
        caption='Отдыхайте...',
        reply_markup=ReplyKeyboardRemove())
    # mmedia = db.select_row(table='Multimedia', multimedia_id=1)
    # path = str(Path.cwd() / Path('tg_bot', 'handlers', f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.gif'))
    # with open(path, 'wb') as file:
    #     file.write(mmedia[2])
    # msg = await message.answer_animation(animation=FSInputFile(path), caption='Отдыхайте...', reply_markup=ReplyKeyboardRemove())
    delete_list.append(msg.message_id)
    # os.remove(path)
    await asyncio.sleep(10)

    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    work = (data['done_workout'][2] * int(user[11]) / 100
            * int(db.select_row(table='exercises_base', exercise_id=data['exercise_id'], new=True)[4]))
    arms_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=0, new=True)[4]
    legs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=1, new=True)[4]
    chest_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=2, new=True)[4]
    abs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=3, new=True)[4]
    back_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=4, new=True)[4]
    db.add_workout_new(workout_id=data['workout_number'], user_id=user[0], exercise_id=data['exercise_id'],
                       approach=3, dynamic=data['done_workout'][2], static=0, date=datetime.utcnow().isoformat(),
                       work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs=abs_work, back=back_work, new=True)

    msg = await message.answer(
        text=f'После того, как отдохнёте, выполните четвёртый подход из {data["new_workout"][3]} повторений '
             f'и нажмите кнопку "Готово". Если не удалось выполнить все необходимые повторения, '
             f'напишите сколько удалось.', reply_markup=ready)
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)
    await state.set_state(FSMTrener.workout_process_4)


@router.message(F.text, StateFilter(FSMTrener.workout_process_4))
async def workout_process_4(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    delete_list = data['delete_list']
    if message.text.isdigit():
        data['done_workout'].append(int(message.text))
    else:
        data['done_workout'].append(data['new_workout'][3])
    await state.update_data(done_workout=data['done_workout'])
    msg = await message.answer_animation(
        animation=db.select_row(table='Multimedia', name='timer', new=True)[3],
        caption='Отдыхайте...',
        reply_markup=ReplyKeyboardRemove())
    delete_list.append(msg.message_id)


    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    work = (data['done_workout'][3] * int(user[11]) / 100
            * int(db.select_row(table='exercises_base', exercise_id=data['exercise_id'], new=True)[4]))
    arms_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=0, new=True)[4]
    legs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=1, new=True)[4]
    chest_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=2, new=True)[4]
    abs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=3, new=True)[4]
    back_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=4, new=True)[4]
    db.add_workout_new(workout_id=data['workout_number'], user_id=user[0], exercise_id=data['exercise_id'],
                       approach=4, dynamic=data['done_workout'][3], static=0, date=datetime.utcnow().isoformat(),
                       work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs=abs_work, back=back_work, new=True)


    await asyncio.sleep(10)
    msg = await message.answer(text=f'После того, как отдохнёте, выполните последний подход на максимум повторений. \n'
                                    f'Напишите, сколько повторений сделали.', reply_markup=ReplyKeyboardRemove())

    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await state.update_data(delete_list=delete_list)
    await state.set_state(FSMTrener.workout_done)



@router.message(F.text, StateFilter(FSMTrener.workout_done))
async def workout_done(message: Message, state: FSMContext, db: SQLiteDatabase):
    data = await state.get_data()
    logger.debug('enter workout_done')
    delete_list = data['delete_list']
    delete_list.append(message.message_id)
    last_repeat = int(message.text.strip())
    logger.debug(f'{last_repeat=}')
    data['done_workout'].append(last_repeat)

    user = db.select_row(table='users_base_long', user_id=message.from_user.id, new=True)
    logger.debug(f'{user=}')
    work = (data['done_workout'][4] * int(user[11]) / 100
            * int(db.select_row(table='exercises_base', exercise_id=data['exercise_id'], new=True)[4]))
    arms_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=0, new=True)[4]
    legs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=1, new=True)[4]
    chest_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=2, new=True)[4]
    abs_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=3, new=True)[4]
    back_work = work * db.select_row('exercises_muscles_base', exercise_id=data['exercise_id'], muscle_id=4, new=True)[4]
    db.add_workout_new(workout_id=data['workout_number'], user_id=user[0], exercise_id=data['exercise_id'],
                       approach=5, dynamic=data['done_workout'][4], static=0, date=datetime.utcnow().isoformat(),
                       work=work, arms=arms_work, legs=legs_work, chest=chest_work, abs=abs_work, back=back_work, new=True)
    await message.answer(text=f"Тренировка сохранена: упражнение №{data['exercise_id']}, подходы "
                              f"{' '.join(list(map(str, data['done_workout'])))}. "
                              f"Рекомендованный перерыв между тренировками одного упражнения - от 2 до 7 дней. "
                              f"Если перерыв будет более 7 дней, прогресс может отсутствовать.")
    msg = await message.answer(text=f"Если остались силы, можете выполнить ещё 5 подходов другого упражнения. Готовы?",
                               reply_markup=yesno)
    delete_list.append(msg.message_id)
    await state.update_data(delete_list=delete_list)
    await state.set_state(FSMTrener.workout_end)


@router.message(F.text.lower().strip() == 'нет', StateFilter(FSMTrener.workout_end))
async def end_workout(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    delete_list = data['delete_list']
    msg = await message.answer(text='До новых встреч!', reply_markup=ReplyKeyboardRemove())
    delete_list.append(msg.message_id)
    delete_list.append(message.message_id)
    await asyncio.sleep(30)
    for message_id in delete_list:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
    await state.update_data(delete_list=[])
    await state.clear()
