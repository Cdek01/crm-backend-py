# test_api.py

import requests
import json
import time
from datetime import datetime

# --- НАСТРОЙКИ ---
# BASE_URL = "http://127.0.0.1:8000"
BASE_URL = "http://89.111.169.47:8005"
# Генерируем уникальный email, чтобы можно было запускать скрипт много раз
UNIQUE_EMAIL = f"testuser_{int(time.time())}@example.com"
USER_PASSWORD = "a_very_secure_password"
TIMESTAMP = int(time.time())
CUSTOM_TABLE_NAME = f"projects_{TIMESTAMP}"

# Глобальные переменные для хранения состояния между тестами
AUTH_TOKEN = None
CREATED_IDS = {
    "lead": None,
    "legal_entity": None,
    "individual": None,
}


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КРАСИВОГО ВЫВОДА ---
def print_response(name: str, response: requests.Response):
    """Красиво печатает результат запроса."""
    print(f"--- {name} ---")
    print(f"URL: {response.request.method} {response.url}")
    print(f"Status Code: {response.status_code}")
    try:
        # Печатаем JSON с отступами и поддержкой кириллицы
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
        print("Response Text:", response.text)
    print("-" * 50 + "\n")


# --- ТЕСТЫ ---

def test_01_auth():
    """Тестирование регистрации, входа и получения данных о себе."""
    global AUTH_TOKEN
    print("====== НАЧАЛО ТЕСТА: АУТЕНТИФИКАЦИЯ ======")

    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    # Генерируем уникальное имя пользователя, как и email
    unique_full_name = f"Тестовый Пользователь {TIMESTAMP}"

    # 1. Регистрация
    user_data = {
        "email": UNIQUE_EMAIL,
        "password": USER_PASSWORD,
        "full_name": unique_full_name  # <-- Используем уникальное имя
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print_response("1. User Registration", response)
    assert response.status_code == 201, "Регистрация не удалась"

    # 2. Вход в систему (получение токена)
    login_data = {"username": UNIQUE_EMAIL, "password": USER_PASSWORD}
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    print_response("2. User Login (Get Token)", response)
    assert response.status_code == 200, "Вход не удался"

    token_data = response.json()
    AUTH_TOKEN = token_data.get("access_token")
    assert AUTH_TOKEN, "Токен не был получен"
    print("SUCCESS: Аутентификация пройдена, токен получен!\n")


def test_02_leads_crud():
    """Тестирование CRUD операций для Лидов."""
    if not AUTH_TOKEN: raise AssertionError("Пропускаем тест лидов: нет токена авторизации.")
    print("====== НАЧАЛО ТЕСТА: ЛИДЫ (LEADS) ======")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # 1. Создание лида
    response = requests.post(f"{BASE_URL}/api/leads/", headers=headers, json={
        "organization_name": "ООО 'Перспективные Технологии'",
        "contact_number": "+79991234567",
        "source": "Холодный звонок"
    })
    print_response("Leads - 1. Create", response)
    assert response.status_code == 201
    CREATED_IDS["lead"] = response.json()['id']

    # 2. Получение списка лидов
    response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
    print_response("Leads - 2. Get All", response)
    assert response.status_code == 200 and len(response.json()) > 0

    # 3. Получение одного лида
    lead_id = CREATED_IDS["lead"]
    response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=headers)
    print_response("Leads - 3. Get One", response)
    assert response.status_code == 200

    # 4. Обновление лида
    response = requests.put(f"{BASE_URL}/api/leads/{lead_id}", headers=headers, json={
        "lead_status": "В работе", "rating": 5
    })
    print_response("Leads - 4. Update", response)
    assert response.status_code == 200 and response.json()['lead_status'] == "В работе"

    # 5. Удаление лида
    response = requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=headers)
    print_response("Leads - 5. Delete", response)
    assert response.status_code == 204

    # 6. Проверка удаления
    response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=headers)
    print_response("Leads - 6. Verify Deletion", response)
    assert response.status_code == 404
    print("====== ТЕСТ ЛИДОВ УСПЕШНО ЗАВЕРШЕН ======\n")


def test_03_legal_entities_crud():
    """Тестирование CRUD операций для Юридических лиц."""
    if not AUTH_TOKEN: raise AssertionError("Пропускаем тест юр. лиц: нет токена авторизации.")
    print("====== НАЧАЛО ТЕСТА: ЮРИДИЧЕСКИЕ ЛИЦА (LEGAL ENTITIES) ======")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    inn = f"77{int(time.time()) % 100000000:08d}"  # Уникальный ИНН

    # 1. Создание
    response = requests.post(f"{BASE_URL}/api/legal-entities/", headers=headers, json={
        "inn": inn, "short_name": "ПАО 'Ромашка'", "address": "г. Москва, ул. Цветочная, д. 1"
    })
    print_response("Legal Entities - 1. Create", response)
    assert response.status_code == 201
    CREATED_IDS["legal_entity"] = response.json()['id']

    # 2. Получение списка
    response = requests.get(f"{BASE_URL}/api/legal-entities/", headers=headers)
    print_response("Legal Entities - 2. Get All", response)
    assert response.status_code == 200 and len(response.json()) > 0

    # 3. Получение одного
    entity_id = CREATED_IDS["legal_entity"]
    response = requests.get(f"{BASE_URL}/api/legal-entities/{entity_id}", headers=headers)
    print_response("Legal Entities - 3. Get One", response)
    assert response.status_code == 200

    # 4. Обновление
    response = requests.put(f"{BASE_URL}/api/legal-entities/{entity_id}", headers=headers, json={
        "status": "Действующая", "revenue": 1000000.50
    })
    print_response("Legal Entities - 4. Update", response)
    assert response.status_code == 200 and response.json()['status'] == "Действующая"

    # 5. Удаление
    response = requests.delete(f"{BASE_URL}/api/legal-entities/{entity_id}", headers=headers)
    print_response("Legal Entities - 5. Delete", response)
    assert response.status_code == 204

    # 6. Проверка удаления
    response = requests.get(f"{BASE_URL}/api/legal-entities/{entity_id}", headers=headers)
    print_response("Legal Entities - 6. Verify Deletion", response)
    assert response.status_code == 404
    print("====== ТЕСТ ЮР. ЛИЦ УСПЕШНО ЗАВЕРШЕН ======\n")


def test_04_individuals_crud():
    """Тестирование CRUD операций для Физических лиц."""
    if not AUTH_TOKEN: raise AssertionError("Пропускаем тест физ. лиц: нет токена авторизации.")
    print("====== НАЧАЛО ТЕСТА: ФИЗИЧЕСКИЕ ЛИЦА (INDIVIDUALS) ======")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # 1. Создание
    response = requests.post(f"{BASE_URL}/api/individuals/", headers=headers, json={
        "full_name": "Иванов Иван Иванович", "phone_number": "+79167654321",
        "email": f"ivanov_{int(time.time())}@mail.com"
    })
    print_response("Individuals - 1. Create", response)
    assert response.status_code == 201
    CREATED_IDS["individual"] = response.json()['id']

    # 2. Получение списка
    response = requests.get(f"{BASE_URL}/api/individuals/", headers=headers)
    print_response("Individuals - 2. Get All", response)
    assert response.status_code == 200 and len(response.json()) > 0

    # 3. Получение одного
    individual_id = CREATED_IDS["individual"]
    response = requests.get(f"{BASE_URL}/api/individuals/{individual_id}", headers=headers)
    print_response("Individuals - 3. Get One", response)
    assert response.status_code == 200

    # 4. Обновление
    response = requests.put(f"{BASE_URL}/api/individuals/{individual_id}", headers=headers, json={
        "city": "Санкт-Петербург", "notes": "Ключевой клиент"
    })
    print_response("Individuals - 4. Update", response)
    assert response.status_code == 200 and response.json()['city'] == "Санкт-Петербург"

    # 5. Удаление
    response = requests.delete(f"{BASE_URL}/api/individuals/{individual_id}", headers=headers)
    print_response("Individuals - 5. Delete", response)
    assert response.status_code == 204

    # 6. Проверка удаления
    response = requests.get(f"{BASE_URL}/api/individuals/{individual_id}", headers=headers)
    print_response("Individuals - 6. Verify Deletion", response)
    assert response.status_code == 404
    print("====== ТЕСТ ФИЗ. ЛИЦ УСПЕШНО ЗАВЕРШЕН ======\n")


# --- НОВЫЕ ТЕСТЫ ДЛЯ EAV ---

def test_05_meta_crud():
    """Тестирование создания 'таблиц' (EntityType) и 'колонок' (Attribute)."""
    if not AUTH_TOKEN: raise AssertionError("Пропускаем тест метаданных: нет токена авторизации.")
    print("====== НАЧАЛО ТЕСТА: META API (Конструктор таблиц) ======")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # 1. Создание нового типа сущности ('таблицы')
    entity_type_data = {
        "name": CUSTOM_TABLE_NAME,
        "display_name": f"Проекты {TIMESTAMP}"
    }
    response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=entity_type_data)
    print_response("Meta - 1. Create Entity Type ('Table')", response)
    assert response.status_code == 201
    CREATED_IDS["entity_type"] = response.json()['id']
    entity_type_id = CREATED_IDS["entity_type"]

    # 2. Добавление атрибутов ('колонок') в эту 'таблицу'
    attributes_to_create = [
        {"name": "project_title", "display_name": "Название проекта", "value_type": "string"},
        {"name": "budget", "display_name": "Бюджет", "value_type": "float"},
        {"name": "is_active", "display_name": "Активен", "value_type": "boolean"},
        {"name": "tasks_count", "display_name": "Количество задач", "value_type": "integer"},
    ]

    for i, attr in enumerate(attributes_to_create):
        response = requests.post(
            f"{BASE_URL}/api/meta/entity-types/{entity_type_id}/attributes",
            headers=headers,
            json=attr
        )
        print_response(f"Meta - 2.{i + 1}. Create Attribute ('Column')", response)
        assert response.status_code == 201

    print("====== ТЕСТ META API УСПЕШНО ЗАВЕРШЕН ======\n")


def test_06_data_crud():
    """Тестирование CRUD для данных в созданной пользовательской 'таблице'."""
    if not AUTH_TOKEN or not CREATED_IDS["entity_type"]:
        raise AssertionError("Пропускаем тест данных: нет токена или не создан тип сущности.")

    print(f"====== НАЧАЛО ТЕСТА: DATA API (данные для таблицы '{CUSTOM_TABLE_NAME}') ======")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # 1. Создание записи ('строки')
    entity_data = {
        "project_title": "Разработка нового модуля CRM",
        "budget": 150000.50,
        "is_active": True,
        "tasks_count": 10
    }
    response = requests.post(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}", headers=headers, json=entity_data)
    print_response("Data - 1. Create Entity ('Row')", response)
    assert response.status_code == 201
    assert response.json()['project_title'] == "Разработка нового модуля CRM"
    CREATED_IDS["entity_instance"] = response.json()['id']
    entity_id = CREATED_IDS["entity_instance"]

    # 2. Получение списка всех записей
    response = requests.get(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}", headers=headers)
    print_response("Data - 2. Get All Entities", response)
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 3. Получение одной записи по ID
    response = requests.get(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}/{entity_id}", headers=headers)
    print_response("Data - 3. Get One Entity", response)
    assert response.status_code == 200
    assert response.json()['id'] == entity_id

    # 4. Обновление записи
    update_data = {
        "project_title": "Завершение разработки модуля CRM",
        "budget": 200000.0,
        "is_active": False,
        "tasks_count": 25
    }
    response = requests.put(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}/{entity_id}", headers=headers, json=update_data)
    print_response("Data - 4. Update Entity", response)
    assert response.status_code == 200
    assert response.json()['is_active'] is False
    assert response.json()['tasks_count'] == 25

    # 5. Удаление записи
    response = requests.delete(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}/{entity_id}", headers=headers)
    print_response("Data - 5. Delete Entity", response)
    assert response.status_code == 204

    # 6. Проверка удаления
    response = requests.get(f"{BASE_URL}/api/data/{CUSTOM_TABLE_NAME}/{entity_id}", headers=headers)
    print_response("Data - 6. Verify Deletion", response)
    assert response.status_code == 404

    print("====== ТЕСТ DATA API УСПЕШНО ЗАВЕРШЕН ======\n")


# --- Основной блок запуска ---

if __name__ == "__main__":
    try:
        # Сначала выполняем старые тесты
        test_01_auth()
        # test_02_leads_crud() # Можно временно закомментировать, чтобы ускорить тесты
        # test_03_legal_entities_crud()
        # test_04_individuals_crud()

        # Затем новые тесты для конструктора
        test_05_meta_crud()
        test_06_data_crud()

        print("\n\n" + "=" * 20 + " ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! " + "=" * 20)
    except requests.exceptions.ConnectionError:
        print(f"\n[ОШИБКА] Не удалось подключиться к серверу {BASE_URL}.")
        print("Убедитесь, что ваш FastAPI сервер запущен командой 'uvicorn main:app --reload'.")
    except AssertionError as e:
        print(f"\n[ОШИБКА] Тест провален: {e}")