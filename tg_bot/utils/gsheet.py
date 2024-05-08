"""ПЛАН ДОРАБОТОК
1. Определять Separator автоматически
2. Определять колонку с номерами автоматически, даже если она не первая
3. Исправить обработку последней строки
4. Добавить расчет строк файла, предварительный расчет времени и индикацию времени.
"""

import asyncio
from pathlib import Path

import gspread
import aiohttp

from logging_settings import logger

# список серверов для проверки
SERVERS = [
    {
        'name': 'voxlink.ru',
        'request': 'http://num.voxlink.ru/get/?num=+7{number}',
        'method': 'GET',
        'requests_24_hours': 0,
        'requests_1_sec': 10
    },
    {
        'name': 'smsc.ru',
        'request': 'https://smsc.ru/sys/info.php?get_operator=1&login=nikovodkov&psw=Smsc_122059&phone=7{number}',
        'method': 'POST',
        'requests_24_hours': 0,
        'requests_1_sec': 1
    },
    {
        'name': 'kody.su',
        'request': 'https://www.kody.su/api/v2.1/search.json?q=+7{number}&key=test',
        'method': 'POST',
        'requests_24_hours': 3000,
        'requests_1_sec': 3
    },
    {
        'name': 'htmlweb.ru',
        'request': 'https://htmlweb.ru/json/mnp/phone/7{number}?api_key=ccffa9acd4bfa9e3942039958e5f667a',
        'method': 'POST',
        'requests_24_hours': 20,
        'requests_1_sec': 1
    }
]


def get_path():
    return str(Path.cwd().parent / Path('keys', 'gsheet.json'))



async def get_operator_from_number(number: str):
    await asyncio.sleep(0.1)
    number = number[-10:]
    number = int(number)
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://num.voxlink.ru/get/?num=+7{number}') as response:
            # print(response.status, response)
            # print(await response.json())
            if response.status == 200:
                operator = await response.json()
                return operator['operator']
            else:
                # print(f'Запрос не обработан, код {response.status}, номер {number}.')
                logger.error(f'Запрос не обработан, код {response.status}, номер {number}.')
                return 'Неизвестен'


async def gsheets(file: str, worksheet: str, google_docs_key: str):
    # Создаём лог в виде списка строк
    lst = list()
    # Делаем паузу, чтобы успеть открыть гугл таблицу для контроля процесса
    await asyncio.sleep(3)
    # Указываем путь к JSON файлу с ключом google docs
    gc = gspread.service_account(filename=google_docs_key)
    # Подключаемся к таблице
    sh = gc.open(file)
    # Считываем лист
    worksheet = sh.worksheet(worksheet)
    # Считываем колонку с номерами
    numbers_column = worksheet.col_values(1)
    # Находим номер колонки с заголовком msisdn
    number_column = worksheet.find("msisdn").col
    # Находим номер колонки с заголовком Оператор
    operator_column = worksheet.find("Оператор").col
    # Считываем колонку с именем оператора
    operators_column = worksheet.col_values(operator_column)
    # Пробегаемся по концу колонки номеров, у которых не проставлен оператор
    for i, number_cell in enumerate(numbers_column[len(operators_column):]):
        # Считываем ячейку с именем оператора
        operator_cell = worksheet.cell(len(operators_column) + i + 1, operator_column).value
        # Если она пустая:
        if not operator_cell:
            # - запрашиваем имя оператора по номеру,
            operator = await get_operator_from_number(number_cell)
            # - обновляем содержимое ячейки именем оператора,
            worksheet.update_cell(len(operators_column) + i + 1, operator_column, operator)
            # - если номер начинается на 8
            if str(number_cell)[0] == '8':
                # меняем первую цифру на 7
                new_number = '7' + number_cell[1:]
                # и обновляем ячейку с номером
                worksheet.update_cell(len(operators_column) + i + 1, number_column, new_number)
            # - сохраняем в лог строку изменённой таблицы,
            logstr = f'{len(operators_column) + i + 1} {number_cell} {operator}'
            # - печатаем строку лога в шелл,
            # print(logstr)
            logger.debug(logstr)
            # - добавляем строку лога в лог-список.
            lst.append(logstr)
    return lst


async def del_black_list(file: str, worksheet: str, black_list: str, google_docs_key: str):
    # Делаем паузу, чтобы успеть открыть гугл таблицу для контроля процесса
    # Указываем путь к JSON файлу с ключом google docs
    gc = gspread.service_account(filename=google_docs_key)
    # Подключаемся к таблице
    sh = gc.open(file)
    # Считываем листы
    worksheet = sh.worksheet(worksheet)
    black_list = sh.worksheet(black_list)
    black_number = black_list.cell(2, 1).value
    while black_number:
        await asyncio.sleep(1)
        # Считываем колонку с номерами
        black_number = black_list.cell(2, 1).value
        logger.debug(f'{black_number=}')
        new_number = black_number
        if str(black_number)[0] == '8':
            logger.debug('change 8->7')
            # меняем первую цифру на 7
            new_number = '7' + black_number[1:]
            black_list.update_cell(2, 1, new_number)
        # Находим номер колонки с заголовком msisdn
        finded_cell = worksheet.find(new_number, in_column=1)
        logger.debug(f'{finded_cell=}')
        if finded_cell:
            worksheet.delete_row(finded_cell.row)
            logger.debug('row deleted')
        else:
            black_list.delete_row(2)
            logger.debug('black_list row deleted')
    return



def add_operators_to_numbers_from_csv(csv_file: str, sep: str = ',', path: str = 'C:\\Users\\nikov\\Downloads\\'):
    with open(path + csv_file, "r", encoding="utf-8") as input_file:
        with open(f"{path}_{csv_file}", "w", encoding="utf-8") as output_file:
            number_of_string = 0
            for input_line in input_file:
                if number_of_string:
                    operator = get_operator_from_number(input_line.split(sep)[0])
                    if input_line[-1] == '\n':
                        output_line = input_line[:-1] + sep + operator + '\n'
                    else:
                        output_line = input_line + sep + operator
                    # output_line = input_line[:-1] + sep + get_operator_from_number(input_line.split(sep)[0]) + '\n'
                    if operator == '':
                        # print(f'В строке {number_of_string+1} оператор не найден')
                        logger.error(f'В строке {number_of_string+1} оператор не найден')
                    else:
                        output_file.write(output_line)
                else:
                    output_file.write(input_line[:-1] + sep + 'Оператор' + '\n')
                number_of_string += 1
                logger.debug('*' * (number_of_string // 50))
                # print('\r' + '*' * (number_of_string // 50), end='')


if __name__ == '__main__':
    asyncio.run(del_black_list(
        file='Example',
        worksheet='Finsburg', black_list='ЧС Finsburg',
        google_docs_key=str(Path.cwd().parent / Path('keys', 'gsheet.json'))))

    # print(get_operator_from_number('9043330778'))
    # if __name__ == '__main__':
    #     add_operators_to_numbers_from_csv('tels.vlad.xlsx - ВлЧС (1).csv')
    # C:\\Users\\nikov\\PycharmProjects\\
