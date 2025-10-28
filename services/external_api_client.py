# services/external_api_client.py
import requests
from typing import Dict, Any
import logging
from core.config import settings
import json # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ
from datetime import date, datetime # <-- И ЭТОТ

# Настраиваем простой логгер
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- НОВЫЙ ВСПОМОГАТЕЛЬНЫЙ КЛАСС ---
class DateTimeEncoder(json.JSONEncoder):
    """
    Кастомный JSON-кодировщик, который умеет преобразовывать
    объекты datetime и date в строки формата ISO 8601.
    """
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)
# --- КОНЕЦ НОВОГО КЛАССА ---

def send_update_to_colleague(event_type: str, table_name: str, entity_id: Any, data: Dict[str, Any]):
    """
    Отправляет уведомление об изменении во внешнее API.
    Безопасно обрабатывает ошибки и корректно сериализует даты.
    """
    if not settings.EXTERNAL_API_URL:
        return

    payload = {
        "event_type": event_type,
        "table_name": table_name,
        "entity_id": entity_id,
        "changed_data": data,
        "source_system": "MyCRM"
    }

    try:
        logging.info(f"Отправка уведомления на {settings.EXTERNAL_API_URL} с данными...")

        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Вместо того чтобы полагаться на requests, мы сами кодируем payload в JSON,
        # используя наш кастомный кодировщик DateTimeEncoder.
        # Это превратит все объекты datetime в строки.
        json_payload = json.dumps(payload, cls=DateTimeEncoder)

        # Устанавливаем заголовок Content-Type вручную
        headers = {'Content-Type': 'application/json'}

        response = requests.post(
            settings.EXTERNAL_API_URL,
            data=json_payload,  # <-- Отправляем как data, а не json
            headers=headers,
            timeout=30
        )
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---

        response.raise_for_status()

        logging.info(f"Уведомление для {event_type} в {table_name} успешно доставлено.")

    except requests.exceptions.RequestException as e:
        logging.error(f"ОШИБКА: Не удалось отправить уведомление во внешнее API. Причина: {e}")
