from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

balance = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Посмотреть вес'), KeyboardButton(text='Посмотреть калории')]
        ], one_time_keyboard=True, resize_keyboard=True)

