# celery_worker.py
from celery import Celery
from core.config import settings
import os
import sys

# --- Абсолютно надёжное добавление пути к проекту ---
CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_FILE)

# На случай, если структура типа /root/projects/crm-backend/crm-backend-py
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Дополнительно выведем, чтобы убедиться:
print(">>> Celery WORKER PATHS <<<")
print("CWD:", os.getcwd())
print("PROJECT_ROOT:", PROJECT_ROOT)
print("sys.path:", sys.path[:3])  # первые три достаточно


# Имя основного модуля теперь 'celery_worker', как и имя файла.
celery_app = Celery(
    'celery_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include = ['tasks.messaging', 'tasks.imports', 'tasks.enrichment', 'tasks.banking', 'tasks.beeline_sync']
)

# --- НОВАЯ КОНФИГУРАЦИЯ ДЛЯ ПЛАНИРОВЩИКА ---
celery_app.conf.update(
    task_track_started=True,
    # Указываем SQLAlchemy URI для планировщика
    beat_dburi=settings.DATABASE_URL,
    # Указываем сам класс планировщика
    beat_scheduler='celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler',
    beat_schedule={
        'celery.backend_cleanup': {
            'task': 'celery.backend_cleanup',
            'schedule': 3600.0, # любое значение, оно не будет использоваться
            'options': {'enabled': False}
        },
    },
)

# --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
# Полностью очищаем стандартное расписание Beat.
# Это более надежный способ, чем просто пустой словарь в update().
celery_app.conf.beat_schedule = {}

# Полностью очищаем стандартное расписание Beat.
celery_app.conf.beat_schedule = {
    # Добавляем нашу новую задачу
    'sync-beeline-calls-every-5-minutes': {
        'task': 'tasks.beeline_sync.sync_beeline_calls',
        'schedule': 300.0,  # 300 секунд = 5 минут
    },
}


