from aiogram.fsm.state import StatesGroup, State


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMTrener(StatesGroup):
    # Создаем экземпляры класса State для сервиса Life Calendar, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    workout = State()  # Состояние тренировки
    choose_exercise = State()  # Состояние выбора упражнения
    choose_exercise_auto = State()  # Состояние выбора упражнения
    choose_exercise_manual = State()  # Состояние выбора упражнения
    workout_process = State()  # Состояние тренировки
    workout_almost_done = State()  # Состояние выполненной тренировки
    workout_done = State()  # Состояние выполненной тренировки
    workout_end = State()  # Состояние выполнения тренировки
    show_exercises = State()  # Состояние в момент входа в команду Тренер
    show_exercises_new = State()  # Состояние в момент входа в команду Тренер
    add_exercise = State()  # Состояние добавления или коррекции упражнения
    enter_weight = State()  # Состояние добавления веса

    check_bdate_01new = State()  # Проверить возраст / чистим сообщения
    enter_bdate_02new = State()  # Вводим возраст / чистим сообщения
    enter_bdate_03new = State()  # Вводим возраст / чистим сообщения
    check_data_04new = State()  # Проверить пол, возраст, рост, вес / чистим сообщения
    enter_data_05new = State()  # Проверить пол, возраст, рост, вес / чистим сообщения
    enter_data_06new = State()  # Проверить пол, возраст, рост, вес / чистим сообщения
    warmup_07new = State()  # Делаем разминку, нажимаем Готово / чистим сообщения
    choose_06new = State()  # Выбираем упражнение, нажимаем Заменить и чистим сообщения или Оставить и НЕ ЧИСТИМ
    workout_info_07new = State()  # Читаем инструкцию на воркаут, нажимаем Готово и чистим сообщения
    workout_1_07new = State()  # Делаем 1 подход, нажимаем Готово и чистим сообщения
    workout_2_08new = State()  # Делаем 2 подход, нажимаем Готово и чистим сообщения
    workout_3_09new = State()  # Делаем 3 подход, нажимаем Готово и чистим сообщения
    workout_4_10new = State()  # Делаем 4 подход, нажимаем Готово и чистим сообщения
    workout_5_11new = State()  # Делаем 5 подход, нажимаем Готово и чистим сообщения
    save_12new = State()  # Сохраняем тренировку, НЕ ЧИСТИМ, предлагаем еще одну тренировку

    is_forwarded = State()  # Состояние добавления реферера или тренера


class FSMCoach(StatesGroup):
    input_shw = State()  # вводим пол, рост, вес
    input_shw_2 = State()  # подтверждаем пол, рост, вес
    input_shw_3 = State()  # сохраняем пол, рост, вес
    input_birth_date = State()  # вводим дату рождения
    input_birth_date_2 = State()  # подтверждаем дату рождения
    input_geo = State()  # получаем часовой пояс
    input_geo_2 = State()  # подтверждаем часовой пояс
    input_geo_3 = State()  # сохраняем часовой пояс
    input_geo_4 = State()  # уточняем часовой пояс
    start_workout = State()  # запускаем тренировку


class FSMAi(StatesGroup):
    get_task = State()  # общаемся с ии
    get_context = State()  # общаемся с ии
    run = State()  # общаемся с ии






