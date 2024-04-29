from tg_bot.database.sqlite import SQLiteDatabase

db = SQLiteDatabase(path_to_db='test.db')


def test():
    db.create_table_users()
    db.create_table_exercises_base()
    db.create_table_muscles_base()
    db.create_table_muscles_user()
    db.create_table_workouts()
    users = db.select_all_table('Users')
    exercises = db.select_all_table('Exercises_base')
    muscles_base = db.select_all_table('Muscles_base')
    muscles_user = db.select_all_table('Muscles_user')
    workouts = db.select_all_table('Workouts')
    print(f'До добавления пользователей: {users=}')
    print(f'До добавления пользователей: {exercises=}')
    print(f'До добавления пользователей: {muscles_base=}')
    print(f'До добавления пользователей: {muscles_user=}')
    print(f'До добавления пользователей: {workouts=}')


test()
