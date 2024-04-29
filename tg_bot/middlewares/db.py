from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


class DbMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ['error', 'update']

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs

    async def pre_process(self, obj, data, *args):
        data.update(**self.kwargs)
        # db = obj.bot.get('db')
        # Передаем данные из таблицы в хендлер
        # data['some_model'] = await Model.get()
