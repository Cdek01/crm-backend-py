# core/logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
        },
        # --- НАШ НОВЫЙ ОБРАБОТЧИК ДЛЯ ВЕБХУКОВ ---
        'webhook_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': '/var/log/crm_webhooks.log',  # <-- Путь к файлу логов
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
            'encoding': 'utf8',
        },
    },

    'loggers': {
        # Логгер для всего приложения
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # --- НАШ НОВЫЙ СПЕЦИАЛЬНЫЙ ЛОГГЕР ---
        'webhook_sender': {
            'handlers': ['console', 'webhook_file_handler'],
            'level': 'INFO',
            'propagate': False,  # Не передавать сообщения в родительский логгер
        },
    },
}


def setup_logging():
    """Применяет конфигурацию логирования."""
    logging.config.dictConfig(LOGGING_CONFIG)