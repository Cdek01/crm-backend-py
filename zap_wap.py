import requests
import json
from datetime import datetime

# --- НАСТРОЙКИ ---
# Укажите адрес вашего запущенного API
BASE_URL = "http://127.0.0.1:8005"  # Или http://89.111.169.47:8005, если тестируете на сервере

# --- Глобальное состояние теста ---
test_state = {
    "token": None,
    "headers": {},
    "project_type_id": None,
    "task_type_id": None,
}


def print_status(ok, message):
    """Выводит красивый статус операции."""
    if ok:
        print(f"✅ [SUCCESS] {message}")
    else:
        print(f"❌ [FAILURE] {message}")
        # Завершаем скрипт при первой же ошибке
        exit(1)


def main():
    """Основная функция для запуска тестов."""
    print("--- ЗАПУСК ТЕСТИРОВАНИЯ META API ---")

    # --- Шаг 1: Регистрация и Вход ---
    print("\n--- Шаг 1: Регистрация и Авторизация ---")
    # Генерируем уникальные данные для каждого запуска теста
    unique_email = f"testuser_{int(datetime.now().timestamp())}@test.com"
    password = "superstrongpassword123"

    try:
        # Регистрация
        reg_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": unique_email, "password": password, "full_name": "Meta Tester"}
        )
        assert reg_response.status_code == 201
        print_status(True, f"Пользователь {unique_email} успешно зарегистрирован.")

        # Вход
        login_response = requests.post(
            f"{BASE_URL}/api/auth/token",
            data={"username": unique_email, "password": password}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        test_state["token"] = token
        test_state["headers"] = {"Authorization": f"Bearer {token}"}
        print_status(True, "Успешно получен JWT токен.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка на шаге авторизации: {e}")
        return

    # --- Шаг 2: Создание Типов Сущностей ---
    print("\n--- Шаг 2: Создание новых 'таблиц' (Entity Types) ---")
    try:
        # Создаем "Проекты"
        project_payload = {"name": "projects", "display_name": "Проекты"}
        response = requests.post(
            f"{BASE_URL}/api/meta/entity-types",
            headers=test_state["headers"],
            json=project_payload
        )
        assert response.status_code == 201
        project_data = response.json()
        test_state["project_type_id"] = project_data["id"]
        print_status(True, f"Создан тип 'Проекты' с ID: {test_state['project_type_id']}")

        # Создаем "Задачи"
        task_payload = {"name": "tasks", "display_name": "Задачи"}
        response = requests.post(
            f"{BASE_URL}/api/meta/entity-types",
            headers=test_state["headers"],
            json=task_payload
        )
        assert response.status_code == 201
        task_data = response.json()
        test_state["task_type_id"] = task_data["id"]
        print_status(True, f"Создан тип 'Задачи' с ID: {test_state['task_type_id']}")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при создании типов сущностей: {e}")

    # --- Шаг 3: Получение списка всех Типов Сущностей ---
    print("\n--- Шаг 3: Проверка получения списка 'таблиц' (GET /api/meta/entity-types) ---")
    try:
        response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=test_state["headers"])
        assert response.status_code == 200
        all_types = response.json()

        # Проверки
        assert isinstance(all_types, list)
        # ВАЖНО: Тест предполагает, что у нового пользователя еще нет других таблиц
        assert len(all_types) == 2

        type_names = {t['name'] for t in all_types}
        assert "projects" in type_names and "tasks" in type_names

        print_status(True, "Список всех типов сущностей получен и содержит созданные нами 'таблицы'.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при получении списка: {e}")

    # --- Шаг 4: Получение одного Типа Сущности по ID ---
    print("\n--- Шаг 4: Проверка получения одной 'таблицы' по ID (GET /api/meta/entity-types/{id}) ---")
    try:
        project_id = test_state["project_type_id"]
        response = requests.get(f"{BASE_URL}/api/meta/entity-types/{project_id}", headers=test_state["headers"])

        assert response.status_code == 200
        project_details = response.json()

        # Проверки
        assert project_details["id"] == project_id
        assert project_details["name"] == "projects"
        assert project_details["display_name"] == "Проекты"

        # Проверяем, что системные атрибуты были автоматически созданы
        assert isinstance(project_details["attributes"], list)
        assert len(project_details["attributes"]) > 0
        attribute_names = {attr['name'] for attr in project_details['attributes']}
        assert "phone_number" in attribute_names
        assert "sms_status" in attribute_names

        print_status(True, "Детальная информация о типе 'Проекты' получена корректно.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при получении одного типа: {e}")

    # --- Шаг 5: Проверка обработки несуществующего ID ---
    print("\n--- Шаг 5: Проверка получения несуществующей 'таблицы' (ожидаем 404) ---")
    try:
        non_existent_id = 999999
        response = requests.get(f"{BASE_URL}/api/meta/entity-types/{non_existent_id}", headers=test_state["headers"])
        assert response.status_code == 404

        print_status(True, f"Сервер корректно вернул ошибку 404 для несуществующего ID {non_existent_id}.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при проверке несуществующего ID: {e}")

    print("\n🎉 Все тесты для Meta API успешно пройдены!")


if __name__ == "__main__":
    main()