from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

yesno = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Да'), KeyboardButton(text='Нет')]
    ], one_time_keyboard=True, resize_keyboard=True
)

ready = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Готово')]
    ], one_time_keyboard=True, resize_keyboard=True
)

ready_end = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Продолжить'), KeyboardButton(text='Закончить тренировку')]
    ], one_time_keyboard=True, resize_keyboard=True
)

ready_in = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text='Готово',
            callback_data='ready'
        )]
    ]
)


yesno_in = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text='Да',
            callback_data='yes'
        )],
        [InlineKeyboardButton(
            text='Нет',
            callback_data='no'
        )]
    ]
)


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        # [KeyboardButton(text='Тренировка')],
        # [KeyboardButton(text='Статистика')],
        [KeyboardButton(text='Упражнения')],
        # [KeyboardButton(text='Мышцы')],
        [KeyboardButton(text='Выход')]
    ], one_time_keyboard=True, resize_keyboard=True
)

workout = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Начать')],
        [KeyboardButton(text='Закончить')]
    ], one_time_keyboard=True, resize_keyboard=True
)

muscles = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Добавить мышцу')],
        [KeyboardButton(text='Найти мышцу')],
        [KeyboardButton(text='Отредактировать мышцу')],
        [KeyboardButton(text='Исключить мышцу из упражнений')]  # частично либо абсолютно
    ], one_time_keyboard=True, resize_keyboard=True
)

exercises = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Выполнить тренировку')],
        [KeyboardButton(text='Добавить упражнение')],
        # [KeyboardButton(text='Отредактировать упражнение')],
        # [KeyboardButton(text='Исключить упражнение')]
    ], one_time_keyboard=True, resize_keyboard=True
)


muscle_groups = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Руки'), KeyboardButton(text='Ноги'), KeyboardButton(text='Грудь')],
        [KeyboardButton(text='Живот'), KeyboardButton(text='Спина')]
    ], one_time_keyboard=True, resize_keyboard=True
)

nokeyboard = ReplyKeyboardRemove()

choose_exercise = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Оставить"), KeyboardButton(text="Изучить"), KeyboardButton(text="Заменить")],
              [KeyboardButton(text="Выбрать из списка")],
              [KeyboardButton(text="Закончить тренировку")]],
    one_time_keyboard=True, resize_keyboard=True)
'''
# ------- Создаем клавиатуру через ReplyKeyboardBuilder -------

# Создаем кнопки с ответами согласия и отказа
button_yes = KeyboardButton(text=LEXICON_RU['yes_button'])
button_no = KeyboardButton(text=LEXICON_RU['no_button'])

# Инициализируем билдер для клавиатуры с кнопками "Давай" и "Не хочу!"
yes_no_kb_builder = ReplyKeyboardBuilder()

# Добавляем кнопки в билдер с аргументом width=2
yes_no_kb_builder.row(button_yes, button_no, width=2)

# Создаем клавиатуру с кнопками "Давай!" и "Не хочу!"
yes_no_kb: ReplyKeyboardMarkup = yes_no_kb_builder.as_markup(
    one_time_keyboard=True,
    resize_keyboard=True
)

# ------- Создаем игровую клавиатуру без использования билдера -------

# Создаем кнопки игровой клавиатуры
button_1 = KeyboardButton(text=LEXICON_RU['rock'])
button_2 = KeyboardButton(text=LEXICON_RU['scissors'])
button_3 = KeyboardButton(text=LEXICON_RU['paper'])

# Создаем игровую клавиатуру с кнопками "Камень 🗿",
# "Ножницы ✂" и "Бумага 📜" как список списков
game_kb = ReplyKeyboardMarkup(
    keyboard=[[button_1],
              [button_2],
              [button_3]],
    resize_keyboard=True
)
'''
