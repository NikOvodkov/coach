import asyncio
import math
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from logging_settings import logger


def godlet(god):
    return {
        god < 0: 'ошибка',
        god % 10 == 0: 'лет',
        god % 10 == 1: 'год',
        god % 10 > 1 and god % 10 < 5: 'года',
        god % 10 > 4: 'лет',
        god % 100 > 10 and god % 100 < 20: 'лет'
    }[True]


async def generate_text_calendar(ldate, rdate, interval):
    rdate_weeks = round((datetime.fromisoformat(rdate) - datetime.fromisoformat(ldate)) / timedelta(days=7))
    lived_weeks = round((datetime.today() - datetime.fromisoformat(ldate)) / timedelta(days=7))
    rdate_weeks = max(rdate_weeks, 3652)
    # print(f'{ldate=} {rdate=} {interval=} {lived_weeks=} {rdate_weeks=}')
    logger.debug(f'{ldate=} {rdate=} {interval=} {lived_weeks=} {rdate_weeks=}')
    str_out = ''
    if interval == 'year':
        points = round(lived_weeks / 52.1)
        str_in = points * 'ø' + (round(rdate_weeks / 52.1) - points) * 'o'
        for i in range(len(str_in)):
            str_out += str_in[i]
            if i % 10 == 9:
                str_out += '\n'
    elif interval == 'month':
        points = round(lived_weeks / 4.35)
        str_in = points * 'ø' + (round(rdate_weeks / 4.35) - points) * 'o'
        for i in range(len(str_in)):
            str_out += str_in[i]
            if i % 25 == 24:
                str_out += '\n'
    elif interval == 'week':
        points = lived_weeks
        str_in = points * 'ø' + (rdate_weeks - points) * 'o'
        for i in range(len(str_in)):
            str_out += str_in[i]
            if i % 52 == 51:
                str_out += '\n'
    return str_out


async def generate_image_calendar(ldate, rdate, interval, path) -> str:
    rdate_years = (datetime.fromisoformat(rdate) - datetime.fromisoformat(ldate)) / timedelta(days=365.25)
    rdate_weeks = round(rdate_years * 52)
    lived_years = (datetime.today() - datetime.fromisoformat(ldate)) / timedelta(days=365.25)
    lived_weeks = round(lived_years * 52)
    font_big = ImageFont.truetype("times.ttf", size=92)
    font_middle = ImageFont.truetype("times.ttf", size=46)
    font_small = ImageFont.truetype("times.ttf", size=23)
    img = Image.new('RGBA', (1000, round(rdate_weeks * 15 / 52) + 650), 'white')
    idraw = ImageDraw.Draw(img)
    idraw.text((50, 30), text='Ваша жизнь в', font=font_big, fill='navy', stroke_width=1, stroke_fill="navy")
    str_out = ''
    y2 = 0
    # print(f'{ldate=} {rdate=} {interval=} {lived_weeks=} {rdate_weeks=} {rdate_years=} {lived_years=}')
    logger.debug(f'{ldate=} {rdate=} {interval=} {lived_weeks=} {rdate_weeks=} {rdate_years=} {lived_years=}')
    if interval == 'year':
        lived_years = round(lived_weeks / 52.1)
        max_years = round(rdate_weeks / 52.1)
        max_tens = math.floor(max_years / 10)
        lived_tens = math.floor(lived_years / 10)
        adj = 0
        if lived_years < 30:
            adj = - 85
            if lived_years < 20:
                adj = - 1000
        # print(f'{lived_years=} {max_years=} {lived_tens=} {max_tens=}')
        logger.debug(f'{lived_years=} {max_years=} {lived_tens=} {max_tens=}')
        str_in = lived_years * 'ø' + (max_years - lived_years) * 'o'
        for i in range(len(str_in)):
            str_out += str_in[i]
            if (i % 10 == 9) and (i < len(str_in) - 1):
                str_out += '\n'

        idraw.text((620, 30), text='годах', font=font_big, fill='brown', stroke_width=1, stroke_fill="brown")
        idraw.text((30, 160), text='Один закрашенный круг = 1 прожитому году', font=font_middle, fill='black')
        idraw.text((110, 240), text='Рождение', font=font_middle, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        idraw.text((155, 260), text='→', font=font_big, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        idraw.text((775, 255), text='10 лет', font=font_middle, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((750, 265), text='←', font=font_big, fill='purple', stroke_width=1, stroke_fill="purple")
        x1, y1 = 200, 300
        x2, y2 = 240, 340
        for i in str_out:
            if i == 'ø':
                x1 += 50
                x2 += 50
                idraw.ellipse((x1, y1, x2, y2), fill='orange', outline='black', width=5)
            elif i == 'o':
                x1 += 50
                x2 += 50
                idraw.ellipse((x1, y1, x2, y2), fill=None, outline='black', width=5)
            elif i == '\n':
                y1 += 50
                y2 += 50
                x1 = 200
                x2 = 240
        if max_years % 10 == 0:
            y2 += 50
        idraw.text((775, lived_tens * 50 + 205 - adj), text=f'{10 * lived_tens} лет', font=font_middle, fill='purple', stroke_width=1, stroke_fill="purple")
        if lived_years >= 20:
            idraw.text((750, lived_tens * 50 + 215), text='←', font=font_big, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((775, y2 - 50), text=f'{10 * max_tens} лет', font=font_middle, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((750, y2 - 125), text='←', font=font_big, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((30, y2 + 50), text='Незакрашенные круги - будущие годы жизни', font=font_middle, fill='black')
        img = img.crop((0, 0, 1000, max_tens * 50 + 650))

    elif interval == 'month':
        lived_months = round(lived_weeks / 4.35)
        max_months = round(rdate_weeks / 4.35)
        max_36s = math.floor(max_months / 36)
        lived_36s = math.floor(lived_months / 36)
        adj = 0
        if lived_months < 300:
            adj = - 90
            if lived_months < 120:
                adj = - 1000
        # print(f'{lived_months=} {max_months=} {lived_36s=} {max_36s=}')
        logger.debug(f'{lived_months=} {max_months=} {lived_36s=} {max_36s=}')
        str_in = lived_months * 'ø' + (max_months - lived_months) * 'o'
        for i in range(len(str_in)):
            str_out += str_in[i]
            if (i % 36 == 35) and (i < len(str_in) - 1):
                str_out += '\n'

        idraw.text((620, 30), text='месяцах', font=font_big, fill='brown', stroke_width=1, stroke_fill="brown")
        idraw.text((30, 160), text='Один закрашенный круг = 1 прожитому месяцу', font=font_middle, fill='black')
        idraw.text((30, 240), text='Рождение', font=font_middle, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        idraw.text((60, 260), text='→', font=font_big, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        idraw.text((760, 240), text='36 месяцев', font=font_middle, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((840, 260), text='←', font=font_big, fill='purple', stroke_width=1, stroke_fill="purple")
        x1, y1 = 135, 310
        x2, y2 = 149, 325
        for i in str_out:
            if i == 'ø':
                x1, x2 = x1 + 19, x2 + 19
                idraw.ellipse((x1, y1, x2, y2), fill='orange', outline='black', width=2)
            elif i == 'o':
                x1, x2 = x1 + 19, x2 + 19
                idraw.ellipse((x1, y1, x2, y2), fill=None, outline='black', width=2)
            elif i == '\n':
                x1, y1 = 135, y1 + 19
                x2, y2 = 149, y2 + 19
        if max_months % 36 == 0:
            y2 += 19
        idraw.text((845, lived_36s * 19 + 225 - adj), text=f'{3 * lived_36s} {godlet(3 * lived_36s)}', font=font_middle, fill='purple', stroke_width=1, stroke_fill="purple")
        if lived_months >= 120:
            idraw.text((840, lived_36s * 19 + 240), text='←', font=font_big, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((845, y2 - 5), text=f'{3 * max_36s} {godlet(3 * max_36s)}', font=font_middle, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((840, y2 - 80), text='←', font=font_big, fill='purple', stroke_width=1, stroke_fill="purple")
        idraw.text((30, y2 + 60), text='Незакрашенные круги - будущие месяцы жизни', font=font_middle, fill='black')
        img = img.crop((0, 0, 1000, max_36s * 25 + 450))

    elif interval == 'week':
        max_52s = round(rdate_weeks / 52)
        lived_52s = round(lived_weeks / 52)
        # print(f'{lived_weeks=} {rdate_weeks=} {lived_52s=} {max_52s=}')
        logger.debug(f'{lived_weeks=} {rdate_weeks=} {lived_52s=} {max_52s=}')
        str_in = lived_weeks * 'ø' + (rdate_weeks - lived_weeks) * 'o'
        for i in range(len(str_in)):
            str_out += str_in[i]
            if (i % 52 == 51) and (i < len(str_in) - 1):
                str_out += '\n'
        idraw.text((620, 30), text='неделях', font=font_big, fill='brown', stroke_width=1, stroke_fill="brown")
        idraw.text((30, 160), text='Один закрашенный круг = 1 прожитой неделе', font=font_middle, fill='black')
        idraw.text((150, 280), text='Неделя года →', font=font_middle, fill='black')
        idraw.text((155, 345), text="1", font=font_small, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        idraw.text((215, 345), text="5", font=font_small, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        for week in range(10, 55, 5):
            idraw.text((134 + 15 * week, 345), text=str(week),
                       font=font_small, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        img_title = Image.new('RGBA', (600, 60), color='white')
        draw_title = ImageDraw.Draw(img_title)
        draw_title.text((520, 30), '← Возраст в годах', font=font_middle, anchor="rm", fill="black")
        img.paste(img_title.transpose(Image.ROTATE_90), (50, 300))

        x1, y1 = 140, 380
        x2, y2 = 150, 390
        for i in str_out:
            if i == 'ø':
                x1, x2 = x1 + 15, x2 + 15
                idraw.ellipse((x1, y1, x2, y2), fill='orange', outline='black', width=2)
            elif i == 'o':
                x1, x2 = x1 + 15, x2 + 15
                idraw.ellipse((x1, y1, x2, y2), fill=None, outline='black', width=2)
            elif i == '\n':
                x1, y1 = 140, y1 + 15
                x2, y2 = 150, y2 + 15
        if rdate_weeks % 52 == 0:
            y2 += 15
        for i in range(max_52s+1):
            if i % 5 == 0:
                idraw.text((100, i * 15 + 370), text=str(i).rjust(5), font=font_small, fill='deepskyblue', stroke_width=1, stroke_fill="deepskyblue")
        idraw.text((20, y2 + 50), text='Незакрашенные круги - будущие недели жизни', font=font_middle, fill='black')

    idraw = ImageDraw.Draw(img)
    idraw.text(
        (200, y2 + 170),
        text='Если вы хотите предложить более привлекательный макет\n'
             'календаря, присылайте его в техническую поддержку бота.',
        font=font_small,
        fill='black'
    )
    img.save(path)
    return str_out


if __name__ == '__main__':
    # rdate = (datetime.fromisoformat('1990-05-22') + timedelta(weeks=3640)).strftime('%Y-%m-%d')
    # print(generate_text_calendar('1984-05-22', rdate, 'year'))
    # print(generate_text_calendar('1984-05-22', rdate, 'month'))
    # print(generate_text_calendar('1984-05-22', rdate, 'week'))
    # rdate = (datetime.fromisoformat('1954-05-22') + timedelta(weeks=6000)).strftime('%Y-%m-%d')
    # print(generate_text_calendar('1954-05-22', rdate, 'year'))
    # print(generate_text_calendar('1954-05-22', rdate, 'month'))
    # print(generate_text_calendar('1954-05-22', rdate, 'week'))
    # print(generate_image_calendar('1990-05-22', '2084-05-22', 'year'))
    path = str(Path.cwd() / Path('rectangle.gif'))
    asyncio.run(generate_image_calendar('1984-05-22', '2054-05-22', 'week', path))
