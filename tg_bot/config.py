from __future__ import annotations

from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str  # токен telegram bot api
    admin_ids: list[int]  # список администраторов бота
    use_redis: bool
    phone_number: str  # номер телефона для telegram api
    api_id: int  # токен telegram api
    api_hash: str  # хэш telegram api
    service_channel: int


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    postgres_uri: str


@dataclass
class AiConfig:
    token: str


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    ai: AiConfig
    misc: Miscellaneous


def load_config(path: str | None = None) -> Config:
    # Создаем экземпляр класса Env
    env: Env = Env()
    # Добавляем в переменные окружения данные, прочитанные из файла .env
    # env.read_env(path)
    env.read_env()
    return Config(
        tg_bot=TgBot(
            token=env.str("TG_TOKEN"),
            # token=env.str("WORK_TOKEN"),
            phone_number=env.str("PHONE_NUMBER"),
            api_id=env.int("API_ID"),
            api_hash=env.str("API_HASH"),
            service_channel=env.int("SERVICE_CHANNEL"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS")),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
            postgres_uri=f'postgresql://{env.str("DB_USER")}:{env.str("DB_PASS")}@{env.str("DB_HOST")}/postgres'),
        ai=AiConfig(
            token=env.str("AI_TOKEN")),
        misc=Miscellaneous())

    # Выводим значения полей экземпляра класса Config на печать,
    # чтобы убедиться, что все данные, получаемые из переменных окружения, доступны


if __name__ == '__main__':
    config = load_config()
    print('BOT_TOKEN:', config.tg_bot.token)
    print('ADMIN_IDS:', config.tg_bot.admin_ids)
    print()
    print('DATABASE:', config.db.database)
    print('DB_HOST:', config.db.host)
    print('DB_USER:', config.db.user)
    print('DB_PASSWORD:', config.db.password)
