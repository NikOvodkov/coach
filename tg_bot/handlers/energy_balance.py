# Инициализируем роутер уровня модуля
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from logging_settings import logger
from tg_bot.database.sqlite2 import SQLiteDatabase
from tg_bot.keyboards.energy_balance import balance

router = Router()


@router.message(Command(commands='energy_balance'))
async def start_energy_balance(message: Message, state: FSMContext, db: SQLiteDatabase):
    # при входе в сервис Календарь жизни отправляем приветствие
    await message.answer(text='Если вы отслеживаете свой вес и/или занимаетесь подсчётом потреблённых и потраченных калорий, '
                              'бот может вам помочь вести учёт. Введённые данные также будут использоваться при расчётах '
                              'тренировок. Для ввода данных не нужно вызывать команду. '
                              'Просто в главном окне введите данные текстом в правильном формате. Если бот не реагирует на '
                              'ввод данных, нажмите команду /start и повторите ввод. Используйте только предложенные ниже форматы!\n'
                              '----Форматы----- \n'
                              'Учёт веса:\n'
                              '- знак "=", затем ЦЕЛОЕ число вашего веса в килограммах в формате: "=73";\n'
                              '- знак "=", затем 2 ЦЕЛЫХ числа в формате: "=73 19", где 73 - ваш вес в кг, 19 - % жира в организме;\n'
                              'Потребеление калорий:\n'
                              '- знак "+", затем целое число в килокалориях (Ккал) с комментарием или без в формате: '
                              '"+175 ранний обед", данная запись означает что вы съели ранний обед с энергетической '
                              'ценностью 175 Ккал;\n'
                              '- знак "+", затем 4 целых числа с комментарием или без в формате: '
                              '"+250 10 20 140 булочка с маком", данная запись означает что вы съели булочку с маком '
                              'энергетической ценностью 250 Ккал, в которой было 10 грамм белка, 20 грамм жира и 140 грамм '
                              'углеводов.\n'
                              'Траты калорий:\n'
                              '- знак "-", затем ЦЕЛОЕ число в килокалориях (Ккал) с комментарием или без в формате: '
                              '"-175 утренняя пробежка", данная запись означает что вы потратили 175Ккал во время '
                              'утренней пробежки.\n'
                              'ТРЕНИРОВКИ В БОТЕ УЧИТЫВАЮТСЯ АВТОМАТИЧЕСКИ, ВНОСИТЬ ИХ НЕ НУЖНО!', reply_markup=balance)


# Принимаем либо 1 число и комментарий: +200 ужин, либо 4 числа и комментарий: +200 40 50 80 гамбургер
@router.message(F.text.startswith('+'))
async def add_energy(message: Message, state: FSMContext, db: SQLiteDatabase):
    energy = message.text[1:].strip().split()
    logger.debug(f'{energy=}')
    comment = None
    p, f, c = None, None, None
    if energy[0].isdigit():
        if len(energy) > 3 and energy[1].isdigit() and energy[2].isdigit() and energy[3].isdigit():
            p = int(energy[1])
            f = int(energy[2])
            c = int(energy[3])
            comment = ' '.join(energy[4:]) if len(energy) > 4 else None
        else:
            comment = ' '.join(energy[1:]) if len(energy) > 1 else None
        energy = int(energy[0])
        db.add_energy(user_id=message.from_user.id, kcal=energy, proteins=p, fats=f, carbohydrates=c, comment=comment)
        await message.answer(text=f'Запись добавлена: в процессе употребления [{comment}] получено {energy} Ккал, '
                                  f'включая {p}г белков, {f}г жиров, {c}г углеводов.', reply_markup=balance)
    else:
        await message.answer(text=f'Данные не считаны, введите повторно целое число с комментарием или без '
                                  f'в формате: "+175 ранний обед" или 4 целых числа с комментарием или без '
                                  f'в формате: "+250 30 80 140 булочка с маком".', reply_markup=balance)


# Принимаем либо 1 число и комментарий: -200 пробежка
@router.message(F.text.startswith('-'))
async def sub_energy(message: Message, state: FSMContext, db: SQLiteDatabase):
    energy = message.text[1:].strip().split()
    logger.debug(f'{energy=}')
    comment = None
    if len(energy) > 1:
        comment = ' '.join(energy[1:])
    if energy[0].isdigit():
        energy = int(energy[0])
        db.add_energy(user_id=message.from_user.id, kcal=-energy, comment=comment)
        await message.answer(text=f'Запись добавлена: в процессе [{comment}] сожжено {energy} Ккал.', reply_markup=balance)
    else:
        await message.answer(text=f'Данные не считаны, введите повторно целое число в формате: "-75" '
                                  f'или целое число и комментарий в формате "-75 утренняя пробежка".', reply_markup=balance)


# Принимаем либо 1 число: =80, либо 2 числа: =80 20
@router.message(F.text.startswith('='))
async def input_weight(message: Message, state: FSMContext, db: SQLiteDatabase):
    weight = message.text[1:].strip().split()
    fat = None
    if len(weight) > 1 and weight[1].isdigit():
        fat = int(weight[1])
    logger.debug(f'{fat=}')
    if weight[0].isdigit():
        weight = int(weight[0])
        logger.debug(f'{weight=}')
        db.add_weight(user_id=message.from_user.id, weight=weight, fat=fat)
        await message.answer(text=f'Запись добавлена: вес = {weight} кг, процент жира = {fat}.', reply_markup=balance)
    else:
        await message.answer(text=f'Данные не считаны, введите повторно целое число в формате: "=75" '
                                  f'или 2 целых числе в формате "=75 15".', reply_markup=balance)


@router.message(F.text.startswith('Посмотреть вес'))
async def input_weight(message: Message, state: FSMContext, db: SQLiteDatabase):
    msg = ''
    weights = db.select_rows('users_weights', fetch='all', user_id=message.from_user.id)
    logger.debug(f'{weights=}')
    for weight in weights:
        date = datetime.fromisoformat(weight['date']).strftime('%d.%m.%y')
        msg += date + ': ' + str(weight['weight']) + 'кг - ' + str(weight['fat']) + '%\n'
    if msg == '':
        await message.answer(text='Таблица пока пуста', reply_markup=balance)
    else:
        await message.answer(text=msg, reply_markup=balance)


@router.message(F.text.startswith('Посмотреть калории'))
async def input_weight(message: Message, state: FSMContext, db: SQLiteDatabase):
    msg = ''
    weights = db.select_rows('energy_balance', fetch='all', user_id=message.from_user.id)
    logger.debug(f'{weights=}')
    for weight in weights:
        date = datetime.fromisoformat(weight['date']).strftime('%d.%m.%y')
        msg += (date + ' ' + weight['comment'] + ': ' + str(weight['kcal']) + 'Ккал= ' + str(weight['proteins'])
                + 'г белка +' + str(weight['fats']) + 'г жира +' + str(weight['carbohydrates']) + 'г углеводов\n')
    if msg == '':
        await message.answer(text='Таблица пока пуста', reply_markup=balance)
    else:
        await message.answer(text=msg, reply_markup=balance)
