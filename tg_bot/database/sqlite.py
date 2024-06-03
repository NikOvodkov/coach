import datetime
import sqlite3

import dateutil

from logging_settings import logger


class SQLiteDatabase:
    def __init__(self, path_to_db='sqlite160124.db'):
        self.path_to_db = path_to_db
        self.new_path = '1716465804.db'
        self.second_path = ''
        # self.new_path = str(int(datetime.datetime.utcnow().timestamp())) + '.db'

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    @property
    def new_connection(self):
        return sqlite3.connect(self.new_path)

    @property
    def second_connection(self):
        return sqlite3.connect(self.new_path)

    def execute_through_sql(self, sql, new=False):
        self.execute(sql, commit=True, new=new)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False, new=False, script=False):
        if not parameters:
            parameters = tuple()
        if new:
            connection = self.new_connection
        else:
            connection = self.connection
        connection.set_trace_callback(logger.debug)
        cursor = connection.cursor()
        data = None
        if script:
            cursor.executescript(sql)
        else:
            cursor.execute(sql, parameters)
        if commit:
            connection.commit()
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()
        connection.close()
        return data

    def select_all_table(self, table, new=False):
        sql = f'SELECT * FROM {table}'
        return self.execute(sql, fetchall=True, new=new)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += ' AND '.join([
            f'{item} = ?' for item in parameters
        ])
        return sql, tuple(parameters.values())

    @staticmethod
    def format_add(sql, parameters: dict):
        sql += '(' + ', '.join([f'{item}' for item in parameters]) + ')'
        sql += 'VALUES(' + ','.join(['?' for item in parameters]) + ')'
        return sql, tuple(parameters.values())

    def count_rows(self, table, new=False):
        return self.execute(f'SELECT COUNT(*) FROM {table};', fetchone=True, new=new)

    def update_cell(self, table, cell, cell_value, key, key_value, new=False):
        sql = f'UPDATE {table} SET {cell}=? WHERE {key}=? '
        return self.execute(sql, parameters=(cell_value, key_value), commit=True, new=new)

    def select_row(self, table, new=False, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchone=True, new=new)

    def select_cell(self, table, column, new=False, **kwargs):
        sql = f'SELECT {column} FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchone=True, new=new)

    def select_rows(self, table, new=False, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchall=True, new=new)

    def select_column(self, table, column, new=False):
        sql = f'SELECT {column} FROM {table};'
        return self.execute(sql, fetchall=True, new=new)

    def create_table_users(self, new=False):
        sql = '''
        CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name varchar(255) NOT NULL,
        email varchar(255),
        time_zone varchar(10),
        birth_date varchar(10), /* дата начала календаря */
        life_date varchar(10),  /* дата окончания календаря */
        life_calendar varchar(255),  /* дата следующего получения календаря, либо None */
        latitude varchar(255),
        longitude varchar(255),
        status varchar(10) NOT NULL,  /* inactive, если пользователь бота заблокировал, иначе active */
        trener_sub varchar,
        weight int
        );
        '''
        self.execute(sql, commit=True, new=new)

    def add_user(self, user_id: int, name: str, email: str = None, time_zone: str = None,
                 birth_date: str = None, life_date: str = None, life_calendar: str = None,
                 latitude: str = None, longitude: str = None, status: str = 'active',
                 trener_sub: str = None, weight: int = None, new=False):
        sql = ('INSERT OR IGNORE INTO Users(user_id, Name, email, time_zone, birth_date, life_date, life_calendar, '
               'latitude, longitude, status, trener_sub, weight) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, name, email, time_zone, birth_date, life_date, life_calendar,
                      latitude, longitude, status, trener_sub, weight)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    def add_user_new(self, user_id: int, name: str, email: str = None, status: int = 1,
                     latitude: float = None, longitude: float = None, time_zone: int = None,
                     birth_date: str = None, life_date: str = None, life_calendar_sub: str = None,
                     trener_sub: str = None, weight: int = None, new=True):
        sql = ('INSERT OR IGNORE INTO users_base_long(user_id, name, email, status, latitude, longitude, time_zone, '
               'birth_date, life_date, life_calendar_sub, trener_sub, weight) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, name, email, status, latitude, longitude, time_zone,
                      birth_date, life_date, life_calendar_sub, trener_sub, weight)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    def create_table_exercises_base(self, new=False):  # таблица содержит неповторяющийся список уникальных упражнений
        sql = '''
        CREATE TABLE IF NOT EXISTS Exercises_base (
        exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        file_id varchar,
        file_unique_id varchar,
        work int
        );
        '''
        self.execute(sql, commit=True, new=new)

    def add_exercise_base(self, exercise_id: int, user_id: int, name: str, description: str = None, muscle_list: str = None,
                          duration_sec: int = None, consumption_cal: int = None, heart_load: int = None,
                          description_animation_link: str = None, description_animation: str = None,
                          description_picture_link: str = None, description_picture: str = None,
                          description_video_link: str = None, description_video: str = None,
                          description_sound_link: str = None, description_sound: str = None,
                          file_id: str = None, file_unique_id: str = None, work: int = None, new=False):
        sql = ('INSERT INTO Exercises_base (exercise_id, user_id, Name, description, muscle_list, '
               'duration_sec, consumption_cal, heart_load, '
               'description_animation_link, description_animation, description_picture_link, description_picture, '
               'description_video_link, description_video, description_sound_link, description_sound, '
               'file_id, file_unique_id, work) '
               'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (exercise_id, user_id, name, description, muscle_list, duration_sec, consumption_cal, heart_load,
                      description_animation_link, description_animation, description_picture_link, description_picture,
                      description_video_link, description_video, description_sound_link, description_sound,
                      file_id, file_unique_id, work)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    def add_exercise_base_new(self, exercise_id: int, user_id: int, name: str, description: str = None, work: float = None,
                              file_id: str = None, file_unique_id: str = None, new=True):
        sql = ('INSERT INTO Exercises_base (exercise_id, user_id, name, description, work, file_id, file_unique_id) '
               'VALUES(?,?,?,?,?,?,?)')
        parameters = (exercise_id, user_id, name, description, work, file_id, file_unique_id)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    # таблица содержит неповторяющийся список уникальных мышц (около 600 штук)
    def create_table_muscles_base(self, new=False):
        sql = '''
        CREATE TABLE IF NOT EXISTS Muscles_base (
        muscle_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        description_sound blob
        );
        '''
        self.execute(sql, commit=True, new=new)

    def add_muscle(self, user_id: int, name: str, length_mm: int = None, strength: int = None,
                   fibers_per_nerve: int = None, nerves: int = None, fibers: int = None,
                   fiber_thickness_microns: int = None, endurance: int = None, heart_load: int = None,
                   exercises_list: str = None, description: str = None, description_animation_link: str = None,
                   description_animation: str = None, description_picture_link: str = None, description_picture: str = None,
                   description_video_link: str = None, description_video: str = None,
                   description_sound_link: str = None, description_sound: str = None, new=False):
        sql = ('INSERT INTO Muscles_base (muscle_id, user_id, name, length_mm, strength, fibers_per_nerve, nerves, fibers, '
               'fiber_thickness_microns, endurance, heart_load, exercises_list, description, '
               'description_animation_link, description_animation, description_picture_link, description_picture, '
               'description_video_link, description_video, description_sound_link, description_sound) '
               'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (self.count_rows('Muscles_base')[0], user_id, name, length_mm, strength, fibers_per_nerve, nerves, fibers,
                      fiber_thickness_microns, endurance, heart_load, exercises_list, description, description_animation_link,
                      description_animation, description_picture_link, description_picture, description_video_link,
                      description_video, description_sound_link, description_sound)
        self.execute(sql, parameters=parameters, commit=True, new=new)

        # таблица содержит неповторяющийся список уникальных мышц (около 600 штук)

    def create_table_muscles_user(self, new=False):
        sql = '''
            CREATE TABLE IF NOT EXISTS Muscles_user (
            muscle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id int NOT NULL, /* id пользователя, хозяина мышцы */
            length_mm int, /* длина мышцы в мм */
            strength int, /* сила мышцы, относительная величина, пока методика расчёта не ясна */
            fibers_per_nerve int, /* мышечных волокон на 1 управляющий нерв */
            nerves int, /* всего управляющих нервов в мышце */
            fibers int, /* всего волокон в мышце */
            fiber_thickness_microns int, /* толщина волокна мышцы в мкм */
            endurance int, /* выносливость в неясных пока величинах */
            heart_load int /* нагрузка на сердце в неясных пока величинах */
            );
            '''
        self.execute(sql, commit=True, new=new)

    def add_muscle_user(self, user_id: int, length_mm: int = None, strength: int = None,
                        fibers_per_nerve: int = None, nerves: int = None, fibers: int = None,
                        fiber_thickness_microns: int = None, endurance: int = None, heart_load: int = None, new=False):
        sql = ('INSERT INTO Muscles_user (muscle_id, user_id, length_mm, strength, fibers_per_nerve, nerves, fibers, '
               'fiber_thickness_microns, endurance, heart_load) '
               'VALUES(?,?,?,?,?,?,?,?,?,?)')
        parameters = (self.count_rows('Muscles_user')[0], user_id, length_mm, strength, fibers_per_nerve, nerves, fibers,
                      fiber_thickness_microns, endurance, heart_load)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    # таблица содержит выполненные тренировки, привязанные к пользователям, невыполненные части тренировок не сохраняются
    def create_table_workouts(self, new=False):
        sql = '''
        CREATE TABLE IF NOT EXISTS Workouts (
        workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id int NOT NULL,
        exercise_id, /* поле для тренировок из одного упражнения */
        exercises_list varchar, /* список кортежей вида упражнение-количество повторений-время отдыха */
        duration_min int, /* общая реальная длительность тренировки в минутах */
        consumption_cal int, /* затраты энергии за время тренировок в калориях, включая перерывы */
        heart_load int, /* нагрузка на сердце в неясных пока величинах */
        date varchar, /* дата тренировки */
        work int,
        arms float,
        legs float,
        chest float,
        abs float,
        back float
        );
        '''
        self.execute(sql, commit=True, new=new)

    def create_table_workouts_short(self, new=True):
        sql = '''
                CREATE TABLE IF NOT EXISTS workouts_short (
                workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users_base_long (user_id),
                work REAL,
                arms REAL,
                legs REAL,
                chest REAL,
                abs REAL,
                back REAL,
                date VARCHAR(255)
                );
                '''
        self.execute(sql, commit=True, new=new)
        # пробегаемся по базе workout long, если в таблице нет этого воркаута, добавляем
        all_workouts = self.select_all_table(table='workouts_long', new=True)
        short_workouts = self.select_all_table(table='workouts_short', new=True)
        if short_workouts is None or len(short_workouts) == 0:
            workouts_voc = {}
            for workout in all_workouts:
                if workout[0] in workouts_voc and workout[7] is not None:
                    workouts_voc[workout[0]][1] += workout[7]
                    workouts_voc[workout[0]][2] += workout[8]
                    workouts_voc[workout[0]][3] += workout[9]
                    workouts_voc[workout[0]][4] += workout[10]
                    workouts_voc[workout[0]][5] += workout[11]
                    workouts_voc[workout[0]][6] += workout[12]
                else:
                    workouts_voc[workout[0]] = [workout[1], workout[7], workout[8], workout[9], workout[10],
                                                workout[11], workout[12], workout[6]]
            logger.debug(f'{workouts_voc=}')
            for workout in workouts_voc:
                sql = (f'INSERT INTO workouts_short (workout_id, user_id, work, arms, legs, chest, abs, back, date) '
                       f'VALUES(?,?,?,?,?,?,?,?,?)')
                parameters = (workout, workouts_voc[workout][0], workouts_voc[workout][1],
                              workouts_voc[workout][2], workouts_voc[workout][3], workouts_voc[workout][4],
                              workouts_voc[workout][5], workouts_voc[workout][6], workouts_voc[workout][7])
                self.execute(sql, parameters=parameters, commit=True, new=new)

    def add_workout(self, user_id: int, exercise_id: int, exercises_list: str, duration_min: int = None,
                    consumption_cal: int = None, heart_load: int = None, date: str = None, work: int = None,
                    arms: float = None, legs: float = None, chest: float = None, abs: float = None, back: float = None, new=False):
        sql = ('INSERT INTO Workouts (workout_id, user_id, exercise_id, exercises_list, '
               'duration_min, consumption_cal, heart_load, date, work, arms, legs, chest, abs, back) '
               'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (self.count_rows('Workouts')[0], user_id, exercise_id, exercises_list,
                      duration_min, consumption_cal, heart_load, date, work, arms, legs, chest, abs, back)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    def add_workout_new(self, workout_id: int, user_id: int, exercise_id: int, approach: int = None, dynamic: int = None,
                        static: int = None, date: str = None, work: float = None, arms: float = None, legs: float = None,
                        chest: float = None, abs: float = None, back: float = None, new=True):
        sql = ('INSERT INTO workouts_long (workout_id, user_id, exercise_id, approach, dynamic, static, date, work, arms, '
               'legs, chest, abs, back) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (workout_id, user_id, exercise_id, approach, dynamic, static, date, work, arms, legs, chest, abs, back)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    # таблица содержит приходы/расходы калорий
    def create_energy_balance(self, new=True):
        sql = '''
           CREATE TABLE IF NOT EXISTS energy_balance (
           user_id INTEGER REFERENCES users_base_long (user_id),
           kcal          INTEGER NOT NULL,
           proteins      INTEGER,
           fats          INTEGER,
           carbohydrates INTEGER,
           comment       VARCHAR, /* сюда записывается съеденный продукт/блюдо или тип тренировки/активности */
           date          VARCHAR(255)
           );
           '''
        self.execute(sql, commit=True, new=new)

    def add_energy(self, user_id: int, kcal: int, proteins: int = None, fats: int = None, carbohydrates: int = None,
                   comment: str = None, date: str = datetime.datetime.utcnow().isoformat(), new=True):
        sql = 'INSERT INTO energy_balance (user_id, kcal, proteins, fats, carbohydrates, comment, date) VALUES(?,?,?,?,?,?,?)'
        parameters = (user_id, kcal, proteins, fats, carbohydrates, comment, date)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    # таблица содержит историю взвешиваний
    def create_weight_table(self, new=True):
        sql = '''
           CREATE TABLE IF NOT EXISTS users_weights_long (
           user_id INTEGER REFERENCES users_base_long (user_id),
           weight        INTEGER NOT NULL,
           fat           INTEGER,
           date          VARCHAR(255)
           );
           '''
        self.execute(sql, commit=True, new=new)

    def add_weight(self, user_id: int, weight: int, fat: int = None, date: str = datetime.datetime.utcnow().isoformat(), new=True):
        sql = 'INSERT INTO users_weights_long (user_id, weight, fat, date) VALUES(?,?,?,?)'
        parameters = (user_id, weight, fat, date)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    # таблица содержит список групп мышц
    def create_table_muscle_groups(self, new=False):
        sql = '''
           CREATE TABLE IF NOT EXISTS Muscle_groups_base (
           group_id INTEGER PRIMARY KEY AUTOINCREMENT,
           name varchar NOT NULL, /* имя мышечной группы */
           mass real /* относительная масса мышечной группы */
           );
           '''
        self.execute(sql, commit=True, new=new)


    def add_muscle_group(self, group_id: int, name: str, mass: float, new=False):
        sql = 'INSERT OR IGNORE INTO Muscle_groups_base (group_id, name, mass) VALUES(?,?,?)'
        parameters = (group_id, name, mass)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    # таблица содержит список групп мышц
    def create_table_muscles_exercises_base(self, new=False):
        sql = '''
           CREATE TABLE IF NOT EXISTS Muscles_exercises_base (
           exercise_id INTEGER PRIMARY KEY,
           exercise_name varchar NOT NULL, /* название упражнения */
           muscle_group_id INTEGER,
           muscle_group_name varchar NOT NULL, /* имя мышечной группы */
           load real /* относительная загрузка мышечной группы */
           );
           '''
        self.execute(sql, commit=True, new=new)

    def add_muscles_exercises(self, exercise_id: int, exercise_name: str, muscle_group_id: int,
                              muscle_group_name: str, load: float, new=False):
        sql = ('INSERT OR IGNORE INTO Muscles_exercises_base (exercise_id, exercise_name, muscle_group_id,'
               'muscle_group_name, load) VALUES(?,?,?,?,?)')
        parameters = (exercise_id, exercise_name, muscle_group_id, muscle_group_name, load)
        self.execute(sql, parameters=parameters, commit=True, new=new)

    def add_column(self, table: str, name: str, new=False):
        sql = f'ALTER TABLE {table} ADD COLUMN {name} varchar'
        self.execute(sql, commit=True, new=new)

    def select_last_workout(self, user_id: int, exercise_id: int, new=False):
        sql = f'SELECT * FROM Workouts WHERE user_id = {user_id} AND exercise_id = {exercise_id} ORDER BY workout_id DESC'
        return self.execute(sql, fetchone=True, new=new)

    def select_last_workout_new(self, user_id: int, exercise_id: int = None, new=True):
        sql = (f'SELECT * FROM workouts_long WHERE user_id = {user_id} AND exercise_id = {exercise_id} '
               f'ORDER BY workout_id DESC, approach ASC')
        return self.execute(sql, fetchall=True, new=new)

    def select_all_users(self, new=False):
        sql = 'SELECT * FROM Users'
        return self.execute(sql, fetchall=True, new=new)

    def select_user(self, new=False, **kwargs):
        sql = 'SELECT * FROM Users WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchone=True, new=new)

    def select_table(self, table, new=False, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetchone=True, new=new)

    def count_users(self, new=False):
        return self.execute('SELECT COUNT(*) FROM Users;', fetchone=True, new=new)

    def count_table(self, table, new=False):
        return self.execute(f'SELECT COUNT(*) FROM {table};', fetchone=True, new=new)

    def delete_table(self, table, new=False):
        self.execute(f'DELETE FROM {table} WHERE True', new=new)

    @staticmethod
    def oldtime_to_newtime(time: str) -> str:
        if time:
            dt = dateutil.parser.parse(time, fuzzy=True)
            return dt.isoformat()
        else:
            return

    @staticmethod
    def dt_to_str(dt: datetime) -> str:
        if dt:
            return dt.isoformat()
        else:
            return

    def add_sex_height(self):
        sql = '''
        ALTER TABLE users_base_long ADD height INTEGER;
        ALTER TABLE users_base_long ADD sex VARCHAR(1);
        '''
        self.execute(sql, commit=True, new=True, script=True)

    def create_new_db_and_copy_data(self) -> str:
        sql = '''
                CREATE TABLE IF NOT EXISTS users_base_long (
                user_id INTEGER PRIMARY KEY NOT NULL,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                status INTEGER NOT NULL DEFAULT 1,  /* 0, если пользователь бота заблокировал, иначе 1 */
                latitude REAL,
                longitude REAL,
                time_zone INTEGER,
                birth_date VARCHAR(255), /* дата рождения - дата начала календаря */
                life_date VARCHAR(255),  /* дата окончания календаря */
                life_calendar_sub VARCHAR(255),  /* дата следующего получения календаря, либо None */
                trener_sub VARCHAR(255),  /* дата следующего напоминания тренера, либо None */
                weight INTEGER
                );
                CREATE TABLE IF NOT EXISTS exercises_base (
                exercise_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                user_id INTEGER REFERENCES users_base_long (user_id),  /* id пользователя, внёсшего упражнение в базу */
                name VARCHAR(255) NOT NULL,  /* наименование упражнения (ёмкое, чёткое, подробное, но компактное) */
                description VARCHAR,  /* подробное описание */
                work REAL,  /* выполняемая в упражнении работа за 1 повторение на 1 кг веса спортсмена */
                file_id VARCHAR(255),
                file_unique_id VARCHAR(255)
                );
                CREATE TABLE IF NOT EXISTS muscles_base (
                muscle_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name VARCHAR(255) NOT NULL, /* имя мышцы */
                group_id INTEGER NOT NULL,
                group_name VARCHAR(255) NOT NULL, /* имя мышечной группы */
                mass REAL /* относительная масса мышцы в общей мышечной массе туловища */
                );
                CREATE TABLE IF NOT EXISTS exercises_muscles_base (
                exercise_id INTEGER REFERENCES exercises_base (exercise_id),
                exercise_name VARCHAR(255) REFERENCES exercises_base (name), /* название упражнения */
                muscle_id INTEGER REFERENCES muscles_base (muscle_id),
                muscle_name VARCHAR(255) REFERENCES muscles_base (name), /* имя мышечной группы */
                load REAL /* относительная загрузка мышечной группы в упражнении относительно всех мышц */
                );
                CREATE TABLE IF NOT EXISTS workouts_long (
                workout_id INTEGER NOT NULL, /* номер тренировки (из одного упражнения) */
                user_id INTEGER REFERENCES users_base_long (user_id), /* пользователь */
                exercise_id INTEGER REFERENCES exercises_base_long (exercise_id), /* упражнение */
                approach INTEGER, /* номер подхода в упражнении, обычно 1-5 */
                dynamic INTEGER, /* количество повторений в подходе */
                static INTEGER, /* задержка в секундах в подходе*/
                date VARCHAR(255), /* дата тренировки */
                work REAL, /* работа, выполненная за данный подход */
                arms REAL, /* часть работы, выполненной мышцами рук */
                legs REAL, /* часть работы, выполненной мышцами ног */
                chest REAL, /* часть работы, выполненной мышцами груди */
                abs REAL, /* часть работы, выполненной мышцами пресса */
                back REAL /* часть работы, выполненной мышцами спины */
                );
                CREATE TABLE IF NOT EXISTS users_muscles_long (
                user_id INTEGER REFERENCES users_base_long (user_id), /* пользователь */
                user_name VARCHAR(255) REFERENCES users_base_long (name), /* имя пользователя */
                muscle_id INTEGER REFERENCES muscles_base (muscle_id), /* мышечная группа */
                muscle_name VARCHAR(255) REFERENCES muscles_base (name), /* мышечная группа */
                weight REAL, /* фактическая масса у данного пользователя */
                mass REAL, /* размер части от общей мышечной массы данного пользователя */
                mark REAL /* оценка группы мышц по результатам тренировки или её отсутствия */
                );
                CREATE TABLE IF NOT EXISTS equipment_base (
                equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL, /* название */
                description VARCHAR /* описание */
                );
                CREATE TABLE IF NOT EXISTS exercises_equipment_base (
                exercise_id INTEGER REFERENCES exercises_base (exercise_id),
                exercise_name VARCHAR(255) REFERENCES exercises_base (name), /* название */
                equipment_id INTEGER REFERENCES equipment_base (equipment_id),
                equipment_name VARCHAR(255) REFERENCES equipment_base (name) /* название */
                );
                '''
        self.execute(sql, commit=True, new=True, script=True)
        sql = '''
                ATTACH DATABASE 'sqlite160124.db' AS olddb;
                
                CREATE TABLE IF NOT EXISTS multimedia AS SELECT multimedia_id, name, type, file_id, file_unique_id  FROM olddb.Multimedia;
                
                INSERT INTO users_base_long (user_id, name, email)
                SELECT user_id, Name, email FROM olddb.Users;
                
                INSERT INTO exercises_base (exercise_id, user_id, name, file_id, file_unique_id)
                SELECT exercise_id, user_id, Name, file_id, file_unique_id FROM olddb.Exercises_base;
        
                INSERT INTO muscles_base (muscle_id, name, group_id, group_name, mass)
                SELECT group_id, name, group_id, name, mass FROM olddb.Muscle_groups_base;
                
                INSERT INTO exercises_muscles_base (exercise_id, exercise_name, muscle_id, muscle_name, load)
                SELECT exercise_id, exercise_name, muscle_group_id, muscle_group_name, load FROM olddb.Muscles_exercises_base;
                
                        '''
        self.execute(sql, commit=True, new=True, script=True)

        # копируем таблицу Workouts 2
        olddb = self.select_all_table(table='Workouts')
        for olddb_str in olddb:
            dynamic = list(map(int, olddb_str[3].split()))
            dynamic_sum = sum(dynamic)
            work = []
            if olddb_str[8]:
                work = [[float(x) / dynamic_sum * y for x in olddb_str[8:]] for y in dynamic]
            else:
                work = [[None for x in olddb_str[8:]] for y in dynamic]
            sql = (f'INSERT INTO workouts_long (workout_id, user_id, exercise_id, approach, dynamic, static, date,'
                   f' work, arms, legs, chest, abs, back) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);')
            parameters = (olddb_str[0], olddb_str[1], olddb_str[2], 1, dynamic[0], 0, self.oldtime_to_newtime(olddb_str[7]),
                          *work[0])
            self.execute(sql, commit=True, new=True, parameters=parameters)
            sql = (f'INSERT INTO workouts_long (workout_id, user_id, exercise_id, approach, dynamic, static, date,'
                   f' work, arms, legs, chest, abs, back) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);')
            parameters = (olddb_str[0], olddb_str[1], olddb_str[2], 2, dynamic[1], 0, self.oldtime_to_newtime(olddb_str[7]),
                          *work[1])
            self.execute(sql, commit=True, new=True, parameters=parameters)
            sql = (f'INSERT INTO workouts_long (workout_id, user_id, exercise_id, approach, dynamic, static, date,'
                   f' work, arms, legs, chest, abs, back) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);')
            parameters = (olddb_str[0], olddb_str[1], olddb_str[2], 3, dynamic[2], 0, self.oldtime_to_newtime(olddb_str[7]),
                          *work[2])
            self.execute(sql, commit=True, new=True, parameters=parameters)
            sql = (f'INSERT INTO workouts_long (workout_id, user_id, exercise_id, approach, dynamic, static, date,'
                   f' work, arms, legs, chest, abs, back) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);')
            parameters = (olddb_str[0], olddb_str[1], olddb_str[2], 4, dynamic[3], 0, self.oldtime_to_newtime(olddb_str[7]),
                          *work[3])
            self.execute(sql, commit=True, new=True, parameters=parameters)
            sql = (f'INSERT INTO workouts_long (workout_id, user_id, exercise_id, approach, dynamic, static, date,'
                   f' work, arms, legs, chest, abs, back) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);')
            if olddb_str[7]:
                if olddb_str[4]:
                    tt = olddb_str[7] + f'T0{olddb_str[4] // 60}:{str(olddb_str[4] % 60).rjust(2, "0")}:00'
                else:
                    tt = olddb_str[7]
            else:
                tt = None
            parameters = (olddb_str[0], olddb_str[1], olddb_str[2], 5, dynamic[4], 0, self.oldtime_to_newtime(tt),
                          *work[4])
            self.execute(sql, commit=True, new=True, parameters=parameters)

        # копируем таблицу Exercises_base
        olddb = self.select_all_table(table='Exercises_base')
        for olddb_str in olddb:
            self.update_cell(table='exercises_base', cell='work', cell_value=float(olddb_str[18]),
                             key='exercise_id', key_value=olddb_str[0], new=True)

        # копируем таблицу Users
        olddb = self.select_all_table(table='Users')
        for olddb_str in olddb:
            if olddb_str[7]:
                latitude = float(olddb_str[7])
            else:
                latitude = None
            self.update_cell(table='users_base_long', cell='latitude', cell_value=latitude,
                             key='user_id', key_value=olddb_str[0], new=True)
            if olddb_str[8]:
                longitude = float(olddb_str[8])
            else:
                longitude = None
            self.update_cell(table='users_base_long', cell='longitude', cell_value=longitude,
                             key='user_id', key_value=olddb_str[0], new=True)
            if olddb_str[3]:
                time_zone = int(olddb_str[3])
            else:
                time_zone = None
            self.update_cell(table='users_base_long', cell='time_zone', cell_value=time_zone,
                             key='user_id', key_value=olddb_str[0], new=True)
            self.update_cell(table='users_base_long', cell='birth_date', cell_value=self.oldtime_to_newtime(olddb_str[4]),
                             key='user_id', key_value=olddb_str[0], new=True)
            self.update_cell(table='users_base_long', cell='life_date', cell_value=self.oldtime_to_newtime(olddb_str[5]),
                             key='user_id', key_value=olddb_str[0], new=True)
            self.update_cell(table='users_base_long', cell='life_calendar_sub', cell_value=self.oldtime_to_newtime(olddb_str[6]),
                             key='user_id', key_value=olddb_str[0], new=True)
            if olddb_str[11]:
                weight = int(olddb_str[11])
            else:
                weight = None
            self.update_cell(table='users_base_long', cell='weight', cell_value=weight,
                             key='user_id', key_value=olddb_str[0], new=True)
            if olddb_str[9] == 'active':
                status = 1
            else:
                status = 0
            self.update_cell(table='users_base_long', cell='status', cell_value=status,
                             key='user_id', key_value=olddb_str[0], new=True)
        return self.new_path

#  можно вернуть этот логгер при необходимости в функции execute, заменив им logger.debug
# def logger(statement):
#     print(f'''
#     ______________________________________
#     Executing:
#     {statement}
#     ______________________________________
# ''')
