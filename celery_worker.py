# celery_worker.py
from celery import Celery
from core.config import settings

# Имя основного модуля теперь 'celery_worker', как и имя файла.
celery_app = Celery(
    'celery_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Явно указываем, где находятся наши задачи.
    # Celery будет искать файл tasks/messaging.py
    include=['tasks.messaging']
)

# Можно добавить дополнительные настройки, если потребуется
celery_app.conf.update(
    task_track_started=True,
)