from aiogram.fsm.state import StatesGroup, State


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMUpdateDb(StatesGroup):
    # Создаем экземпляры класса State для сервиса Life Calendar, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    email = State()
    update_db = State()


