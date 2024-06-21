from aiogram.fsm.state import StatesGroup, State


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMAdd(StatesGroup):
    # Создаем экземпляры класса State , последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    add_or_update = State()  # Меняем старый или добавляем новый?
    update_type = State()  # Выбор типа обновляемого материала
    add_choose_type = State()  # Выбор типа добавляемого материала
    type_exercise_1_a = State()  # Добавляем динамическое упражнение
    type_exercise_1_b = State()  # Добавляем статическое упражнение
    type_exercise_2 = State()  # Добавляем динамическое упражнение
    type_exercise_3 = State()  # Добавляем динамическое упражнение
    type_exercise_4 = State()  # Добавляем динамическое упражнение
    type_workout_1 = State()  # Добавляем тренировку
    type_workout_2 = State()  # Добавляем тренировку
    type_timer = State()  # Добавляем таймер
    exit_add = State()  # Выходим из режима добавления
    moderate_new = State()  # Режим модерации нового
    moderate_update = State()  # Режим модерации обновления
    exit_moderate = State()  # Прекращение режима модерации
    moderate_add_work = State()  # Прекращение режима модерации




