# tasks/messaging.py
import logging
from celery_worker import celery_app
from api.wappi import api as send_wappi_text_message

from db.session import SessionLocal
from services.eav_service import EAVService

# Настраиваем логгер
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="send_sms_for_entity")
def send_sms_for_entity_task(self, entity_id: int):
    """
    Фоновая задача, которая отправляет сообщение и обновляет статус.
    `bind=True` позволяет получить доступ к самой задаче через `self`.
    """
    logger.info(f"Начинаю задачу для entity_id: {entity_id}")
    logger.info(f"Начинаю задачу для entity_id: {entity_id}")
    db = SessionLocal()
    eav_service = EAVService(db=db)

    try:
        # ... (код обновления статуса и получения данных без изменений)
        eav_service.update_entity(entity_id, {"sms_status": "processing"})
        entity_data = eav_service.get_entity_by_id(entity_id)
        phone = entity_data.get("phone_number")
        text = entity_data.get("message_text")

        logger.info(f"Данные для отправки: phone={phone}, text='{text}'")

        if not phone or not text:
            raise ValueError("Не указан номер телефона или текст сообщения")

        # 3. Вызываем ваш API для отправки
        logger.info(f"Отправляю сообщение через Wappi для entity_id: {entity_id}")

        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Убираем третий аргумент `folder_path`
        has_error = send_wappi_text_message(nomer=phone, text=text)

        # 4. Обновляем финальный статус
        if has_error:
            # ... (остальной код обработки ошибок без изменений)
            error_message = "Не удалось отправить текстовое сообщение через Wappi."
            logger.error(f"Ошибка Wappi для entity_id: {entity_id}. {error_message}")
            eav_service.update_entity(entity_id, {
                "sms_status": "error",
                "sms_last_error": error_message
            })
        else:
            logger.info(f"Успешная отправка для entity_id: {entity_id}. Обновляю статус на 'sent'")
            eav_service.update_entity(entity_id, {"sms_status": "sent"})

    except Exception as e:
        logger.error(f"Критическая ошибка в задаче для entity_id: {entity_id}", exc_info=True)
        # exc_info=True добавит полный traceback в лог
        try:
            eav_service.update_entity(entity_id, {
                "sms_status": "error",
                "sms_last_error": str(e)
            })
        except Exception as db_err:
            logger.error(f"НЕ УДАЛОСЬ ОБНОВИТЬ СТАТУС ОШИБКИ для entity_id: {entity_id}. Ошибка БД: {db_err}")
    finally:
        db.close()
        logger.info(f"Задача для entity_id: {entity_id} завершена.")