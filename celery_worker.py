# celery_worker.py
from celery import Celery
from core.config import settings
import os
import sys

# --- ДОБАВЬТЕ ЭТОТ БЛОК ---
# Добавляем корневую директорию проекта в PYTHONPATH.
# Это позволяет Celery воркеру находить модули вашего приложения (services, api, и т.д.)
# независимо от того, откуда он был запущен.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    
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