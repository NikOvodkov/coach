import datetime
import sqlite3

import dateutil

from logging_settings import logger


class SQLiteDatabase:
    def __init__(self, path_to_db='1716465804.db'):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute_through_sql(self, sql):
        self.execute(sql, commit=True)

    def execute(self, sql: str, parameters: tuple = None, fetch: str = None, commit=False, script=False, tuple_=False):
        if not parameters:
            parameters = tuple()
        connection = self.connection
        if not tuple_:
            connection.row_factory = sqlite3.Row
        connection.set_trace_callback(logger.debug)
        cursor = connection.cursor()
        data = None
        try:
            if script:
                cursor.executescript(sql)
            else:
                cursor.execute(sql, parameters)
        except sqlite3.Error as er:
            logger.debug('____________ОПЕРАЦИЯ НЕ ВЫПОЛНЕНА!!!_________')
            logger.debug(er.sqlite_errorcode)  # Prints 275
            logger.debug(er.sqlite_errorname)  # Prints SQLITE_CONSTRAINT_CHECK
            connection.close()
            return
        if commit:
            connection.commit()
        if fetch == 'one':
            data = cursor.fetchone()
        elif fetch == 'all':
            data = cursor.fetchall()
        elif fetch == 'many':
            data = cursor.fetchmany()
        connection.close()
        return data

    @staticmethod
    def format_args(sql, parameters: dict = None):
        if parameters:
            sql += ' AND '.join([
                f'{item} = ?' for item in parameters
            ])
            return sql, tuple(parameters.values())
        else:
            return sql

    @staticmethod
    def format_add(sql, parameters: dict):
        sql += '(' + ', '.join([f'{item}' for item in parameters]) + ')'
        sql += 'VALUES(' + ','.join(['?' for item in parameters]) + ')'
        return sql, tuple(parameters.values())

    def create_table_users(self):
        sql = '''
         CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY NOT NULL,
                referrer INTEGER,
                coach_id INTEGER,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                status INTEGER NOT NULL DEFAULT 1,  /* 0, если пользователь бота заблокировал, иначе 1 */
                latitude REAL,
                longitude REAL,
                time_zone INTEGER,
                birth_date VARCHAR(255), /* дата рождения - дата начала календаря */
                life_date VARCHAR(255),  /* дата окончания календаря */
                life_calendar_sub VARCHAR(255),  /* дата следующего получения календаря, либо None */
                coach_sub VARCHAR(255),  /* дата следующего напоминания тренера, либо None */
                weight INTEGER,
                height INTEGER,
                sex VARCHAR(1),
                arms_level REAL,
                legs_level REAL,
                chest_level REAL,
                abs_level REAL,
                back_level REAL
                );
         INSERT OR IGNORE INTO users (user_id, name, email, status, latitude, longitude, time_zone, birth_date, life_date,
                                      life_calendar_sub, coach_sub, weight, height, sex)
         SELECT user_id, name, email, status, latitude, longitude, time_zone, birth_date, life_date,
                                      life_calendar_sub, trener_sub, weight, height, sex FROM users_base_long;
        '''
        self.execute(sql, commit=True, script=True)

    def add_user(self, user_id: int, name: str, email: str = None, status: int = 1,
                 latitude: float = None, longitude: float = None, time_zone: int = None,
                 birth_date: str = None, life_date: str = None, life_calendar_sub: str = None,
                 trener_sub: str = None, weight: int = None, arms_level: float = None, legs_level: float = None,
                 chest_level: float = None, abs_level: float = None, back_level: float = None):
        sql = ('INSERT OR IGNORE INTO users(user_id, name, email, status, latitude, longitude, time_zone, '
               'birth_date, life_date, life_calendar_sub, trener_sub, weight,'
               'arms_level, legs_level, chest_level, abs_level, back_level) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, name, email, status, latitude, longitude, time_zone,
                      birth_date, life_date, life_calendar_sub, trener_sub, weight,
                      arms_level, legs_level, chest_level, abs_level, back_level)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_exercises(self):  # таблица содержит неповторяющийся список уникальных упражнений
        sql = '''
        CREATE TABLE IF NOT EXISTS exercises (
                exercise_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                user_id INTEGER REFERENCES users (user_id),  /* id пользователя, внёсшего упражнение в базу */
                type INTEGER, /*1-динамика/2-статика/3-разминка/4-заминка/5-тренировка/0-таймер*/
                name VARCHAR(255) NOT NULL,  /* наименование упражнения (ёмкое, чёткое, подробное, но компактное) */
                description VARCHAR,  /* подробное описание */
                description_text_link VARCHAR,  /* ссылка на подробное описание упражнения */
                description_video_link VARCHAR,  /* ссылка на подробное описание упражнения */
                work REAL,  /* выполняемая в упражнении работа за 1 повторение на 1 кг веса спортсмена */
                file_id VARCHAR(255),
                file_unique_id VARCHAR(255)
                );
        INSERT OR IGNORE INTO exercises (exercise_id, user_id, name, work, file_id, file_unique_id)
                SELECT exercise_id, user_id, name, work, file_id, file_unique_id FROM exercises_base;
        '''
        self.execute(sql, commit=True, script=True)

    def add_exercise(self, user_id: int, type_: int, name: str, description: str = None, description_text_link: str = None,
                     description_video_link: str = None, work: float = None, file_id: str = None, file_unique_id: str = None):
        sql = ('INSERT INTO exercises (user_id, type, name, description, '
               'description_text_link, description_video_link, work, file_id, file_unique_id) '
               'VALUES(?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, type_, name, description, description_text_link, description_video_link,
                      work, file_id, file_unique_id)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_materials(self):  # таблица содержит материалы, предложенные на модерацию
        sql = '''
        CREATE TABLE IF NOT EXISTS materials (
                material_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                user_id INTEGER REFERENCES users (user_id) NOT NULL,  /* id пользователя, предложившего материал */
                type INTEGER NOT NULL, /*1-динамика/2-статика/3-разминка/4-заминка/5-тренировка/0-таймер*/
                exercise_id INTEGER REFERENCES exercises (exercise_id),  /* id редактируемого упражнения */
                name VARCHAR(255),  /* наименование упражнения (ёмкое, чёткое, подробное, но компактное) */
                description VARCHAR,  /* короткое текстовое описание упражнения */
                description_text_link VARCHAR,  /* ссылка на подробное описание упражнения */
                description_video_link VARCHAR,  /* ссылка на подробное описание упражнения */
                file_id VARCHAR(255),
                file_unique_id VARCHAR(255),
                date VARCHAR(31) /* дата запроса модерации */
                );
        '''
        self.execute(sql, commit=True)

    def add_material(self, user_id: int, type_: int, exercise_id: int = None, name: str = None, description: str = None,
                     text: str = None, video: str = None, file_id: str = None, file_unique_id: str = None, date: str = None):
        sql = ('INSERT INTO materials (user_id, type, exercise_id, name, description, '
               'description_text_link, description_video_link, file_id, file_unique_id, date) '
               'VALUES(?,?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, type_, exercise_id, name, description, text, video, file_id, file_unique_id, date)
        logger.debug(f'{sql=} {parameters=}')
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_exercises_users(self):  # таблица содержит ссылки на личные настроенные базы упражнений пользователей
        sql = '''
        CREATE TABLE IF NOT EXISTS exercises_users (
                user_id INTEGER REFERENCES users (user_id),  /* id пользователя */
                exercise_id INTEGER REFERENCES exercises (exercise_id), /* id упражнения */
                list INTEGER DEFAULT NULL,  /* белый=1/черный=0 */
                weighting INTEGER DEFAULT 0,  /* текущее утяжеление в упражнении */
                arms REAL,  /* нагрузка на руки в упражнении с текущим утяжелением*/
                legs REAL,  /* нагрузка на ноги в упражнении с текущим утяжелением*/
                chest REAL,  /* нагрузка на грудь в упражнении с текущим утяжелением*/
                abs REAL,  /* нагрузка на живот в упражнении с текущим утяжелением*/
                back REAL  /* нагрузка на спину в упражнении с текущим утяжелением*/
                );
        '''
        self.execute(sql, commit=True)

    def add_exercise_user(self, user_id: int, exercise_id: int, list_: int = None, weighting: int = 0, arms: float = None,
                          legs: float = None, chest: float = None, abs_: float = None, back: float = None):
        sql = ('INSERT INTO exercises_users (user_id, exercise_id, list, weighting, arms, legs, chest, abs, back) '
               'VALUES(?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, exercise_id, list_, weighting, arms, legs, chest, abs_, back)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_muscles(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS muscles (
                muscle_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name VARCHAR(255) NOT NULL, /* имя мышцы */
                group_id INTEGER NOT NULL,
                group_name VARCHAR(255) NOT NULL, /* имя мышечной группы */
                mass REAL /* относительная масса мышцы в общей мышечной массе туловища */
                );
        INSERT OR IGNORE INTO muscles (muscle_id, name, group_id, group_name, mass)
        SELECT * FROM muscles_base;
        '''
        self.execute(sql, commit=True, script=True)

    def add_muscle(self, muscle_id: int, name: str, group_id: int, group_name: str, mass: float):
        sql = 'INSERT OR IGNORE INTO muscles (muscle_id, name, group_id, group_name, mass) VALUES(?,?,?,?,?)'
        parameters = (muscle_id, name, group_id, group_name, mass)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_exercises_muscles(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS exercises_muscles (
                exercise_id INTEGER REFERENCES exercises (exercise_id),
                exercise_name VARCHAR(255) REFERENCES exercises (name), /* название упражнения */
                muscle_id INTEGER REFERENCES muscles (muscle_id),
                muscle_name VARCHAR(255) REFERENCES muscles (name), /* имя мышечной группы */
                level REAL, /* уровень сложности упражнения */
                load REAL /* относительная загрузка мышечной группы в упражнении относительно всех мышц */
                );
        INSERT OR IGNORE INTO exercises_muscles (exercise_id, exercise_name, muscle_id, muscle_name, load)
        SELECT * FROM exercises_muscles_base;
        '''
        self.execute(sql, commit=True, script=True)

    def add_exercises_muscles(self, exercise_id: int, exercise_name: str, muscle_id: int, muscle_name: str,
                              level: float, load: float):
        sql = ('INSERT OR IGNORE INTO exercises_muscles (exercise_id, exercise_name, muscle_id, muscle_name, level, load)'
               ' VALUES(?,?,?,?,?,?)')
        parameters = (exercise_id, exercise_name, muscle_id, muscle_name, level, load)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_workouts(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS workouts (
                workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users (user_id),
                date VARCHAR(31),
                exercise_id INTEGER REFERENCES exercises (exercise_id),
                approaches INTEGER,
                work REAL,
                arms REAL,
                legs REAL,
                chest REAL,
                abs REAL,
                back REAL
                );
        INSERT OR IGNORE INTO workouts (workout_id, user_id, date, approaches, work, arms, legs, chest, abs, back)
        SELECT * FROM workouts_short;
        '''
        self.execute(sql, commit=True, script=True)

    def add_workout(self, workout_id: int, user_id: int, date: str, exercise_id: int, approaches: int,
                    work: float, arms: float, legs: float, chest: float, abs_: float, back: float):
        sql = (f'INSERT OR IGNORE INTO workouts (workout_id, user_id, date, exercise_id, approaches,'
               f' work, arms, legs, chest, abs, back) VALUES(?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (workout_id, user_id, date, exercise_id, approaches, work, arms, legs, chest, abs_, back)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_approaches(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS approaches (
                approach_id INTEGER GENERATED ALWAYS AS ((workout_id * 100) + number) STORED UNIQUE, /* уникальный номер подхода */
                workout_id INTEGER NOT NULL, /* номер тренировки (из одного упражнения) */
                user_id INTEGER REFERENCES users (user_id), /* пользователь */
                exercise_id INTEGER REFERENCES exercises (exercise_id), /* упражнение */
                number INTEGER, /* номер подхода в упражнении, обычно 1-5 */
                
                dynamic INTEGER, /* количество повторений в подходе */
                static INTEGER, /* задержка в секундах в подходе*/
                date VARCHAR(31), /* дата тренировки */
                work REAL, /* работа, выполненная за данный подход */
                arms REAL, /* часть работы, выполненной мышцами рук */
                legs REAL, /* часть работы, выполненной мышцами ног */
                chest REAL, /* часть работы, выполненной мышцами груди */
                abs REAL, /* часть работы, выполненной мышцами пресса */
                back REAL /* часть работы, выполненной мышцами спины */
                );
        INSERT OR IGNORE INTO approaches (workout_id, user_id, exercise_id, number, dynamic, static, date,
                                          work, arms, legs, chest, abs, back)
        SELECT workout_id, user_id, exercise_id, approach, dynamic, static, date,
               work, arms, legs, chest, abs, back FROM workouts_long;
        '''
        self.execute(sql, commit=True, script=True)

    def add_approach(self, workout_id: int, user_id: int, exercise_id: int, number: int, dynamic: int, static: int,
                     date: str, work: float, arms: float, legs: float, chest: float, abs_: float, back: float):
        sql = ('INSERT OR IGNORE INTO approaches (workout_id, user_id, exercise_id, number, dynamic, static, date, '
               'work, arms, legs, chest, abs, back) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (workout_id, user_id, exercise_id, number, dynamic, static, date, work, arms, legs, chest, abs_, back)
        self.execute(sql, parameters=parameters, commit=True)

    def select_last_approaches(self, user_id: int, exercise_id: int = None):
        sql = (f'SELECT * FROM approaches WHERE user_id = {user_id} AND exercise_id = {exercise_id} '
               f'ORDER BY workout_id DESC, number ASC')
        return self.execute(sql, fetch='all')

    def create_table_energy(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS energy (
                user_id INTEGER REFERENCES users (user_id),
                kcal          INTEGER NOT NULL,
                proteins      INTEGER,
                fats          INTEGER,
                carbohydrates INTEGER,
                comment       VARCHAR, /* сюда записывается съеденный продукт/блюдо или тип тренировки/активности */
                date          VARCHAR(31)
                );
        INSERT OR IGNORE INTO energy (user_id, kcal, proteins, fats, carbohydrates, comment, date)
        SELECT * FROM energy_balance;
        '''
        self.execute(sql, commit=True, script=True)

    def add_energy(self, user_id: int, kcal: int, proteins: int = None, fats: int = None, carbohydrates: int = None,
                   comment: str = None, date: str = datetime.datetime.utcnow().isoformat()):
        sql = 'INSERT OR IGNORE INTO energy (user_id, kcal, proteins, fats, carbohydrates, comment, date) VALUES(?,?,?,?,?,?,?)'
        parameters = (user_id, kcal, proteins, fats, carbohydrates, comment, date)
        self.execute(sql, parameters=parameters, commit=True)

        # таблица содержит историю взвешиваний

    def create_table_weight(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS users_weights (
                user_id INTEGER REFERENCES users (user_id),
                weight  INTEGER NOT NULL,
                fat     INTEGER,
                date    VARCHAR(255)
                );
        INSERT OR IGNORE INTO users_weights (user_id, weight, fat, date)
        SELECT * FROM users_weights_long;
        '''
        self.execute(sql, commit=True, script=True)

    def add_weight(self, user_id: int, weight: int, fat: int = None, date: str = datetime.datetime.utcnow().isoformat()):
        sql = 'INSERT OR IGNORE INTO users_weights (user_id, weight, fat, date) VALUES(?,?,?,?)'
        parameters = (user_id, weight, fat, date)
        self.execute(sql, parameters=parameters, commit=True)

    #################################################################################

    def clear_table(self, table):
        self.execute(f'DELETE FROM {table} WHERE True', commit=True)

    def delete_table(self, table):
        self.execute(f'DROP TABLE IF EXISTS {table};', commit=True)

    def select_table(self, table, tuple_=False):
        sql = f'SELECT * FROM {table}'
        return self.execute(sql, fetch='all', tuple_=tuple_)

    def count_rows(self, table):
        return self.execute(f'SELECT COUNT(*) FROM {table};', fetch='one')

    def delete_rows(self, table, **kwargs):
        sql = f'DELETE FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, commit=True)

    def select_rows(self, table, fetch, tuple_=False, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetch=fetch, tuple_=tuple_)

    def select_filtered_sorted_rows(self, table, fetch, sql2: str = '', tuple_=False, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        '''
        ORDER BY workout_id DESC, number ASC
        ORDER BY LENGTH(column_name) DESC LIMIT 1;
        '''
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql + sql2, parameters, fetch=fetch, tuple_=tuple_)

    def update_cell(self, table, cell, cell_value, key, key_value):
        sql = f'UPDATE {table} SET {cell}=? WHERE {key}=? '
        return self.execute(sql, parameters=(cell_value, key_value), commit=True)

    def update_cell_new(self, table, cell, cell_value, **kwargs):
        sql = f'UPDATE {table} SET {cell}=? WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, (cell_value, *parameters), commit=True)

    def update_cells(self, table, cells, **kwargs):
        sql = ', '.join([f'{cell}={cells[cell]}' for cell in cells])
        sql = f'UPDATE {table} SET {sql} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, commit=True)

    def filter(self, table, fetch, tuple_=False, **kwargs):
        sql = f'SELECT * FROM {table} WHERE '
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters, fetch=fetch, tuple_=tuple_)

    ##############################################################################################

    def add_workout_short(self, workout_id: int, user_id: int, date: str, approaches: int,
                          work: float, arms: float, legs: float, chest: float, abs_: float, back: float):
        sql = ('INSERT INTO workouts_short (workout_id, user_id, date, approaches, work, arms, legs, chest, abs, back) '
               'VALUES(?,?,?,?,?,?,?,?,?,?)')
        parameters = (workout_id, user_id, date, approaches, work, arms, legs, chest, abs_, back)
        self.execute(sql, parameters=parameters, commit=True)

    def add_workout_new(self, workout_id: int, user_id: int, exercise_id: int, approach: int = None, dynamic: int = None,
                        static: int = None, date: str = None, work: float = None, arms: float = None, legs: float = None,
                        chest: float = None, abs_: float = None, back: float = None):
        sql = ('INSERT INTO workouts_long (workout_id, user_id, exercise_id, approach, dynamic, static, date, work, arms, '
               'legs, chest, abs, back) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (workout_id, user_id, exercise_id, approach, dynamic, static, date, work, arms, legs, chest, abs_, back)
        self.execute(sql, parameters=parameters, commit=True)

    def select_last_workout(self, user_id: int, exercise_id: int = None, tuple_=False):
        sql = (f'SELECT * FROM approaches WHERE user_id = {user_id} AND exercise_id = {exercise_id} '
               f'ORDER BY workout_id DESC, number ASC')
        return self.execute(sql, fetch='all', tuple_=tuple_)

    def add_user_new(self, user_id: int, name: str, email: str = None, status: int = 1,
                     latitude: float = None, longitude: float = None, time_zone: int = None,
                     birth_date: str = None, life_date: str = None, life_calendar_sub: str = None,
                     trener_sub: str = None, weight: int = None):
        sql = ('INSERT OR IGNORE INTO users_base_long (user_id, name, email, status, latitude, longitude, time_zone, '
               'birth_date, life_date, life_calendar_sub, trener_sub, weight) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)')
        parameters = (user_id, name, email, status, latitude, longitude, time_zone,
                      birth_date, life_date, life_calendar_sub, trener_sub, weight)
        self.execute(sql, parameters=parameters, commit=True)

    def create_table_workouts_short(self):
        sql = '''
                CREATE TABLE IF NOT EXISTS workouts_short (
                workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users_base_long (user_id),
                date VARCHAR(255),
                approaches INTEGER,
                work REAL,
                arms REAL,
                legs REAL,
                chest REAL,
                abs REAL,
                back REAL
                );
                '''
        self.execute(sql, commit=True)
        # пробегаемся по базе workout long, если в таблице нет этого воркаута, добавляем
        all_workouts = self.select_table(table='workouts_long', tuple_=True)
        logger.debug(f'{all_workouts=}')
        short_workouts = self.select_table(table='workouts_short', tuple_=True)
        if short_workouts is None or len(short_workouts) == 0:
            workouts_voc = {}
            for workout in all_workouts:
                if workout[0] in workouts_voc:
                    workouts_voc[workout[0]][0] = workout[1]
                    workouts_voc[workout[0]][1] = workout[6]
                    workouts_voc[workout[0]][2] += 1
                    if workout[7] is not None:
                        workouts_voc[workout[0]][3] += workout[7]
                        workouts_voc[workout[0]][4] += workout[8]
                        workouts_voc[workout[0]][5] += workout[9]
                        workouts_voc[workout[0]][6] += workout[10]
                        workouts_voc[workout[0]][7] += workout[11]
                        workouts_voc[workout[0]][8] += workout[12]
                else:
                    workouts_voc[workout[0]] = [workout[1], workout[6], 1,
                                                workout[7], workout[8], workout[9], workout[10], workout[11], workout[12]]
            logger.debug(f'{workouts_voc=}')
            for workout in workouts_voc:
                sql = (f'INSERT INTO workouts_short (workout_id, user_id, date, approaches, work, arms, legs, chest, abs, back) '
                       f'VALUES(?,?,?,?,?,?,?,?,?,?)')
                parameters = (workout, workouts_voc[workout][0], workouts_voc[workout][1], workouts_voc[workout][2],
                              workouts_voc[workout][3], workouts_voc[workout][4], workouts_voc[workout][5],
                              workouts_voc[workout][6], workouts_voc[workout][7], workouts_voc[workout][8])
                self.execute(sql, parameters=parameters, commit=True)

    def change_repeated_approaches(self):
        """
        1. создаём пустое множество номеров подходов
        2. генерируем новый номер подхода и добавляем в множество если нет, если есть меняем номер подхода на +1
        :param user_id:
        :param exercise_id:
        :param tuple_:
        :return:
        """
        ind = True
        while ind:
            ind = False
            apps_set = set()
            approaches = self.select_table('workouts_long')
            row_id = 0
            for approach in approaches:
                row_id += 1
                new_number = approach['workout_id'] * 100 + approach['approach']
                if new_number in apps_set:
                    ind = True
                    self.update_cell('workouts_long', 'approach', approach['approach'] + 1, 'rowid', row_id)
                else:
                    apps_set.add(new_number)
        logger.debug('workouts now unique')

    def add_sex_height(self):
        sql = '''
        ALTER TABLE users ADD height INTEGER;
        ALTER TABLE users ADD sex VARCHAR(1);
        '''
        self.execute(sql, commit=True, script=True)

    def add_descriptions(self):
        sql = '''
        ALTER TABLE exercises ADD description_text_link VARCHAR;
        ALTER TABLE exercises ADD description_video_link VARCHAR;
        '''
        self.execute(sql, commit=True, script=True)

    def set_type_1(self):
        self.execute(sql='UPDATE exercises SET type = 1;', commit=True)

    def add_levels(self):
        sql = '''
        ALTER TABLE exercises_muscles ADD level REAL;
        ALTER TABLE users ADD arms_level REAL;
        ALTER TABLE users ADD legs_level REAL;
        ALTER TABLE users ADD chest_level REAL;
        ALTER TABLE users ADD abs_level REAL;
        ALTER TABLE users ADD back_level REAL;
        '''
        self.execute(sql, commit=True, script=True)

    def add_ex_to_workouts(self):
        self.execute(sql='ALTER TABLE workouts ADD exercise_id INTEGER;', commit=True)
