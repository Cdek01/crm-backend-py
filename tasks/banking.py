# tasks/banking.py
import json
import requests
from datetime import datetime, time
from celery_worker import celery_app
from db.session import SessionLocal
from db import models
from core.encryption import decrypt_data
from services.eav_service import EAVService

try:
    from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
except ImportError:
    # Заглушка, если django-celery-beat не установлен
    PeriodicTask, CrontabSchedule, IntervalSchedule = None, None, None


def setup_schedule_for_tenant(tenant: models.Tenant, disable: bool = False) -> Optional[int]:
    """
    Создает, обновляет или удаляет запись о периодической задаче в БД для Celery Beat.
    """
    if not PeriodicTask:  # Проверка, что пакет установлен
        return None

    # Сначала удаляем старую задачу, если она была
    if tenant.modulbank_periodic_task_id:
        PeriodicTask.objects.filter(id=tenant.modulbank_periodic_task_id).delete()

    if disable or tenant.modulbank_sync_schedule_type == 'manual':
        return None  # Для ручного режима или отключения задача не нужна

    task_name = f'Modulbank Sync for Tenant {tenant.id}'
    task_args = json.dumps([tenant.id])

    if tenant.modulbank_sync_schedule_type == 'hourly':
        # Расписание для "каждый час"
        schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.HOURS)
        task = PeriodicTask.objects.create(interval=schedule, name=task_name,
                                           task='tasks.banking.sync_tenant_operations', args=task_args)
        return task.id

    crontab_kwargs = {}
    if tenant.modulbank_sync_schedule_type == 'daily' and tenant.modulbank_sync_time:
        crontab_kwargs = {'minute': tenant.modulbank_sync_time.minute, 'hour': tenant.modulbank_sync_time.hour}
    elif tenant.modulbank_sync_schedule_type == 'weekly' and tenant.modulbank_sync_time and tenant.modulbank_sync_weekday is not None:
        crontab_kwargs = {'minute': tenant.modulbank_sync_time.minute, 'hour': tenant.modulbank_sync_time.hour,
                          'day_of_week': tenant.modulbank_sync_weekday}

    if not crontab_kwargs:
        return None

    schedule, _ = CrontabSchedule.objects.get_or_create(**crontab_kwargs)
    task = PeriodicTask.objects.create(crontab=schedule, name=task_name, task='tasks.banking.sync_tenant_operations',
                                       args=task_args)
    return task.id


@celery_app.task
def sync_tenant_operations(tenant_id: int):
    """Синхронизирует операции для одного конкретного клиента."""
    # ... (этот код остается без изменений)