import requests
import json
from datetime import datetime

# --- НАСТРОЙКИ ---
# Укажите адрес вашего запущенного API
BASE_URL = "http://127.0.0.1:8005"  # Или http://89.111.169.47:8005, если тестируете на сервере
# BASE_URL = "http://89.111.169.47:8005"  # Или http://89.111.169.47:8005, если тестируете на сервере

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


def test_delete_attribute_flow(base_url, headers):
    """
    Тестирует полный цикл удаления атрибута (колонки).
    """
    print("\n--- ЗАПУСК ТЕСТИРОВАНИЯ УДАЛЕНИЯ АТРИБУТА ---")

    # --- Шаг 1: Подготовка (создаем таблицу и колонки) ---
    print("\n--- Шаг 1: Подготовка среды ---")
    try:
        # Создаем таблицу "Кандидаты"
        response = requests.post(f"{base_url}/api/meta/entity-types", headers=headers,
                                 json={"name": "candidates", "display_name": "Кандидаты"})
        assert response.status_code == 201
        entity_type = response.json()
        entity_type_id = entity_type["id"]
        print_status(True, f"Создана таблица 'Кандидаты' с ID: {entity_type_id}")

        # Создаем колонку "Ожидаемая ЗП" (останется)
        response = requests.post(f"{base_url}/api/meta/entity-types/{entity_type_id}/attributes", headers=headers,
                                 json={"name": "expected_salary", "display_name": "Ожидаемая ЗП",
                                       "value_type": "integer"})
        assert response.status_code == 201
        salary_attr = response.json()
        print_status(True, "Создана колонка 'Ожидаемая ЗП'")

        # Создаем колонку "Статус" (будет удалена)
        response = requests.post(f"{base_url}/api/meta/entity-types/{entity_type_id}/attributes", headers=headers,
                                 json={"name": "status", "display_name": "Статус", "value_type": "string"})
        assert response.status_code == 201
        status_attr = response.json()
        status_attr_id = status_attr["id"]
        print_status(True, f"Создана колонка 'Статус' с ID: {status_attr_id}")

    except (requests.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка на шаге подготовки: {e}")
        return

    # --- Шаг 2: Наполнение данными ---
    print("\n--- Шаг 2: Наполнение таблицы данными ---")
    entity1_id, entity2_id = None, None
    try:
        # Создаем первую строку
        payload1 = {"expected_salary": 150000, "status": "В работе"}
        response = requests.post(f"{base_url}/api/data/candidates", headers=headers, json=payload1)
        assert response.status_code == 201
        entity1_id = response.json()['id']
        print_status(True, "Создана первая строка с данными.")

        # Создаем вторую строку
        payload2 = {"expected_salary": 200000, "status": "Отказ"}
        response = requests.post(f"{base_url}/api/data/candidates", headers=headers, json=payload2)
        assert response.status_code == 201
        entity2_id = response.json()['id']
        print_status(True, "Создана вторая строка с данными.")

    except (requests.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка на шаге наполнения данными: {e}")
        return

    # --- Шаг 3: Удаление атрибута ---
    print("\n--- Шаг 3: Удаление колонки 'Статус' ---")
    try:
        response = requests.delete(f"{base_url}/api/meta/entity-types/{entity_type_id}/attributes/{status_attr_id}",
                                   headers=headers)
        assert response.status_code == 204
        print_status(True, "Сервер успешно обработал запрос на удаление колонки 'Статус'.")

    except (requests.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при удалении колонки: {e}")
        return

    # --- Шаг 4: Проверка последствий ---
    print("\n--- Шаг 4: Проверка последствий удаления ---")
    try:
        # Проверяем структуру таблицы - колонки "Статус" быть не должно
        response = requests.get(f"{base_url}/api/meta/entity-types/{entity_type_id}", headers=headers)
        assert response.status_code == 200
        updated_entity_type = response.json()
        attribute_names = {attr['name'] for attr in updated_entity_type['attributes']}
        assert 'status' not in attribute_names
        assert 'expected_salary' in attribute_names
        print_status(True, "Колонка 'Статус' отсутствует в структуре таблицы.")

        # Проверяем данные в строке - поля "status" быть не должно
        response = requests.get(f"{base_url}/api/data/candidates/{entity1_id}", headers=headers)
        assert response.status_code == 200
        entity_data = response.json()
        assert 'status' not in entity_data
        assert 'expected_salary' in entity_data
        assert entity_data['expected_salary'] == 150000
        print_status(True, "Поле 'status' отсутствует в данных строки (каскадное удаление сработало).")

    except (requests.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка на шаге проверки последствий: {e}")
        return

    # --- Шаг 5: Проверка защиты от удаления системных атрибутов ---
    print("\n--- Шаг 5: Проверка защиты от удаления системной колонки ---")
    try:
        # Получаем ID системного атрибута 'sms_status'
        sms_status_attr_id = next(
            (attr['id'] for attr in updated_entity_type['attributes'] if attr['name'] == 'sms_status'), None)
        assert sms_status_attr_id is not None

        response = requests.delete(f"{base_url}/api/meta/entity-types/{entity_type_id}/attributes/{sms_status_attr_id}",
                                   headers=headers)
        # Ожидаем ошибку клиента, а не сервера
        assert response.status_code == 400
        print_status(True, "Сервер корректно вернул ошибку 400 при попытке удалить системную колонку.")

    except (requests.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при проверке защиты системных колонок: {e}")
        return

    print("\n🎉 Все тесты для удаления атрибутов успешно пройдены!")


def main():
    """Основная функция для запуска тестов."""
    print("--- ЗАПУСК ТЕСТИРОВАНИЯ META API ---")

    # --- Шаг 1: Регистрация и Вход ---
    print("\n--- Шаг 1: Регистрация и Авторизация ---")
    import time

    # Используем уникальные данные для каждого запуска
    UNIQUE_ID = int(time.time())
    USER_EMAIL = f"meta_tester_{UNIQUE_ID}@example.com"
    USER_PASSWORD = "a_very_secure_password_123!"
    CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
    try:
        # Регистрация
        register_payload = {
            "email": USER_EMAIL,
            "password": USER_PASSWORD,
            "full_name": f"Meta Tester {UNIQUE_ID}",
            "registration_token": CORRECT_REGISTRATION_TOKEN
        }
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
        # Проверяем, что регистрация прошла успешно
        assert reg_response.status_code == 201, f"Ошибка регистрации: {reg_response.text}"

        # Вход
        auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
        auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
        assert auth_response.status_code == 200, f"Ошибка входа: {auth_response.text}"

        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Сохраняем токен и заголовки в ГЛОБАЛЬНЫЙ test_state
        token = auth_response.json()["access_token"]
        test_state["token"] = token
        test_state["headers"] = {"Authorization": f"Bearer {token}"}
        # -------------------------

        print_status(True, "Успешно зарегистрирован и получен токен.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка на шаге авторизации: {e}")
        return  # Выходим, если не удалось авторизоваться

    # --- Шаг 2: Создание Типов Сущностей ---
    print("\n--- Шаг 2: Создание новых 'таблиц' (Entity Types) ---")
    try:
        # Теперь test_state["headers"] содержит правильный токен
        headers = test_state["headers"]

        # Создаем "Проекты"
        project_payload = {"name": f"projects_{UNIQUE_ID}", "display_name": f"Проекты {UNIQUE_ID}"}
        response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=project_payload)
        assert response.status_code == 201, f"Ошибка создания 'Проектов': {response.text}"
        project_data = response.json()
        test_state["project_type_id"] = project_data["id"]
        print_status(True, f"Создан тип 'Проекты' с ID: {test_state['project_type_id']}")

        # Создаем "Задачи"
        task_payload = {"name": f"tasks_{UNIQUE_ID}", "display_name": f"Задачи {UNIQUE_ID}"}
        response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=task_payload)
        assert response.status_code == 201, f"Ошибка создания 'Задач': {response.text}"
        task_data = response.json()
        test_state["task_type_id"] = task_data["id"]
        print_status(True, f"Создан тип 'Задачи' с ID: {test_state['task_type_id']}")

    except (requests.exceptions.RequestException, AssertionError) as e:
        # Добавим вывод текста ошибки для лучшей диагностики
        print_status(False, f"Ошибка при создании типов сущностей: {e}")
        return

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
        assert "prottoooeqqr" in type_names and "tasttoooeqqr" in type_names

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
        assert project_details["name"] == "prottoooeqqr"
        assert project_details["display_name"] == "Проttoooeqqr"

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
        # ... (код для проверки 404 ошибки остается без изменений) ...

        # 7.2. В общем списке должен остаться только один тип
        response_list_after_delete = requests.get(
            f"{BASE_URL}/api/meta/entity-types",
            headers=test_state["headers"]
        )
        assert response_list_after_delete.status_code == 200
        list_after_delete = response_list_after_delete.json()
        assert len(list_after_delete) == 1
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Проверяем, что имя оставшейся таблицы - 'prott', как мы и создавали
        assert list_after_delete[0]["name"] == "prottoooeqqr"
        print_status(True, "Общий список теперь содержит только одну оставшуюся 'таблицу'.")

    except (requests.exceptions.RequestException, AssertionError) as e:
        print_status(False, f"Ошибка при проверке последствий удаления: {e}")


    """Основная функция для запуска тестов."""
    # ... (код для авторизации и первых тестов) ...
    # Предполагаем, что test_state["headers"] уже заполнен

    # Вызываем новый набор тестов
    test_delete_attribute_flow(BASE_URL, test_state["headers"])

print("\n🎉 Все тесты успешно пройдены!")

if __name__ == "__main__":
    main()