from aiogram.fsm.state import StatesGroup, State


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMTrener(StatesGroup):
    # Создаем экземпляры класса State для сервиса Life Calendar, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    workout = State()  # Состояние тренировки
    workout_process_1 = State()  # Состояние тренировки
    workout_process_2 = State()  # Состояние тренировки
    workout_process_3 = State()  # Состояние тренировки
    workout_process_4 = State()  # Состояние тренировки
    workout_process_5 = State()  # Состояние тренировки
    workout_almost_done = State()  # Состояние выполненной тренировки
    workout_done = State()  # Состояние выполненной тренировки
    workout_end = State()  # Состояние выполнения тренировки
    show_exercises = State()  # Состояние в момент входа в команду Тренер
    add_exercise = State()  # Состояние добавления или коррекции упражнения
    enter_weight = State()  # Состояние добавления веса
