import requests
import json
import time

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"


# -----------------
def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}"); exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

# --- Вспомогательные функции ---
# ... (вставьте сюда `print_status`, `print_header`, `register_and_login`)

def run_time_filter_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
        headers = register_and_login()

        table_name = f"meetings_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Встречи (time тест)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        attributes = [
            {"name": "topic", "display_name": "Тема встречи", "value_type": "string"},
            {"name": "start_time", "display_name": "Время начала", "value_type": "time"},
        ]
        for attr in attributes:
            requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                          json=attr).raise_for_status()

        # --- ШАГ 2: НАПОЛНЕНИЕ ДАННЫМИ ---
        print_header("ШАГ 2: НАПОЛНЕНИЕ ТАБЛИЦЫ ДАННЫМИ О ВСТРЕЧАХ")

        test_data = [
            {"topic": "Утренний планер", "start_time": "09:00:00"},
            {"topic": "Синхронизация с отделом продаж", "start_time": "11:30:00"},
            {"topic": "Обед", "start_time": "14:00:00"},
            {"topic": "Встреча с клиентом", "start_time": "15:00:00"},
            {"topic": "Вечерний отчет", "start_time": "18:00:00"},
        ]
        for item in test_data:
            requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=item).raise_for_status()

        print_status(True, "5 тестовых записей успешно созданы.")

        # --- ШАГ 3: ТЕСТИРОВАНИЕ ФИЛЬТРОВ ---
        print_header("ШАГ 3: ТЕСТЫ ФИЛЬТРАЦИИ ПО ВРЕМЕНИ")

        # Тест 1: Точное совпадение
        print("\n -> Тест 1: Найти встречу ровно в 14:00 (ожидается 1)")
        filters1 = [{"field": "start_time", "op": "is", "value": "14:00:00"}]
        resp1 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters1)}).json()
        print_status(len(resp1) == 1 and resp1[0]['topic'] == "Обед", f"Найдено {len(resp1)} записей.")

        # Тест 2: После
        print("\n -> Тест 2: Найти все встречи после 12:00 (ожидается 3)")
        filters2 = [{"field": "start_time", "op": "is_after", "value": "12:00:00"}]
        resp2 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters2)}).json()
        print_status(len(resp2) == 3, f"Найдено {len(resp2)} записей.")

        # Тест 3: Включительно или до
        print("\n -> Тест 3: Найти все встречи в 15:00 или раньше (ожидается 4)")
        filters3 = [{"field": "start_time", "op": "is_on_or_before", "value": "15:00:00"}]
        resp3 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters3)}).json()
        print_status(len(resp3) == 4, f"Найдено {len(resp3)} записей.")

        # Тест 4: Диапазон
        print("\n -> Тест 4: Найти встречи между 10:00 и 15:00 (ожидается 3)")
        filters4 = [{"field": "start_time", "op": "is_within", "value": ["10:00:00", "15:00:00"]}]
        resp4 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters4)}).json()
        print_status(len(resp4) == 3, f"Найдено {len(resp4)} записей.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ ФИЛЬТРАЦИИ ПО ВРЕМЕНИ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА В СКРИПТЕ: {e}")

def register_and_login():
    unique_id = int(time.time())
    email = f"bool_tester_{unique_id}@example.com"
    password = "password123"
    reg_payload = {"email": email, "password": password, "full_name": "Boolean Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}

if __name__ == "__main__":
    run_time_filter_test()