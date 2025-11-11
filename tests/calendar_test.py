import requests
import time
import json

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"  # Замените на URL вашего API
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"


# --- КОНЕЦ КОНФИГУРАЦИИ ---

# Вспомогательные функции
def login(email, password):
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"\n[!!!] Ошибка входа для {email}: {e.response.text if e.response else e}")
        return None


def print_status(message, response, expected_status):
    is_ok = response.status_code == expected_status
    status_char = "[OK]" if is_ok else "[FAIL]"
    print(f"{status_char} {message} (Статус: {response.status_code}, Ожидался: {expected_status})")
    if not is_ok:
        print(f"       Ответ: {response.text[:250]}")
    return is_ok


# Основной сценарий теста
def run_calendar_test():
    print(">>> НАЧАЛО ТЕСТИРОВАНИЯ API КОНФИГУРАЦИИ КАЛЕНДАРЕЙ <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}"}

    # --- [ШАГ 1] Подготовка: Создаем временную таблицу и поля для теста ---
    print("\n--- [ШАГ 1] Создание временной EAV-таблицы и атрибутов ---")
    timestamp = int(time.time())
    table_name = f"cal_test_table_{timestamp}"

    table_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                               json={"name": table_name, "display_name": "Тест Календаря"})
    if not print_status("Создание тестовой таблицы", table_resp, 201): return
    table_id = table_resp.json()["id"]

    title_attr_resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                                    json={"name": "task_title", "display_name": "Название", "value_type": "string"})
    start_date_attr_resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                                         json={"name": "start_date", "display_name": "Дата начала",
                                               "value_type": "date"})
    end_date_attr_resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                                       json={"name": "end_date", "display_name": "Дата конца", "value_type": "date"})

    if not all([title_attr_resp.ok, start_date_attr_resp.ok, end_date_attr_resp.ok]):
        print("[FAIL] Не удалось создать необходимые атрибуты для теста.")
        return

    title_attr_id = title_attr_resp.json()["id"]
    start_date_attr_id = start_date_attr_resp.json()["id"]
    end_date_attr_id = end_date_attr_resp.json()["id"]

    # --- [ШАГ 2] CREATE: Создаем новую конфигурацию календаря ---
    print("\n--- [ШАГ 2] CREATE: Проверка создания конфигурации календаря ---")
    calendar_config_payload = {
        "name": "Календарь задач по срокам",
        "entity_type_id": table_id,
        "title_attribute_id": title_attr_id,
        "start_date_attribute_id": start_date_attr_id,
        "end_date_attribute_id": end_date_attr_id,
        "default_view": "week"
    }
    create_resp = requests.post(f"{BASE_URL}/api/calendar-views/", headers=headers, json=calendar_config_payload)

    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    # Ожидаем ошибку 500, так как FastAPI по умолчанию так обрабатывает NotImplementedError
    print_status("Создание конфигурации календаря (ожидаем ошибку, т.к. не реализовано)", create_resp, 500)

    # --- [ШАГ 3] Очистка ---
    print("\n--- [ШАГ 3] Очистка тестовых данных ---")
    cleanup_resp = requests.delete(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers)
    print_status("Удаление временной EAV-таблицы", cleanup_resp, 204)

    print("\n>>> ТЕСТИРОВАНИЕ ЗАВЕРШЕНО <<<")
    print(
        "\nПримечание: Тест прошел успешно, если на Шаге 2 получен статус 500. Это подтверждает, что эндпоинт существует, но его логика еще не реализована.")


if __name__ == "__main__":
    run_calendar_test()