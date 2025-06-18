# test_api.py

import requests
import json
import time

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8000"
# Генерируем уникальный email, чтобы можно было запускать скрипт много раз
UNIQUE_EMAIL = f"testuser_{int(time.time())}@example.com"
USER_PASSWORD = "a_very_secure_password"

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

    # 1. Регистрация
    user_data = {
        "email": UNIQUE_EMAIL,
        "password": USER_PASSWORD,
        "full_name": "Тестовый Пользователь"
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


if __name__ == "__main__":
    try:
        test_01_auth()
        test_02_leads_crud()
        test_03_legal_entities_crud()
        test_04_individuals_crud()
        print("\n\n" + "=" * 20 + " ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! " + "=" * 20)
    except requests.exceptions.ConnectionError:
        print(f"\n[ОШИБКА] Не удалось подключиться к серверу {BASE_URL}.")
        print("Убедитесь, что ваш FastAPI сервер запущен командой 'uvicorn main:app --reload'.")
    except AssertionError as e:
        print(f"\n[ОШИБКА] Тест провален: {e}")