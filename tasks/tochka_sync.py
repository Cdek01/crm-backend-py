# tasks/tochka_sync.py
import requests
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from celery_worker import celery_app
from db.session import SessionLocal
from db import models
from services.eav_service import EAVService
from services.alias_service import AliasService
from core.encryption import decrypt_data

# Импорты для планировщика
try:
    from celery_sqlalchemy_scheduler.models import PeriodicTask, CrontabSchedule, IntervalSchedule
    from sqlalchemy.orm import Session
except ImportError:
    PeriodicTask, CrontabSchedule, IntervalSchedule, Session = None, None, None, None

logger = logging.getLogger(__name__)

# --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
# Указываем, что эта задача работает ТОЛЬКО с таблицей Точка Банка
CRM_TABLE_NAME = "tochka_operations"
# -------------------------


def setup_schedule_for_tochka(tenant: models.Tenant, db: Session, disable: bool = False) -> Optional[int]:
    """Создает/обновляет/удаляет периодическую задачу для синхронизации с Точка Банком."""
    if not PeriodicTask:
        return None

    if tenant.tochka_periodic_task_id:
        old_task = db.query(PeriodicTask).filter_by(id=tenant.tochka_periodic_task_id).first()
        if old_task:
            db.delete(old_task)
            db.commit()

    if disable or tenant.tochka_sync_schedule_type == 'manual':
        return None

    task_name = f'Tochka Bank Sync for Tenant {tenant.id}'
    task_args = json.dumps([tenant.id])

    schedule = None
    if tenant.tochka_sync_schedule_type == 'hourly':
        schedule = db.query(IntervalSchedule).filter_by(every=1, period='hours').first()
        if not schedule:
            schedule = IntervalSchedule(every=1, period='hours')
            db.add(schedule)
            db.commit()
    else:
        crontab_kwargs = {}
        if tenant.tochka_sync_schedule_type == 'daily' and tenant.tochka_sync_time:
            crontab_kwargs = {'minute': str(tenant.tochka_sync_time.minute), 'hour': str(tenant.tochka_sync_time.hour)}
        elif tenant.tochka_sync_schedule_type == 'weekly' and tenant.tochka_sync_time and tenant.tochka_sync_weekday is not None:
            crontab_kwargs = {'minute': str(tenant.tochka_sync_time.minute), 'hour': str(tenant.tochka_sync_time.hour),
                              'day_of_week': str(tenant.tochka_sync_weekday)}
        if not crontab_kwargs: return None
        schedule = db.query(CrontabSchedule).filter_by(**crontab_kwargs).first()
        if not schedule:
            schedule = CrontabSchedule(**crontab_kwargs)
            db.add(schedule)
            db.commit()

    new_task = PeriodicTask(name=task_name, task='tasks.tochka_sync.sync_tochka_operations', args=task_args)
    if isinstance(schedule, IntervalSchedule):
        new_task.interval_id = schedule.id
    else:
        new_task.crontab_id = schedule.id
    db.add(new_task)
    db.commit()
    return new_task.id


@celery_app.task
def sync_tochka_operations(tenant_id: int):
    """Синхронизирует операции для клиента из Точка Банка."""
    logger.info(f"--- [Tochka Sync] Запуск задачи для Tenant ID: {tenant_id} ---")
    db = SessionLocal()
    tenant = None
    try:
        tenant = db.get(models.Tenant, tenant_id)
        if not tenant or not tenant.tochka_api_token:
            logger.warning(f"[Tochka Sync] Пропуск Tenant ID {tenant_id}: интеграция неактивна или нет токена.")
            return

        alias_service = AliasService(db=db)
        eav_service = EAVService(db=db, alias_service=alias_service)
        owner = db.query(models.User).filter(models.User.tenant_id == tenant.id).first()
        if not owner:
            logger.error(f"[Tochka Sync] Не найден владелец для Tenant ID {tenant.id}")
            return

        sync_sources = json.loads(tenant.tochka_sync_sources or '{"accounts": []}')
        selected_accounts = sync_sources.get("accounts", [])
        if not selected_accounts:
            logger.warning(f"[Tochka Sync] У Tenant ID {tenant_id} не выбраны счета для синхронизации.")
            tenant.tochka_last_error = "Счета для синхронизации не выбраны в настройках."
            db.commit()
            return

        token = decrypt_data(tenant.tochka_api_token)
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

        # Определяем период для запроса
        end_date = datetime.now(timezone.utc)
        start_date = tenant.tochka_last_sync or (end_date - timedelta(days=30))

        params = {
            'startDateTime': start_date.isoformat(),
            'endDateTime': end_date.isoformat()
        }

        total_new_ops = 0
        for account_id in selected_accounts:
            params['accountId'] = account_id
            logger.info(f"[Tochka Sync] Запрос выписок для счета {account_id} с {start_date.isoformat()}")

            response = requests.get("https://enter.tochka.com/uapi/open-banking/v1.0/statements", headers=headers,
                                    params=params)
            response.raise_for_status()
            data = response.json()

            statements = data.get('Data', {}).get('Statement', [])
            if not statements:
                logger.info(f"[Tochka Sync] -> Для счета {account_id} нет новых выписок.")
                continue

            for statement in statements:
                for op in statement.get('Transaction', []):
                    op_id = op.get('transactionId')
                    if not op_id: continue

                    existing_op_filter = [{"field": "operation_id", "op": "eq", "value": str(op_id)}]
                    search_result = eav_service.get_all_entities_for_type(
                        entity_type_name=CRM_TABLE_NAME, current_user=owner, filters=existing_op_filter, limit=1
                    )
                    if search_result['total'] > 0:
                        continue

                    # Определяем контрагента и тип операции
                    op_type = "Списание"
                    contractor = op.get('CreditorParty', {}).get('name')
                    if op.get('creditDebitIndicator') == 'Credit':
                        op_type = "Поступление"
                        contractor = op.get('DebtorParty', {}).get('name')

                    op_data = {
                        "operation_id": str(op_id),
                        "amount": op.get('Amount', {}).get('amount'),
                        "currency": op.get('Amount', {}).get('currency'),
                        "operation_type": op_type,
                        "contractor_name": contractor,
                        "purpose": op.get('description'),
                        "operation_date": op.get('documentProcessDate'),
                    }

                    op_data_cleaned = {k: v for k, v in op_data.items() if v is not None}
                    eav_service.create_entity(CRM_TABLE_NAME, op_data_cleaned, owner)
                    total_new_ops += 1

        logger.info(f"[Tochka Sync] Обработка завершена. Сохранено {total_new_ops} новых операций.")
        tenant.tochka_last_sync = datetime.now(timezone.utc)
        tenant.tochka_last_error = None
        db.commit()

    except Exception as e:
        logger.error(f"[Tochka Sync] Ошибка при синхронизации для Tenant ID {tenant_id}: {e}", exc_info=True)
        if tenant:
            tenant.tochka_last_error = str(e)[:1000]
            db.commit()
    finally:
        db.close()