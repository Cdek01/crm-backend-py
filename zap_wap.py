# zapr.py

import requests
import json
import time
from datetime import datetime

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8000"
# BASE_URL = "http://89.111.169.47:8005"  # Если тестируете на удаленном сервере
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"testuser_{TIMESTAMP}@example.com"
USER_PASSWORD = "a_very_secure_password"
CUSTOM_TABLE_NAME = f"contracts_{TIMESTAMP}"  # Изменим на "контракты" для разнообразия

# Глобальные переменные для хранения состояния между тестами
AUTH_TOKEN = None
CREATED_IDS = {
    "lead": None,
    "legal_entity": None,
    "individual": None,
    "entity_type": None,
    "entity_instance": None,
}


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ (без изменений) ---
def print_response(name: str, response: requests.Response):
    """Красиво печатает результат запроса."""
    print(f"--- {name} ---")
    print(f"URL: {response.request.method} {response.url}")
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
        print("Response Text:", response.text)
    print("-" * 50 + "\n")


# --- СУЩЕСТВУЮЩИЕ ТЕСТЫ (оставим только нужные для этого сценария) ---

def test_01_auth():
    # ... (код этого теста без изменений)
    global AUTH_TOKEN
    print("====== НАЧАЛО ТЕСТА: АУТЕНТИФИКАЦИЯ ======")
    unique_full_name = f"Тестовый Пользователь {TIMESTAMP}"
    user_data = {
        "email": UNIQUE_EMAIL,
        "password": USER_PASSWORD,
        "full_name": unique_full_name
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print_response("1. User Registration", response)
    assert response.status_code == 201, "Регистрация не удалась"
    login_data = {"username": UNIQUE_EMAIL, "password": USER_PASSWORD}
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    print_response("2. User Login (Get Token)", response)
    assert response.status_code == 200, "Вход не удался"
    token_data = response.json()
    AUTH_TOKEN = token_data.get("access_token")
    assert AUTH_TOKEN, "Токен не был получен"
    print("SUCCESS: Аутентификация пройдена, токен получен!\n")


def test_05_meta_crud_for_messaging():
    """Создаем 'таблицу' Контракты со всеми системными полями для рассылки."""
    if not AUTH_TOKEN: raise AssertionError("Пропускаем тест метаданных: нет токена авторизации.")
    print("====== НАЧАЛО ТЕСТА: META API (для рассылки) ======")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # 1. Создание нового типа сущности ('таблицы')
    entity_type_data = {
        "name": CUSTOM_TABLE_NAME,
        "display_name": f"Контракты {TIMESTAMP}"
    }
    response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=entity_type_data)
    print_response("Meta - 1. Create Entity Type 'Contracts'", response)
    assert response.status_code == 201
    # Проверяем, что системные поля создались автоматически
    assert any(attr['name'] == 'send_sms_trigger' for attr in response.json()['attributes'])
    assert any(attr['name'] == 'sms_status' for attr in response.json()['attributes'])
    assert any(attr['name'] == 'phone_number' for attr in response.json()['attributes'])
    CREATED_IDS["entity_type"] = response.json()['id']
    print("====== ТЕСТ META API (для рассылки) УСПЕШНО ЗАВЕРШЕН ======\n")


# --- НОВЫЙ ТЕСТ ДЛЯ ПРОВЕРКИ РАССЫЛКИ ---

def test_07_messaging_task():
    """Тестирует полный цикл запуска фоновой задачи на отправку сообщения."""
    if not AUTH_TOKEN or not CREATED_IDS["entity_type"]:
        raise AssertionError("Пропускаем тест рассылки: нет токена или не создан тип сущности.")

    print(f"====== НАЧАЛО ТЕСТА: MESSAGING TASK (для таблицы '{CUSTOM_TABLE_NAME}') ======")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # 1. Создание записи ('контракта') с номером телефона и текстом
    entity_data = {
        # Замените на реальный номер для теста, если хотите увидеть сообщение
        "phone_number": "9952116323",
        "message_text": f"Тестовое сообщение для контракта #{TIMESTAMP}",
        "sms_status": "new"  # Начальный статус
    }
    response = requests.post(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}", headers=headers, json=entity_data)
    print_response("Messaging - 1. Create contract instance", response)
    assert response.status_code == 201
    CREATED_IDS["entity_instance"] = response.json()['id']
    entity_id = CREATED_IDS["entity_instance"]

    # 2. Обновление записи для запуска триггера рассылки
    print("\n>>> Запускаем триггер отправки сообщения...\n")
    update_data = {
        "send_sms_trigger": True
    }
    response = requests.put(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}/{entity_id}", headers=headers, json=update_data)
    print_response("Messaging - 2. Trigger sending message", response)
    assert response.status_code == 200
    # Сразу после запроса статус должен стать 'pending'
    assert response.json()['sms_status'] == 'pending'

    # 3. Ожидание и проверка результата
    print("\n>>> Ждем 10 секунд, чтобы фоновая задача выполнилась...")
    time.sleep(10)

    print("\n>>> Проверяем финальный статус записи...\n")
    response = requests.get(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}/{entity_id}", headers=headers)
    print_response("Messaging - 3. Verify final status", response)
    assert response.status_code == 200
    final_status = response.json().get('sms_status')

    # Проверяем, что статус изменился на 'sent' или 'error'
    assert final_status in ['sent', 'error'], f"Неожиданный финальный статус: {final_status}"

    if final_status == 'error':
        print(
            "!!! ВНИМАНИЕ: Задача завершилась с ошибкой. Это может быть нормально, если API Wappi недоступен или ключи неверны.")
        print(f"Текст ошибки: {response.json().get('sms_last_error')}")
    else:
        print("УСПЕХ: Фоновая задача успешно выполнена, статус изменен на 'sent'.")

    print("====== ТЕСТ MESSAGING TASK УСПЕШНО ЗАВЕРШЕН ======\n")


# --- Основной блок запуска ---

if __name__ == "__main__":
    try:
        # Запускаем тесты последовательно
        test_01_auth()
        test_05_meta_crud_for_messaging()
        test_07_messaging_task()

        print("\n\n" + "=" * 20 + " ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! " + "=" * 20)
    except requests.exceptions.ConnectionError as e:
        print(f"\n[ОШИБКА] Не удалось подключиться к серверу {BASE_URL}.")
        print(f"Детали: {e}")
        print("Убедитесь, что ваш FastAPI сервер запущен командой 'uvicorn main:app --reload'.")
    except AssertionError as e:
        print(f"\n[ОШИБКА] Тест провален: {e}")