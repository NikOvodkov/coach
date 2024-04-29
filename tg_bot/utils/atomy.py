import asyncio
from dataclasses import dataclass

import aiohttp
import requests

from logging_settings import logger


@dataclass
class Buyer(object):
    FirstName: str = ''
    LastName: str = ''
    MiddleName: str = ''
    BirthDay: str = ''
    Gender: str = ''
    HandPhone: str = ''
    PostNo: str = ''
    Addr2: str = ''
    Addr2_plus: str = ''
    Addr1: str = ''
    Email: str = ''
    Country: str = ''


async def check_user(payload):
    # session = requests.session()

    async with aiohttp.ClientSession() as session:
        query = {
            "auth": ('12345678', '123456')
        }  # параметры, тут можно указать любые
        query = {}
        response = await session.post("https://www.atomy.ru/ru/Account/GetFindId", data=payload, params=query)  # отправка запросов

        if response.status == 200:
            json = await response.json()
            if json['jsonData']:
                logger.debug(f"Покупатель найден, его почта: {json['jsonData']['Email']}")
                # print('Покупатель найден, его почта: ', json['jsonData']['Email'])
                return 'Покупатель найден, его почта: ' + json['jsonData']['Email']
            else:
                logger.debug(f"Покупатель не найден")
                # print('Покупатель не найден')
                return 'Покупатель не найден'
        else:
            # print(f'Запрос не обработан, код {response.status}.')
            logger.debug(f"Запрос не обработан, код {response.status}.")
            return f'Запрос не обработан, код {response.status}.'


def sign_in_0():
    url = 'https://www.atomy.ru/ru/Home/Account/Login'
    user_agent_val = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    session = requests.Session()
    session.headers.update({'Referer': url})
    session.headers.update({'User-Agent': user_agent_val})
    rvt = session.cookies.get('__RequestVerificationToken_L3J10')
    # print(rvt)
    logger.debug(rvt)
    data = {
        '__RequestVerificationToken': rvt,
        'userId': '12345678',
        'userPw': '123456',
        'rpage': ''
    }
    # print(data)
    logger.debug(data)
    res = session.post(url, data=data)
    if res.status_code == 200:
        # print('Покупатель найден, его почта: ', res.text)
        logger.debug(f'Покупатель найден, его почта: {res.text}.')
    else:
        # print(f'Запрос не обработан, код {res.status_code}.')
        logger.debug(f'Запрос не обработан, код {res.status_code}.')
    return session


if __name__ == '__main__':
    asyncio.run(check_user(payload=None))
