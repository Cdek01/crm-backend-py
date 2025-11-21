import requests
import json
import time
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"


def login(email, password):
    """Логинится в систему и возвращает JWT токен."""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        print("[OK] Успешный вход в систему")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Ошибка входа для {email}: {e.response.text if e.response else e}")
        return None


def print_status(message, is_ok, details=""):
    """Удобно выводит результат проверки в консоль."""
    status_char = "[OK]" if is_ok else "[FAIL]"
    print(f"{status_char} {message} {details}")
    if not is_ok:
        raise AssertionError(f"Test failed: {message}")
    return True


def run_undo_redo_test():
    """
    Тестирует полный цикл Undo/Redo для операций CREATE, UPDATE, DELETE.
    """
    print(">>> Тест: Проверка функциональности Отмены и Повтора действий (Undo/Redo) <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    test_table_id = None

    try:
        # --- [ШАГ 0] Подготовка: Создание временной таблицы для тестов ---
        print("\n--- [ШАГ 0] Подготовка: Создание временной таблицы ---")
        table_name = f"undo_test_table_{int(time.time())}"
        resp_create_table = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json={
            "name": table_name,
            "display_name": "Тестовая таблица для Undo/Redo"
        })
        print_status("Создание таблицы", resp_create_table.ok, f"| Статус: {resp_create_table.status_code}")
        test_table_id = resp_create_table.json()['id']

        # Добавляем колонки
        requests.post(f"{BASE_URL}/api/meta/entity-types/{test_table_id}/attributes", headers=headers,
                      json={"name": "name", "display_name": "Name", "value_type": "string"})
        requests.post(f"{BASE_URL}/api/meta/entity-types/{test_table_id}/attributes", headers=headers,
                      json={"name": "value", "display_name": "Value", "value_type": "integer"})
        print("    [INFO] Тестовая таблица и колонки созданы.")

        # --- [ШАГ 1] Тестирование CREATE ---
        print("\n--- [ШАГ 1] Тестирование UNDO/REDO для операции CREATE ---")

        # 1.1. Создаем запись
        print("    [ACTION] Создание новой записи...")
        resp_create = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                                    json={"name": "Initial Name", "value": 100})
        created_entity_id = resp_create.json()['data'][0]['id']
        print_status("Запрос на создание записи", resp_create.status_code == 201)

        # 1.2. Проверяем, что запись появилась
        resp_get = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
        print_status("Проверка: запись существует в базе", len(resp_get.json()['data']) == 1)

        # 1.3. Отменяем создание
        print("    [ACTION] Отмена создания (Undo)...")
        resp_undo = requests.post(f"{BASE_URL}/api/history/undo", headers=headers)
        print_status("Запрос на отмену", resp_undo.ok)

        # 1.4. Проверяем, что запись исчезла
        resp_get_after_undo = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
        print_status("Проверка: запись удалена после отмены", len(resp_get_after_undo.json()['data']) == 0)

        # 1.5. Повторяем создание
        print("    [ACTION] Повтор создания (Redo)...")
        resp_redo = requests.post(f"{BASE_URL}/api/history/redo", headers=headers)
        print_status("Запрос на повтор", resp_redo.ok)

        # 1.6. Проверяем, что запись снова появилась
        resp_get_after_redo = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
        print_status("Проверка: запись восстановлена после повтора", len(resp_get_after_redo.json()['data']) == 1)

        # --- [ШАГ 2] Тестирование UPDATE ---
        print("\n--- [ШАГ 2] Тестирование UNDO/REDO для операции UPDATE ---")

        # 2.1. Обновляем запись
        print("    [ACTION] Обновление записи (value: 100 -> 250)...")
        resp_update = requests.put(f"{BASE_URL}/api/data/{table_name}/{created_entity_id}", headers=headers,
                                   json={"value": 250})
        print_status("Запрос на обновление", resp_update.ok)
        print_status("Проверка: значение обновлено", resp_update.json()['value'] == 250)

        # 2.2. Отменяем обновление
        print("    [ACTION] Отмена обновления (Undo)...")
        resp_undo_update = requests.post(f"{BASE_URL}/api/history/undo", headers=headers)
        print_status("Запрос на отмену", resp_undo_update.ok)

        # 2.3. Проверяем, что значение вернулось к исходному
        resp_get_after_undo = requests.get(f"{BASE_URL}/api/data/{table_name}/{created_entity_id}", headers=headers)
        print_status("Проверка: значение вернулось к исходному (100)", resp_get_after_undo.json()['value'] == 100)

        # 2.4. Повторяем обновление
        print("    [ACTION] Повтор обновления (Redo)...")
        resp_redo_update = requests.post(f"{BASE_URL}/api/history/redo", headers=headers)
        print_status("Запрос на повтор", resp_redo_update.ok)

        # 2.5. Проверяем, что значение снова обновлено
        resp_get_after_redo = requests.get(f"{BASE_URL}/api/data/{table_name}/{created_entity_id}", headers=headers)
        print_status("Проверка: значение снова обновлено (250)", resp_get_after_redo.json()['value'] == 250)

        # --- [ШАГ 3] Тестирование DELETE ---
        print("\n--- [ШАГ 3] Тестирование UNDO/REDO для операции DELETE ---")

        # 3.1. Удаляем запись
        print("    [ACTION] Удаление записи...")
        resp_delete = requests.delete(f"{BASE_URL}/api/data/{table_name}/{created_entity_id}", headers=headers)
        print_status("Запрос на удаление", resp_delete.status_code == 204)

        # 3.2. Проверяем, что запись удалена
        resp_get_after_delete = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
        print_status("Проверка: запись удалена из базы", len(resp_get_after_delete.json()['data']) == 0)

        # 3.3. Отменяем удаление
        print("    [ACTION] Отмена удаления (Undo)...")
        resp_undo_delete = requests.post(f"{BASE_URL}/api/history/undo", headers=headers)
        print_status("Запрос на отмену", resp_undo_delete.ok)

        # 3.4. Проверяем, что запись восстановлена
        resp_get_after_undo = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
        print_status("Проверка: запись восстановлена после отмены", len(resp_get_after_undo.json()['data']) == 1)

        # 3.5. Повторяем удаление
        print("    [ACTION] Повтор удаления (Redo)...")
        resp_redo_delete = requests.post(f"{BASE_URL}/api/history/redo", headers=headers)
        print_status("Запрос на повтор", resp_redo_delete.ok)

        # 3.6. Проверяем, что запись снова удалена
        resp_get_after_redo = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
        print_status("Проверка: запись снова удалена после повтора", len(resp_get_after_redo.json()['data']) == 0)

    except AssertionError as e:
        print(f"\n[CRITICAL] Тест провален: {e}")
    except Exception as e:
        print(f"\n[CRITICAL] В ходе теста произошла непредвиденная ошибка: {e}")
    finally:
        # --- [ШАГ 4] Очистка: Удаление временной таблицы ---
        if test_table_id:
            print("\n--- [ШАГ 4] Очистка: Удаление временной таблицы ---")
            resp_cleanup = requests.delete(f"{BASE_URL}/api/meta/entity-types/{test_table_id}", headers=headers)
            if resp_cleanup.ok:
                print("[OK] Временная таблица успешно удалена.")
            else:
                print("[FAIL] Не удалось удалить временную таблицу.")

    print("\n>>> ТЕСТ UNDO/REDO ЗАВЕРШЕН <<<")


if __name__ == "__main__":
    run_undo_redo_test()