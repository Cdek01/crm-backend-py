# tasks/messaging.py
import logging
from celery_worker import celery_app
from db import models
from db.session import SessionLocal
from api import wappi
from typing import Dict, Any
from sqlalchemy.orm import Session


# Настраиваем логгер
logger = logging.getLogger(__name__)


@celery_app.task
def send_sms_for_entity_task(entity_id: int, user_id: int):  # <-- Добавляем user_id
    """
    Фоновая задача для отправки SMS.
    """
    print(f"Запущена задача для entity_id={entity_id}, инициирована user_id={user_id}")

    db: Session = SessionLocal()
    try:
        from services.eav_service import EAVService

        # 1. Загружаем объект пользователя из БД
        initiator_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not initiator_user:
            print(f"Критическая ошибка: пользователь с ID={user_id} не найден. Задача прервана.")
            # Можно обновить статус на error, но без пользователя это сложно
            return

        # 2. Создаем экземпляр сервиса
        eav_service = EAVService(db=db)

        # 3. Получаем данные сущности (объект-словарь)
        # Мы передаем initiator_user, чтобы get_entity_by_id мог проверить права
        entity_data = eav_service.get_entity_by_id(entity_id, current_user=initiator_user)

        phone_number = entity_data.get("phone_number")
        message_text = entity_data.get("message_text")

        if not phone_number or not message_text:
            error_message = "Отсутствует номер телефона или текст сообщения."
            eav_service.update_entity(
                entity_id,
                {"sms_status": "error", "sms_last_error": error_message},
                current_user=initiator_user  # <-- Передаем пользователя
            )
            return

        # 4. Вызываем функцию отправки
        has_error = wappi.api(nomer=phone_number, text=message_text)

        # 5. Обновляем статус в базе данных
        if has_error:
            eav_service.update_entity(
                entity_id,
                {"sms_status": "error", "sms_last_error": "Ошибка при отправке через API Wappi."},
                current_user=initiator_user  # <-- Передаем пользователя
            )
        else:
            eav_service.update_entity(
                entity_id,
                {"sms_status": "sent", "sms_last_error": None},
                current_user=initiator_user  # <-- Передаем пользователя
            )
            print(f"Задача для entity_id={entity_id} успешно выполнена.")

    finally:
        db.close()




@celery_app.task
def send_webhook_task(event_type: str, table_name: str, entity_id: Any, data: Dict[str, Any], tenant_id: int):
    """
    Фоновая задача для отправки уведомления (вебхука) во внешнее API.
    """
    # Импортируем клиент здесь, чтобы избежать циклических импортов
    from services import external_api_client

    logger.info(f"Запущена задача send_webhook_task для tenant_id={tenant_id}, событие='{event_type}', таблица='{table_name}'")

    # Вся логика отправки теперь находится здесь, в фоновом режиме.
    # Основное приложение не будет ждать ее выполнения.
    external_api_client.send_update_to_colleague(
        event_type=event_type,
        table_name=table_name,
        entity_id=entity_id,
        data=data
    )