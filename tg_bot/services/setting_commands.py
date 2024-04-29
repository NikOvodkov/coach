from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeAllChatAdministrators, BotCommandScopeChatAdministrators, BotCommandScopeChatMember


async def set_default_commands(bot: Bot):
    return await bot.set_my_commands(
        commands=[
            BotCommand(command='start', description='Начать работу/ Сброс'),
            BotCommand(command='fitness', description='Фитнес'),
            BotCommand(command='life_calendar', description='Календарь жизни'),
            BotCommand(command='about', description='О боте'),
            BotCommand(command='help', description='Помощь')
        ],
        scope=BotCommandScopeDefault()
    )


async def set_admins_commands(bot: Bot, chat_id: int):
    return await bot.set_my_commands(
        commands=[
            BotCommand(command='gsheet', description='Обработать новые номера'),
            BotCommand(command='fitness', description='Фитнес'),
            BotCommand(command='atomy', description='Проверить покупателя'),
            BotCommand(command='test_location', description='Тест локации'),
            BotCommand(command='life_calendar', description='Календарь жизни'),
            BotCommand(command='sql_db', description='Редактировать БД'),
            BotCommand(command='start', description='Рестарт бота'),
            BotCommand(command='email', description='Сменить почту'),
            BotCommand(command='get_commands', description='Получить список команд'),
            BotCommand(command='help', description='Помощь')
        ],
        scope=BotCommandScopeChat(chat_id=chat_id),
        language_code='ru'
    )


async def set_starting_commands(bot: Bot, chat_id: int):
    STARTING_COMMANDS = {
        'ru': [
            BotCommand(command='start', description='Начать работу/ Сброс'),
            BotCommand(command='fitness', description='Фитнес'),
            BotCommand(command='life_calendar', description='Календарь жизни'),
            BotCommand(command='about', description='О боте'),
            BotCommand(command='help', description='Помощь')
        ],
        'en': [
            BotCommand(command='start', description='Begin to work'),
            BotCommand(command='fitness', description='Get workout'),
            BotCommand(command='life_calendar', description='Get life calendar'),
            BotCommand(command='about', description='Get information'),
            BotCommand(command='help', description='Get help')
        ]
    }
    for language_code, commands in STARTING_COMMANDS.items():
        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeChat(chat_id=chat_id),
            language_code=language_code
        )


async def force_reset_all_commands(bot: Bot):
    for language_code in ('ru', 'en'):
        for scope in (
                BotCommandScopeAllGroupChats(),
                BotCommandScopeAllPrivateChats(),
                BotCommandScopeAllChatAdministrators(),
                # BotCommandScopeChatAdministrators(chat_id=chat_id),
                # BotCommandScopeChat(chat_id=chat_id),
                # BotCommandScopeChatMember(),
                BotCommandScopeDefault()
        ):
            await bot.delete_my_commands(
                scope=scope,
                language_code=language_code
            )


async def set_all_groups_commands(bot: Bot):
    return await bot.set_my_commands(
        commands=[
            BotCommand(command='start', description='Информация о боте'),
            BotCommand(command='report', description='Пожаловаться на пользователя')
        ],
        scope=BotCommandScopeAllGroupChats()
    )


async def set_all_chat_admins_commands(bot: Bot):
    return await bot.set_my_commands(
        commands=[
            BotCommand(command='ro', description='Мут пользователя'),
            BotCommand(command='ban', description='Забанить пользователя'),
            BotCommand(command='change_commands', description='Изменить команды в этом чате')
        ],
        scope=BotCommandScopeAllChatAdministrators()
    )


async def set_chat_admins_commands(bot: Bot, chat_id: int):
    return await bot.set_my_commands(
        commands=[
            BotCommand(command='ro', description='Мут пользователя'),
            BotCommand(command='ban', description='Забанить пользователя'),
            BotCommand(command='reset_commands', description='Сбросить команды')
        ],
        scope=BotCommandScopeChatAdministrators(chat_id=chat_id)
    )


async def set_chat_members_commands(bot: Bot, chat_id, user_id: int):
    return await bot.set_my_commands(
        commands=[BotCommand(command='promote', description='Повысить до админа')],
        scope=BotCommandScopeChatMember(chat_id=chat_id, user_id=user_id)
    )


async def set_all_private_commands(bot: Bot):
    return await bot.set_my_commands(
        commands=[
            BotCommand(command='start', description='Начать работу/ Сброс'),
            BotCommand(command='fitness', description='Фитнес'),
            BotCommand(command='life_calendar', description='Календарь жизни'),
            BotCommand(command='about', description='О боте'),
            BotCommand(command='help', description='Помощь')
        ], scope=BotCommandScopeAllPrivateChats())
