# tasks/enrichment.py
import logging
from datetime import datetime

from dadata import Dadata
from celery_worker import celery_app
from core.config import settings
from db.session import SessionLocal
from db import models
from services.eav_service import EAVService
from services.alias_service import AliasService

logger = logging.getLogger(__name__)


@celery_app.task
def enrich_data_by_inn_task(entity_id: int, inn: str, user_id: int):
    """
    Фоновая задача для обогащения данных по ИНН через DaData.
    """
    if not settings.DADATA_API_KEY or not settings.DADATA_SECRET_KEY:
        logger.warning("Ключи DaData не настроены. Обогащение данных по ИНН пропущено.")
        return

    logger.info(f"Запуск обогащения для Entity ID: {entity_id} по ИНН: {inn}")
    db = None
    try:
        dadata = Dadata(settings.DADATA_API_KEY, settings.DADATA_SECRET_KEY)
        results = dadata.find_by_id("party", inn, count=1)

        if not results:
            logger.warning(f"DaData не нашла информацию по ИНН: {inn}")
            return

        company_data = results[0]

        # --- Сопоставление полей DaData с вашими стандартными именами колонок ---
        # Ключ - системное имя колонки в вашей CRM, Значение - путь к данным в ответе DaData
        mapping = {
            "full_name": "value",
            "short_name": "name.short_with_opf",
            "ogrn": "data.ogrn",
            "kpp": "data.kpp",
            "address": "data.address.unrestricted_value",
            "manager_name": "data.management.name",
            "manager_post": "data.management.post",
            "company_status": "data.state.status",
            "registration_date": "data.state.registration_date",
        }

        update_payload = {}
        for crm_field, dadata_path in mapping.items():
            # Безопасно извлекаем вложенные значения из ответа DaData
            value = company_data
            try:
                for key in dadata_path.split('.'):
                    value = value.get(key)
                if value:
                    # Преобразуем дату из миллисекунд в нужный формат, если это дата
                    if crm_field.endswith("_date") and isinstance(value, int):
                        update_payload[crm_field] = datetime.fromtimestamp(value / 1000).isoformat()
                    else:
                        update_payload[crm_field] = value
            except (AttributeError, KeyError):
                continue

        if not update_payload:
            logger.info(f"Не удалось извлечь значимых данных для ИНН: {inn}")
            return

        # --- Обновляем запись в нашей CRM ---
        db = SessionLocal()
        alias_service = AliasService(db=db)
        eav_service = EAVService(db=db, alias_service=alias_service)
        current_user = db.query(models.User).get(user_id)

        logger.info(f"Обновление Entity ID {entity_id}. Данные для обновления: {update_payload}")
        eav_service.update_entity(entity_id, update_payload, current_user)

        logger.info(f"Обогащение для Entity ID: {entity_id} успешно завершено.")

    except Exception as e:
        logger.error(f"Ошибка в задаче обогащения для Entity ID {entity_id}: {e}", exc_info=True)
        # Не пробрасываем ошибку дальше, чтобы не завалить очередь Celery
    finally:
        if db:
            db.close()