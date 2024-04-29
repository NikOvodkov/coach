from dataclasses import dataclass


@dataclass
class Muscle:
    length: int  # длина мышщы
    strength: int  # сила мышцы в условных единицах
    fibers_per_nerve: int  # количество мышечных волокон на 1 нерв
    nerves: int  # количество управляющих мышцей нервов
    fibers: int  # общее количество мышечных волокон в мышце
    fiber_thickness: int  # средняя толщина мышечного волокна


@dataclass
class Exercise:
    power_consumption: int  # относительные энергозатраты на 1 повторение, например в калориях
    muscles: list[tuple[Muscle, int]]  # список пар мышца-вовлечение
    time: int  # нормализованное время исполнения 1 повторения в миллисекундах
    iteration_timeout: int  # нормализованный таймаут между повторениями в миллисекундах
    set_timeout: int  # нормализованный таймаут между подходами в секундах


@dataclass
class Workout:
    power_consumption: int  # относительные энергозатраты на тренировку, например в калориях
    exercises: list[tuple[Exercise, int, int]]  # список пар упражнение-количество повторов-перерыв в секундах
    time: int  # примерное время исполнения тренировки в секундах
    iteration_timeout: int  # таймаут между повторениями в миллисекундах
    set_timeout: int  # таймаут между подходами в секундах


@dataclass
class User:
    endurance: int  # выносливость
    muscles: list[tuple[Muscle, int, int]]  # список пар мышца-развитость-нервная сила в секундах