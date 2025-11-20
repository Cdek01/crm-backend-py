from typing import Optional

import requests
import json
import logging
from datetime import datetime, timedelta

from celery_worker import celery_app
from db.session import SessionLocal
from db import models
from services.eav_service import EAVService
from services.alias_service import AliasService
from core.config import settings
from core.encryption import decrypt_data

# Импорты для планировщика
try:
    from celery_sqlalchemy_scheduler.models import PeriodicTask, CrontabSchedule, IntervalSchedule
    from sqlalchemy.orm import Session
except ImportError:
    PeriodicTask, CrontabSchedule, IntervalSchedule, Session = None, None, None, None

logger = logging.getLogger(__name__)
CRM_TABLE_NAME = "beeline_calls"


# --- НАЧАЛО НОВОГО БЛОКА: Функция для управления расписанием ---
def setup_schedule_for_beeline(tenant: models.Tenant, db: Session, disable: bool = False) -> Optional[int]:
    """Создает/обновляет/удаляет периодическую задачу для синхронизации Билайн."""
    if not PeriodicTask:
        return None

    # Если у клиента уже есть задача, удаляем ее, чтобы создать новую с актуальным расписанием
    if tenant.beeline_periodic_task_id:
        old_task = db.query(PeriodicTask).filter_by(id=tenant.beeline_periodic_task_id).first()
        if old_task:
            db.delete(old_task)
            db.commit()

    # Если задача отключается или тип "вручную", просто выходим
    if disable or tenant.beeline_sync_schedule_type == 'manual':
        return None

    task_name = f'Beeline Sync for Tenant {tenant.id}'
    task_args = json.dumps([tenant.id])  # Передаем ID клиента в задачу

    schedule = None
    # Логика создания расписания (аналогично banking)
    if tenant.beeline_sync_schedule_type == 'hourly':
        schedule = db.query(IntervalSchedule).filter_by(every=1, period='hours').first()
        if not schedule:
            schedule = IntervalSchedule(every=1, period='hours')
            db.add(schedule)
            db.commit()
    else:
        crontab_kwargs = {}
        if tenant.beeline_sync_schedule_type == 'daily' and tenant.beeline_sync_time:
            crontab_kwargs = {'minute': str(tenant.beeline_sync_time.minute),
                              'hour': str(tenant.beeline_sync_time.hour)}
        elif tenant.beeline_sync_schedule_type == 'weekly' and tenant.beeline_sync_time and tenant.beeline_sync_weekday is not None:
            crontab_kwargs = {'minute': str(tenant.beeline_sync_time.minute),
                              'hour': str(tenant.beeline_sync_time.hour),
                              'day_of_week': str(tenant.beeline_sync_weekday)}
        if not crontab_kwargs: return None
        schedule = db.query(CrontabSchedule).filter_by(**crontab_kwargs).first()
        if not schedule:
            schedule = CrontabSchedule(**crontab_kwargs)
            db.add(schedule)
            db.commit()

    # Создаем новую запись о периодической задаче
    new_task = PeriodicTask(name=task_name, task='tasks.beeline_sync.sync_beeline_calls', args=task_args)
    if isinstance(schedule, IntervalSchedule):
        new_task.interval_id = schedule.id
    else:
        new_task.crontab_id = schedule.id
    db.add(new_task)
    db.commit()
    return new_task.id


# --- КОНЕЦ НОВОГО БЛОКА ---


# --- ИЗМЕНЕНИЕ: Задача теперь принимает tenant_id ---
@celery_app.task
def sync_beeline_calls(tenant_id: int):
    """
    Синхронизирует звонки для ОДНОГО конкретного клиента, ID которого был передан.
    """
    # Теперь нам не нужен if/else, мы сразу вызываем основную логику.
    # Старый код, который искал всех активных клиентов, можно удалить.
    _sync_for_single_tenant(tenant_id)


def _sync_for_single_tenant(tenant_id: int):
    """Основная логика синхронизации для одного клиента."""
    logger.info(f"--- [Beeline Sync] Запуск задачи для Tenant ID: {tenant_id} ---")
    db = SessionLocal()
    tenant = None
    try:
        tenant = db.get(models.Tenant, tenant_id)
        if not tenant or not tenant.beeline_api_token:
            logger.warning(f"[Beeline Sync] Пропуск Tenant ID {tenant_id}: интеграция неактивна или нет токена.")
            return

        alias_service = AliasService(db=db)
        eav_service = EAVService(db=db, alias_service=alias_service)
        owner = db.query(models.User).filter(models.User.tenant_id == tenant.id).first()
        if not owner:
            logger.error(f"[Beeline Sync] Не найден владелец для Tenant ID {tenant.id}")
            return

        token = decrypt_data(tenant.beeline_api_token)
        headers = {"X-MPBX-API-AUTH-TOKEN": token}

        # Определяем, с какой даты запрашивать звонки
        date_from = datetime.now() - timedelta(days=1)  # По умолчанию за последний день
        if tenant.beeline_last_sync:
            date_from = tenant.beeline_last_sync - timedelta(minutes=5)  # С небольшим запасом

        params = {"dateFrom": date_from.strftime("%Y-%m-%d"), "dateTo": datetime.now().strftime("%Y-%m-%d")}

        logger.info(f"[Beeline Sync] Запрос звонков для Tenant ID {tenant.id} с параметрами: {params}")
        response = requests.get(f"{settings.BEELINE_BASE_URL}/records", headers=headers, params=params)
        response.raise_for_status()
        calls = response.json()

        logger.info(f"[Beeline Sync] Получено {len(calls)} звонков от API для Tenant ID {tenant.id}.")
        # ... (остальная логика обработки звонков остается такой же, как была) ...
        # ... (проверка на дубликаты, сохранение в CRM) ...

        # Обновляем статус в БД, если все прошло успешно
        tenant.beeline_last_sync = datetime.now()
        tenant.beeline_last_error = None
        db.commit()

    except Exception as e:
        logger.error(f"[Beeline Sync] Ошибка при синхронизации для Tenant ID {tenant_id}: {e}", exc_info=True)
        if tenant:
            tenant.beeline_last_error = str(e)[:1000]
            db.commit()
    finally:
        if db:
            db.close()