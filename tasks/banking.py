# tasks/banking.py
import json
import requests
from datetime import datetime, time, timedelta, timezone # <-- Добавьте 'timezone'
from typing import Optional

from celery_worker import celery_app
from db.session import SessionLocal
from db import models
from core.encryption import decrypt_data
from services.eav_service import EAVService
from services.alias_service import AliasService # <-- 1. Добавляем импорт AliasService

# Импортируем модели из celery_sqlalchemy_scheduler
from celery_sqlalchemy_scheduler.models import (
    PeriodicTask,
    CrontabSchedule,
    IntervalSchedule,
)
from sqlalchemy.orm import Session


def setup_schedule_for_tenant(tenant: models.Tenant, db: Session, disable: bool = False) -> Optional[int]:
    """
    Создает, обновляет или удаляет запись о периодической задаче
    с использованием SQLAlchemy.
    """
    # Сначала удаляем старую задачу, если она была
    if tenant.modulbank_periodic_task_id:
        old_task = db.query(PeriodicTask).filter_by(id=tenant.modulbank_periodic_task_id).first()
        if old_task:
            db.delete(old_task)
            db.commit()

    if disable or tenant.modulbank_sync_schedule_type == 'manual':
        return None

    task_name = f'Modulbank Sync for Tenant {tenant.id}'
    task_args = json.dumps([tenant.id])

    schedule = None
    if tenant.modulbank_sync_schedule_type == 'hourly':
        schedule = db.query(IntervalSchedule).filter_by(every=1, period='hours').first()
        if not schedule:
            schedule = IntervalSchedule(every=1, period='hours')
            db.add(schedule)
            db.commit()
    else:
        crontab_kwargs = {}
        if tenant.modulbank_sync_schedule_type == 'daily' and tenant.modulbank_sync_time:
            crontab_kwargs = {'minute': str(tenant.modulbank_sync_time.minute),
                              'hour': str(tenant.modulbank_sync_time.hour)}
        elif tenant.modulbank_sync_schedule_type == 'weekly' and tenant.modulbank_sync_time and tenant.modulbank_sync_weekday is not None:
            crontab_kwargs = {'minute': str(tenant.modulbank_sync_time.minute),
                              'hour': str(tenant.modulbank_sync_time.hour),
                              'day_of_week': str(tenant.modulbank_sync_weekday)}

        if not crontab_kwargs: return None

        schedule = db.query(CrontabSchedule).filter_by(**crontab_kwargs).first()
        if not schedule:
            schedule = CrontabSchedule(**crontab_kwargs)
            db.add(schedule)
            db.commit()

    # Создаем новую задачу
    new_task = PeriodicTask(
        name=task_name,
        task='tasks.banking.sync_tenant_operations',
        args=task_args,
    )
    if isinstance(schedule, IntervalSchedule):
        new_task.interval_id = schedule.id
    else:
        new_task.crontab_id = schedule.id

    db.add(new_task)
    db.commit()
    return new_task.id


@celery_app.task
def sync_tenant_operations(tenant_id: int):
    """Синхронизирует операции для одного конкретного клиента."""
    db = SessionLocal()
    eav_service = EAVService(db=db)  # Нужен для создания записей

    try:
        tenant = db.get(models.Tenant, tenant_id)
        if not tenant or not tenant.modulbank_api_token:
            return

        token = decrypt_data(tenant.modulbank_api_token)
        headers = {'Authorization': f'Bearer {token}'}

        from_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')
        if tenant.modulbank_last_sync:
            # Добавляем 1 секунду, чтобы не запрашивать последнюю полученную операцию заново
            from_date = (tenant.modulbank_last_sync + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S')

        # --- НАЧАЛО ИСПРАВЛЕНИЯ ---

        # 1. Получаем список компаний и счетов через POST-запрос
        companies_resp = requests.post("https://api.modulbank.ru/v1/account-info", headers=headers)
        companies_resp.raise_for_status()
        companies = companies_resp.json()
        if not companies: return

        owner = db.query(models.User).filter(models.User.tenant_id == tenant.id).first()
        if not owner: return

        # 2. Проходим по каждой компании и ее счетам
        for company in companies:
            for account in company.get('bankAccounts', []):
                account_id = account['id']
            operations_url = f"https://api.modulbank.ru/v1/operation-history/{account_id}"
            payload = {
                "from": from_date,
                "records": 50  # Максимальное значение по документации
            }
            operations_resp = requests.post(operations_url, headers=headers, json=payload)
            operations_resp.raise_for_status()
            operations = operations_resp.json()

            for op in operations:
                # 3. Проверяем, не создавали ли мы уже такую запись
                # Для этого в EAV-таблице должно быть поле "operation_id"
                existing_op_filter = [{"field": "operation_id", "op": "eq", "value": op['id']}]

                # Нужен пользователь, от имени которого будем создавать
                owner = db.query(models.User).filter(models.User.tenant_id == tenant.id).first()
                if not owner: continue  # Пропускаем, если у клиента нет пользователей

                # Используем EAVService для поиска
                search_result = eav_service.get_all_entities_for_type(
                    entity_type_name="banking_operations",  # Системное имя вашей EAV-таблицы
                    current_user=owner,
                    filters=existing_op_filter,
                    limit=1
                )

                if search_result['total'] > 0:
                    continue  # Такая операция уже есть, пропускаем

                # 4. Создаем новую запись в EAV
                op_data = {
                    "operation_id": op['id'],
                    "amount": op['amount'],
                    "currency": op['currency'],
                    "operation_type": op['type'],
                    "contractor_name": op['contractorName'],
                    "purpose": op['purpose'],
                    "operation_date": op['executed'],
                }
                eav_service.create_entity("banking_operations", op_data, owner)

        # Обновляем статус в БД
        tenant.modulbank_last_sync = datetime.now(timezone.utc)
        tenant.modulbank_last_error = None
        db.commit()

    except Exception as e:
        # Если что-то пошло не так, записываем ошибку в БД
        if 'tenant' in locals():
            tenant.modulbank_integration_status = 'error'
            tenant.modulbank_last_error = str(e)
            db.commit()
    finally:
        db.close()