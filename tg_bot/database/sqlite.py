import sqlite3

from logging_settings import logger


class SQLiteDatabase:
    def __init__(self, path_to_db='sqlite160124.db'):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute_through_sql(self, sql):
        self.execute(sql, commit=True)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()
        connection = self.connection
        connection.set_trace_callback(logger.debug)
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)
        if commit:
            connection.commit()
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()
        connection.close()
        return data

    def select_all_table(self, table):
        sql = f'SELECT * FROM {table}'
        return self.execute(sql, fetchall=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += ' AND '.join([
            f'{item} = ?' for item in parameters
        ])
        return sql, tuple(parameters.values())

    def count_rows(self, table):
        return self.execute(f'SELECT COUNT(*) FROM {table};', fetchone=True)

    def update_cell(self, table, cell, cell_value, key, key_value):
        sql = f'/*многострочный коммент 1*/UPDATE {table}/*многострочный коммент 2*/ SET {cell}=? WHERE {key}=? -- Однострочный коммент'
        return self.execute(sql, parameters=(cell_value, key_value), commit=True)

    def select_row(self, table, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchone=True)

    def select_rows(self, table, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchall=True)

    def create_table_users(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS Users (
        user_id int NOT NULL,
        Name varchar(255) NOT NULL,
        email varchar(255),
        time_zone varchar(10),
        birth_date varchar(10), /* дата начала календаря */
        life_date varchar(10),  /* дата окончания календаря */
        life_calendar varchar(255),  /* дата следующего получения календаря, либо None */
        latitude varchar(255),
        longitude varchar(255),
        status varchar(10) NOT NULL, /* inactive, если пользователь бота заблокировал, иначе active */
        PRIMARY KEY (user_id)
        );
        '''
        self.execute(sql, commit=True)

    def add_user(self, user_id: int, name: str, email: str = None, time_zone: str = None,
                 birth_date: str = None, life_date: str = None, life_calendar: str = None,
                 latitude: str = None, longitude: str = None, status: str = 'active'):
        sql = ('INSERT IGNORE INTO Users(user_id, Name, email, time_zone, birth_date, life_date, life_calendar, '
               'latitude, longitude, status) VALUES(?,?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, name, email, time_zone, birth_date, life_date, life_calendar, latitude, longitude, status)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_exercises_base(self):  # таблица содержит неповторяющийся список уникальных упражнений
        sql = '''
        CREATE TABLE IF NOT EXISTS Exercises_base (
        exercise_id int NOT NULL,
        user_id int NOT NULL,  /* id пользователя, внёсшего упражнение в базу */
        Name varchar(255) NOT NULL,
        muscle_list varchar, /* список кортежей мышца-распределённая на неё нагрузка */
        duration_sec int, /* длительность упражнения в секундах */
        consumption_cal int, /* затраты энергии в калориях на 1 повторение */
        heart_load int, /* нагрузка на сердце в неясных пока величинах */
        description varchar,
        description_animation_link varchar,
        description_animation blob,
        description_picture_link varchar,
        description_picture blob,
        description_video_link varchar,
        description_video blob,
        description_sound_link varchar,
        description_sound blob,
        PRIMARY KEY (exercise_id)
        );
        '''
        self.execute(sql, commit=True)

    def add_exercise_base(self, user_id: int, name: str, description: str = None, muscle_list: str = None,
                          duration_sec: int = None, consumption_cal: int = None, heart_load: int = None,
                          description_animation_link: str = None, description_animation: str = None,
                          description_picture_link: str = None, description_picture: str = None,
                          description_video_link: str = None, description_video: str = None,
                          description_sound_link: str = None, description_sound: str = None):
        sql = ('INSERT INTO Exercises_base (exercise_id, user_id, Name, description, muscle_list, '
               'duration_sec, consumption_cal, heart_load, '
               'description_animation_link, description_animation, description_picture_link, description_picture, '
               'description_video_link, description_video, description_sound_link, description_sound) '
               'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (self.count_rows('Exercises_base')[0], user_id, name, description, muscle_list, duration_sec, consumption_cal, heart_load,
                      description_animation_link, description_animation, description_picture_link, description_picture,
                      description_video_link, description_video, description_sound_link, description_sound)
        self.execute(sql, parameters=parameters, commit=True)

    # таблица содержит неповторяющийся список уникальных мышц (около 600 штук)
    def create_table_muscles_base(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS Muscles_base (
        muscle_id int NOT NULL,
        user_id int NOT NULL, /* id пользователя, которые внёс мышцу в базу данных */
        Name varchar(255) NOT NULL,
        length_mm int, /* длина мышцы в мм */
        strength int, /* сила мышцы, относительная величина, пока методика расчёта не ясна */
        fibers_per_nerve int, /* мышечных волокон на 1 управляющий нерв */
        nerves int, /* всего управляющих нервов в мышце */
        fibers int, /* всего волокон в мышце */
        fiber_thickness_microns int, /* толщина волокна мышцы в мкм */
        endurance int, /* выносливость в неясных пока величинах */
        heart_load int, /* нагрузка на сердце в неясных пока величинах */
        exercises_list varchar,
        description varchar,
        description_animation_link varchar,
        description_animation blob,
        description_picture_link varchar,
        description_picture blob,
        description_video_link varchar,
        description_video blob,
        description_sound_link varchar,
        description_sound blob,
        PRIMARY KEY (muscle_id)
        );
        '''
        self.execute(sql, commit=True)

    def add_muscle(self, user_id: int, name: str, length_mm: int = None, strength: int = None,
                   fibers_per_nerve: int = None, nerves: int = None, fibers: int = None,
                   fiber_thickness_microns: int = None, endurance: int = None, heart_load: int = None,
                   exercises_list: str = None, description: str = None, description_animation_link: str = None,
                   description_animation: str = None, description_picture_link: str = None, description_picture: str = None,
                   description_video_link: str = None, description_video: str = None,
                   description_sound_link: str = None, description_sound: str = None):
        sql = ('INSERT INTO Muscles_base (muscle_id, user_id, name, length_mm, strength, fibers_per_nerve, nerves, fibers, '
               'fiber_thickness_microns, endurance, heart_load, exercises_list, description, '
               'description_animation_link, description_animation, description_picture_link, description_picture, '
               'description_video_link, description_video, description_sound_link, description_sound) '
               'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (self.count_rows('Muscles_base')[0], user_id, name, length_mm, strength, fibers_per_nerve, nerves, fibers,
                      fiber_thickness_microns, endurance, heart_load, exercises_list, description, description_animation_link,
                      description_animation, description_picture_link, description_picture, description_video_link,
                      description_video, description_sound_link, description_sound)
        self.execute(sql, parameters=parameters, commit=True)

        # таблица содержит неповторяющийся список уникальных мышц (около 600 штук)

    def create_table_muscles_user(self):
        sql = '''
            CREATE TABLE IF NOT EXISTS Muscles_user (
            muscle_id int NOT NULL,
            user_id int NOT NULL, /* id пользователя, хозяина мышцы */
            length_mm int, /* длина мышцы в мм */
            strength int, /* сила мышцы, относительная величина, пока методика расчёта не ясна */
            fibers_per_nerve int, /* мышечных волокон на 1 управляющий нерв */
            nerves int, /* всего управляющих нервов в мышце */
            fibers int, /* всего волокон в мышце */
            fiber_thickness_microns int, /* толщина волокна мышцы в мкм */
            endurance int, /* выносливость в неясных пока величинах */
            heart_load int, /* нагрузка на сердце в неясных пока величинах */
            PRIMARY KEY (muscle_id)
            );
            '''
        self.execute(sql, commit=True)

    def add_muscle_user(self, user_id: int, length_mm: int = None, strength: int = None,
                        fibers_per_nerve: int = None, nerves: int = None, fibers: int = None,
                        fiber_thickness_microns: int = None, endurance: int = None, heart_load: int = None):
        sql = ('INSERT INTO Muscles_user (muscle_id, user_id, length_mm, strength, fibers_per_nerve, nerves, fibers, '
               'fiber_thickness_microns, endurance, heart_load) '
               'VALUES(?,?,?,?,?,?,?,?,?,?)')
        parameters = (self.count_rows('Muscles_user')[0], user_id, length_mm, strength, fibers_per_nerve, nerves, fibers,
                      fiber_thickness_microns, endurance, heart_load)
        self.execute(sql, parameters=parameters, commit=True)

    # таблица содержит выполненные тренировки, привязанные к пользователям, невыполненные части тренировок не сохраняются
    def create_table_workouts(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS Workouts (
        workout_id int NOT NULL,
        user_id int NOT NULL,
        exercise_id, /* поле для тренировок из одного упражнения */
        exercises_list varchar, /* список кортежей вида упражнение-количество повторений-время отдыха */
        duration_min int, /* общая реальная длительность тренировки в минутах */
        consumption_cal int, /* затраты энергии за время тренировок в калориях, включая перерывы */
        heart_load int, /* нагрузка на сердце в неясных пока величинах */
        date varchar, /* дата тренировки */
        PRIMARY KEY (workout_id)
        );
        '''
        self.execute(sql, commit=True)

    def add_workout(self, user_id: int, exercise_id: int, exercises_list: str, duration_min: int = None,
                    consumption_cal: int = None, heart_load: int = None, date: str = None):
        sql = ('INSERT INTO Workouts (workout_id, user_id, exercise_id, exercises_list, '
               'duration_min, consumption_cal, heart_load, date) '
               'VALUES(?,?,?,?,?,?,?,?)')
        parameters = (self.count_rows('Workouts')[0], user_id, exercise_id, exercises_list,
                      duration_min, consumption_cal, heart_load, date)
        self.execute(sql, parameters=parameters, commit=True)

    def add_column(self, table: str, name: str):
        sql = f'ALTER TABLE {table} ADD COLUMN {name} varchar'
        self.execute(sql, commit=True)

    def select_last_workout(self, user_id: int, exercise_id: int):
        sql = f'SELECT * FROM Workouts WHERE user_id = {user_id} AND exercise_id = {exercise_id} ORDER BY workout_id DESC'
        return self.execute(sql, fetchone=True)

    def select_all_users(self):
        sql = 'SELECT * FROM Users'
        return self.execute(sql, fetchall=True)

    def select_user(self, **kwargs):
        sql = 'SELECT * FROM Users WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchone=True)

    def count_users(self):
        return self.execute('SELECT COUNT(*) FROM Users;', fetchone=True)

    # def update_email(self, email, user_id):
    #     sql = 'UPDATE Users SET email=? WHERE user_id=?'
    #     return self.execute(sql, parameters=(email, user_id), commit=True)
    #
    # def update_time_zone(self, time_zone, user_id):
    #     sql = 'UPDATE Users SET time_zone=? WHERE user_id=?'
    #     return self.execute(sql, parameters=(time_zone, user_id), commit=True)
    #
    # def update_birth_date(self, birth_date, user_id):
    #     sql = 'UPDATE Users SET birth_date=? WHERE user_id=?'
    #     return self.execute(sql, parameters=(birth_date, user_id), commit=True)
    #
    # def update_life_date(self, life_date, user_id):
    #     sql = 'UPDATE Users SET life_date=? WHERE user_id=?'
    #     return self.execute(sql, parameters=(life_date, user_id), commit=True)
    #
    # def update_life_calendar(self, life_calendar, user_id):
    #     sql = 'UPDATE Users SET life_calendar=? WHERE user_id=?'
    #     return self.execute(sql, parameters=(life_calendar, user_id), commit=True)
    #
    # def update_latitude(self, latitude, user_id):
    #     sql = 'UPDATE Users SET latitude=? WHERE user_id=?'
    #     return self.execute(sql, parameters=(latitude, user_id), commit=True)
    #
    # def update_longitude(self, longitude, user_id):
    #     sql = 'UPDATE Users SET longitude=? WHERE user_id=?'
    #     return self.execute(sql, parameters=(longitude, user_id), commit=True)

    def delete_users(self):
        self.execute('DELETE FROM Users WHERE True')

    def delete_table(self, table):
        self.execute(f'DELETE FROM {table} WHERE True')

#  можно вернуть этот логгер при необходимости в функции execute, заменив им logger.debug
# def logger(statement):
#     print(f'''
#     ______________________________________
#     Executing:
#     {statement}
#     ______________________________________
# ''')
