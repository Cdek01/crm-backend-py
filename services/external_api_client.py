# services/external_api_client.py
import requests
from typing import Dict, Any
import logging
from core.config import settings

# Настраиваем простой логгер
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def send_update_to_colleague(event_type: str, table_name: str, entity_id: Any, data: Dict[str, Any]):
    """
    Отправляет уведомление об изменении во внешнее API.
    Безопасно обрабатывает ошибки, не прерывая работу основного приложения.
    """
    # 1. Проверяем, настроен ли URL. Если нет - тихо выходим.
    if not settings.EXTERNAL_API_URL:
        # Это не ошибка, а штатная ситуация, если интеграция не настроена.
        # Поэтому здесь можно ничего не логировать или использовать logging.DEBUG.
        return

    # 2. Формируем тело запроса
    payload = {
        "event_type": event_type,
        "table_name": table_name,
        "entity_id": entity_id,
        "changed_data": data,
        "source_system": "MyCRM"
    }

    try:
        # 3. Отправляем POST-запрос с таймаутом
        logging.info(f"Отправка уведомления на {settings.EXTERNAL_API_URL} с данными: {payload}")

        # Устанавливаем таймаут (например, 5 секунд), чтобы не ждать вечно
        response = requests.post(settings.EXTERNAL_API_URL, json=payload, timeout=5)

        # Проверяем, что API коллеги ответило успехом (статус 2xx).
        # Если статус 4xx или 5xx, будет выброшено исключение HTTPError.
        response.raise_for_status()

        logging.info(f"Уведомление для {event_type} в {table_name} успешно доставлено.")

    except requests.exceptions.RequestException as e:
        # --- БЛОК ПЕРЕХВАТА ОШИБОК ---
        # Этот блок `except` сработает для ЛЮБОЙ проблемы с запросом:
        # - ConnectionError: Сервер коллеги не запущен или недоступен.
        # - Timeout: Сервер коллеги не ответил за 5 секунд.
        # - HTTPError: Сервер коллеги ответил с ошибкой (например, 404, 500).

        # Мы логируем ошибку, но НЕ пробрасываем ее дальше.
        # Работа основного приложения продолжится без сбоев.
        logging.error(f"ОШИБКА: Не удалось отправить уведомление во внешнее API. Причина: {e}")
        # -----------------------------
