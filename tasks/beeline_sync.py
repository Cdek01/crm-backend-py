from typing import Optional
import os  # <-- Импорт для работы с путями
import uuid # <-- Импорт для генерации уникальных имен
import requests
import json
import logging
from datetime import datetime, timedelta, timezone

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


# Путь к папке, куда будут сохраняться записи
AUDIO_UPLOAD_DIR = os.path.join("static", "uploads", "audio")
os.makedirs(AUDIO_UPLOAD_DIR, exist_ok=True)

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

        date_from = datetime.now(timezone.utc) - timedelta(days=1)
        if tenant.beeline_last_sync:
            date_from = tenant.beeline_last_sync - timedelta(minutes=5)

        params = {"dateFrom": date_from.strftime("%Y-%m-%d"), "dateTo": datetime.now(timezone.utc).strftime("%Y-%m-%d")}

        logger.info(f"[Beeline Sync] Запрос звонков для Tenant ID {tenant.id} с параметрами: {params}")
        response = requests.get(f"{settings.BEELINE_BASE_URL}/records", headers=headers, params=params)
        response.raise_for_status()
        calls = response.json()

        logger.info(f"[Beeline Sync] Получено {len(calls)} звонков от API для Tenant ID {tenant.id}.")

        # --- НАЧАЛО ВОССТАНОВЛЕННОГО БЛОКА ---
        new_calls_count = 0
        if not calls:
            logger.info("[Beeline Sync] Новых звонков для обработки нет.")
        else:
            for call in calls:
                call_id = call.get("id")
                if not call_id:
                    continue

                # Проверяем, не был ли этот звонок уже сохранен
                existing_call_filter = [{"field": "call_id", "op": "eq", "value": str(call_id)}]
                search_result = eav_service.get_all_entities_for_type(
                    entity_type_name=CRM_TABLE_NAME,
                    current_user=owner,
                    filters=existing_call_filter,
                    limit=1
                )

                if search_result['total'] > 0:
                    continue

                # Звонок новый, обрабатываем и сохраняем
                call_date = datetime.fromtimestamp(call.get("date", 0) / 1000)
                duration_seconds = round(call.get("duration", 0) / 1000)

                # --- 1. Скачиваем файл записи разговора ---
                audio_url_path = ""  # Путь по умолчанию, если скачать не удалось
                call_id = call.get("id")
                try:
                    logger.info(f"[Beeline Sync] Попытка скачать запись для звонка ID: {call_id}...")
                    download_url = f"{settings.BEELINE_BASE_URL}/records/{call_id}/download"

                    # Делаем запрос на скачивание, stream=True для эффективности
                    record_response = requests.get(download_url, headers=headers, stream=True, timeout=30)
                    record_response.raise_for_status()

                    # Генерируем уникальное имя файла. Расширение можно взять из заголовков, если есть, или .mp3 по умолчанию
                    # Content-Disposition: attachment; filename="record.mp3"
                    content_disp = record_response.headers.get('Content-Disposition', '')
                    original_filename = [part for part in content_disp.split(';') if 'filename' in part]
                    file_extension = os.path.splitext(original_filename[0] if original_filename else ".mp3")[1]

                    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
                    file_path = os.path.join(AUDIO_UPLOAD_DIR, unique_filename)

                    # Сохраняем файл на диск
                    with open(file_path, "wb") as f:
                        for chunk in record_response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    # Формируем относительный URL для сохранения в БД
                    audio_url_path = f"/{os.path.join('static', 'uploads', 'audio', unique_filename).replace(os.path.sep, '/')}"
                    logger.info(f"[Beeline Sync] Запись успешно сохранена: {audio_url_path}")

                except requests.exceptions.HTTPError as e:
                    # Часто API возвращает 404, если записи нет. Это не критическая ошибка.
                    if e.response.status_code == 404:
                        logger.warning(f"Запись для звонка ID: {call_id} не найдена (404).")
                    else:
                        logger.error(f"Ошибка HTTP при скачивании записи для звонка {call_id}: {e}")
                except Exception as e:
                    logger.error(f"Не удалось скачать или сохранить запись для звонка {call_id}: {e}")

                # --- 2. Готовим данные для CRM, включая ссылку на аудио ---
                call_date = datetime.fromtimestamp(call.get("date", 0) / 1000)
                duration_seconds = round(call.get("duration", 0) / 1000)

                call_data_for_crm = {
                    "call_id": str(call_id),
                    "external_phone": call.get("phone"),
                    "direction": call.get("direction"),
                    "call_date": call_date.isoformat(),
                    "duration_seconds": duration_seconds,
                    "internal_user": call.get("abonent", {}).get("extension"),
                    "audio_record": audio_url_path  # <-- Добавляем путь к файлу
                }

                eav_service.create_entity(CRM_TABLE_NAME, call_data_for_crm, owner)
                new_calls_count += 1

            logger.info(f"[Beeline Sync] Обработка завершена. Сохранено {new_calls_count} новых звонков.")
        # --- КОНЕЦ ВОССТАНОВЛЕННОГО БЛОКА ---

        # Обновляем статус в БД, если все прошло успешно
        tenant.beeline_last_sync = datetime.now(timezone.utc)
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