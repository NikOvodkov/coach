from aiogram.fsm.state import StatesGroup, State


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMLifeCalendar(StatesGroup):
    # Создаем экземпляры класса State для сервиса Life Calendar, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    enter_date = State()        # Состояние запуска с вводом даты рождения
    enter_date_opt = State()  # вспомогательное состояние ввода даты
    no_enter_date = State()         # Состояние запуска без ввода даты рождения
    everyweek_order = State()      # Состояние подписки на еженедельную рассылку
    oldster_enter_date = State()     # Состояние запуска с вводом даты рождения для стариков
    confirm_date = State()   # Состояние подтверждения даты рождения
    change_timezone = State()   # Состояние выбора часового пояса
    confirm_geo = State()  # Состояние получения георасположения
    confirm_geo_process = State()  # Состояние подтверждения георасположения


