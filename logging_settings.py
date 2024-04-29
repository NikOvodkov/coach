import logging
import logging.config
import sys
from typing import Iterable


# Определяем свой фильтр, наследуясь от класса Filter библиотеки logging
class LoggingLevelFilter(logging.Filter):
    def __init__(self, lvl_logging: Iterable[str], *args, **kwargs):
        super().__init__()
        self.lvl_logging = [elem.upper() for elem in lvl_logging]

    def filter(self, record):
        return record.levelname in self.lvl_logging


logging_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'formatter': {
            'format': '[{asctime}] #{levelname:8} {filename}: {lineno} - {name} - {message}',
            'style': '{'
        }
    },
    'filters': {
        'logging_level_filter': {
            '()': LoggingLevelFilter,
            'lvl_logging': ['DEBUG', 'INFO']
        }
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'formatter'
        },
        'error_stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'formatter',
            'level': 'WARNING',
            'stream': sys.stderr
        },
        'debug_stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'formatter',
            'filters': ['logging_level_filter'],
            'level': 'DEBUG',
            'stream': sys.stdout
        },
        'error_file_handler': {
            'class': 'logging.FileHandler',
            'filename': 'error.log',
            'mode': 'a',
            'level': 'WARNING',
            'formatter': 'formatter'
        }
    },
    'loggers': {},
    'root': {
        'formatter': 'formatter',
        'level': 'DEBUG',
        'handlers': ['error_stream_handler', 'debug_stream_handler', 'error_file_handler']
    }
}

# Загружаем настройки логирования из словаря `logging_config`
logger = logging.getLogger()
logging.config.dictConfig(logging_config)
logger.debug('test debug level')
logger.info('test info level')
logger.warning('test warning level')
logger.error('test error level')
logger.critical('test critical level')
