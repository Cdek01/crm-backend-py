import requests
import time
import json
from datetime import date, timedelta

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




def run_events_test():
    print(">>> НАЧАЛО ТЕСТИРОВАНИЯ API ПОЛУЧЕНИЯ СОБЫТИЙ КАЛЕНДАРЯ <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}

    # --- ШАГ 1: Настройка ---
    print("\n--- [ШАГ 1] Создание тестовой таблицы, полей и конфигурации ---")
    table_id, attr_ids = setup_test_environment(headers)
    if not table_id: return

    config_payload = {
        "name": "Тестовый календарь событий",
        "entity_type_id": table_id,
        "title_attribute_id": attr_ids["title"],
        "start_date_attribute_id": attr_ids["start_date"],
        "color_attribute_id": attr_ids["status"],
        "color_settings": {"В работе": "#3498db", "Готово": "#2ecc71"}
    }
    config_resp = requests.post(f"{BASE_URL}/api/calendar-views/", headers=headers, json=config_payload)
    if not print_status("Создание конфигурации календаря", config_resp, 201): return
    view_id = config_resp.json()["id"]

    # --- ШАГ 2: Создание тестовых данных ---
    print("\n--- [ШАГ 2] Создание тестовых событий в EAV-таблице ---")
    today = date.today()
    # Событие внутри диапазона
    requests.post(f"{BASE_URL}/api/data/cal_events_{table_id}", headers=headers,
                  json={"task_title": "Событие 1 (В работе)", "start_date": today.isoformat(), "status": "В работе"})
    # Событие вне диапазона (в прошлом)
    requests.post(f"{BASE_URL}/api/data/cal_events_{table_id}", headers=headers,
                  json={"task_title": "Событие 2 (в прошлом)", "start_date": (today - timedelta(days=40)).isoformat(),
                        "status": "Готово"})
    # Событие внутри диапазона (Готово)
    requests.post(f"{BASE_URL}/api/data/cal_events_{table_id}", headers=headers,
                  json={"task_title": "Событие 3 (Готово)", "start_date": (today + timedelta(days=5)).isoformat(),
                        "status": "Готово"})
    print("    Создано 3 тестовых события.")

    # --- ШАГ 3: Проверка получения событий ---
    print("\n--- [ШАГ 3] Проверка эндпоинта получения событий ---")
    start_range = (today - timedelta(days=10)).isoformat()
    end_range = (today + timedelta(days=10)).isoformat()

    events_resp = requests.get(f"{BASE_URL}/api/calendar/events/{view_id}?start={start_range}&end={end_range}",
                               headers=headers)
    if print_status("Запрос событий для календаря", events_resp, 200):
        events = events_resp.json()
        if len(events) == 2:
            print(f"    [OK] Получено правильное количество событий: {len(events)} (ожидалось 2).")
        else:
            print(f"    [FAIL] Получено неправильное количество событий: {len(events)} (ожидалось 2).")

        # Проверяем, что данные отформатированы правильно
        event1 = next((e for e in events if e["title"] == "Событие 1 (В работе)"), None)
        if event1 and event1["color"] == "#3498db":
            print("    [OK] Событие 1 отформатировано правильно (цвет #3498db).")
        else:
            print("    [FAIL] Ошибка в форматировании События 1.")

    # --- ШАГ 4: Очистка ---
    print("\n--- [ШАГ 4] Очистка ---")
    requests.delete(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers)
    print("    Тестовая таблица удалена.")

    print("\n>>> ТЕСТИРОВАНИЕ ЗАВЕРШЕНО <<<")


def setup_test_environment(headers):
    """Вспомогательная функция для создания EAV-таблицы и атрибутов."""
    table_name = f"cal_events_{int(time.time())}"
    table_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                               json={"name": table_name, "display_name": "События для теста"})
    if not table_resp.ok: return None, None
    table_id = table_resp.json()["id"]

    attrs = {
        "title": {"name": "task_title", "display_name": "Название", "value_type": "string"},
        "start_date": {"name": "start_date", "display_name": "Дата начала", "value_type": "date"},
        "status": {"name": "status", "display_name": "Статус", "value_type": "string"},
    }
    attr_ids = {}
    for key, payload in attrs.items():
        attr_resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                                  json=payload)
        if not attr_resp.ok: return None, None
        attr_ids[key] = attr_resp.json()["id"]

    # Меняем имя таблицы, чтобы соответствовать тому, как EAVService создает URL
    return table_id, attr_ids


if __name__ == "__main__":
    run_events_test()