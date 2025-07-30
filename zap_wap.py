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

    timestamp = int(datetime.now().timestamp())
    unique_email = f"testuser_{timestamp}@test.com"

    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    # Сделаем full_name тоже уникальным для каждого запуска теста
    unique_full_name = f"Meta Tester {timestamp}"

    password = "superstrongpassword123"

    try:
        # Регистрация
        reg_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            # Используем нашу новую уникальную переменную
            json={"email": unique_email, "password": password, "full_name": unique_full_name}
        )
        assert reg_response.status_code == 201
        print_status(True, f"Пользователь {unique_email} ({unique_full_name}) успешно зарегистрирован.")

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
        project_payload = {"name": "pro", "display_name": "Про"}
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
        task_payload = {"name": "tas", "display_name": "Зад"}
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
        assert "pro" in type_names and "tas" in type_names

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
        assert project_details["name"] == "pro"
        assert project_details["display_name"] == "Про"

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

    # --- Шаг 6: Удаление одного из типов сущностей ---
    print("\n--- Шаг 6: Проверка удаления 'таблицы' (DELETE /api/meta/entity-types/{id}) ---")
    try:
        # Будем удалять 'Задачи'
        task_id_to_delete = test_state["task_type_id"]
        response = requests.delete(
            f"{BASE_URL}/api/meta/entity-types/{task_id_to_delete}",
            headers=test_state["headers"]
        )
        # Ожидаем успешный пустой ответ
        assert response.status_code == 204

        print_status(True, f"Сервер успешно обработал запрос на удаление типа с ID {task_id_to_delete}.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при удалении типа: {e}")

    # --- Шаг 7: Проверка последствий удаления ---
    print("\n--- Шаг 7: Проверка, что 'таблица' действительно удалена ---")
    try:
        # 7.1. Попытка получить удаленный тип по ID должна вернуть 404
        task_id_deleted = test_state["task_type_id"]
        response_get_deleted = requests.get(
            f"{BASE_URL}/api/meta/entity-types/{task_id_deleted}",
            headers=test_state["headers"]
        )
        assert response_get_deleted.status_code == 404
        print_status(True, "Повторный запрос удаленного ID корректно вернул 404.")

        # 7.2. В общем списке должен остаться только один тип
        response_list_after_delete = requests.get(
            f"{BASE_URL}/api/meta/entity-types",
            headers=test_state["headers"]
        )
        assert response_list_after_delete.status_code == 200
        list_after_delete = response_list_after_delete.json()
        assert len(list_after_delete) == 1
        assert list_after_delete[0]["name"] == "projects"
        print_status(True, "Общий список теперь содержит только одну оставшуюся 'таблицу'.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при проверке последствий удаления: {e}")

if __name__ == "__main__":
    main()