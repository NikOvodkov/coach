import asyncio
import os.path
import time
from notifiers import get_notifier

from tg_bot.config import load_config


async def print_telegram(mes='hello'):
    config = load_config('.env')
    get_notifier('telegram').notify(token=config.tg_bot.token, chat_id=config.tg_bot.admin_ids[0], message=mes)


def return_bot_status(file: str, secs: int):
    try:
        if abs(os.path.getmtime(file) - time.time()) < secs:
            return True
        else:
            return False
    except FileNotFoundError:
        return False


async def main():
    if return_bot_status('bot.log', 300):
        print('\r', 'Autorun: nib_bot rabotaet', end='')
        await print_telegram('Autorun: nib_bot rabotaet')
        bot_is_working = True
    else:
        print('\r', 'Autorun: nib_bot ne rabotaet', end='')
        await print_telegram('Autorun: nib_bot ne rabotaet')
        bot_is_working = False

    while True:
        with open(f'autorun.txt', 'w') as f:
            f.write(f"{time.asctime(time.localtime(time.time()))} Autorun rabotaet")
        bot_was_working = bot_is_working
        bot_is_working = return_bot_status('bot.log', 300)
        if bot_is_working != bot_was_working:
            if bot_is_working:
                print('\r', 'Autorun: nib_bot zarabotal', end='')
                await print_telegram('Autorun: nib_bot zarabotal')
            else:
                print('\r', 'Autorun: nib_bot ostanovilsya', end='')
                await print_telegram('Autorun: nib_bot ostanovilsya')
            # break
            # os.system('python main.py')
        await asyncio.sleep(120)


if __name__ == '__main__':
    asyncio.run(main())
