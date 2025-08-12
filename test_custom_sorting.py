import requests
import json
import time

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8005"
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


# ... (Вставьте сюда вашу функцию `register_and_login` из предыдущих скриптов)

def run_sorting_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ СТРУКТУРЫ")
        headers = register_and_login()

        table_name = f"candidates_sort_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Кандидаты (сортировка)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        attributes = [
            {"name": "full_name", "display_name": "ФИО", "value_type": "string"},
            {"name": "rating", "display_name": "Рейтинг", "value_type": "integer"},
            {"name": "interview_date", "display_name": "Дата собеседования", "value_type": "date"},
        ]
        for attr in attributes:
            requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                          json=attr).raise_for_status()

        print_status(True, f"Создана таблица '{table_name}' с необходимыми колонками.")

        # --- ШАГ 2: НАПОЛНЕНИЕ ДАННЫМИ (В ПЕРЕМЕШАННОМ ПОРЯДКЕ) ---
        print_header("ШАГ 2: НАПОЛНЕНИЕ ДАННЫМИ")

        data_to_create = [
            {"full_name": "Виктор", "rating": 5, "interview_date": "2025-08-10T12:00:00"},
            {"full_name": "Анна", "rating": 10, "interview_date": "2025-08-12T15:00:00"},
            {"full_name": "Борис", "rating": 8, "interview_date": "2025-08-11T10:00:00"},
        ]
        for item in data_to_create:
            requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=item).raise_for_status()

        print_status(True, "Тестовые данные успешно созданы.")

        # --- ШАГ 3: ТЕСТИРОВАНИЕ СОРТИРОВКИ ---
        print_header("ШАГ 3: ТЕСТЫ СОРТИРОВКИ")

        # Тест 1: Сортировка по числу (рейтингу) по убыванию
        print("\n -> Тест 1: sort_by=rating, sort_order=desc")
        params1 = {"sort_by": "rating", "sort_order": "desc"}
        response1 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params1)
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Проверяем статус ответа перед попыткой парсить JSON
        if response1.status_code != 200:
            print_status(False, f"Ошибка сервера (статус {response1.status_code}) при запросе сортировки: {response1.text}")
        response1.raise_for_status() # Это выбросит исключение, если статус 4xx/5xx
        # ------------------------
        data1 = response1.json()
        ratings_order = [item.get('rating') for item in data1]
        print(f"    Получен порядок рейтингов: {ratings_order}")
        print_status(ratings_order == [10, 8, 5], "Сортировка по рейтингу (desc) верна.")

        # Тест 2: Сортировка по строке (имени) по возрастанию
        print("\n -> Тест 2: sort_by=full_name, sort_order=asc")
        params2 = {"sort_by": "full_name", "sort_order": "asc"}
        response2 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params2)
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Проверяем статус ответа перед попыткой парсить JSON
        if response2.status_code != 200:
            print_status(False, f"Ошибка сервера (статус {response2.status_code}) при запросе сортировки: {response1.text}")
        response2.raise_for_status() # Это выбросит исключение, если статус 4xx/5xx
        # ------------------------
        data2 = response2.json()
        names_order = [item.get('full_name') for item in data2]
        print(f"    Получен порядок имен: {names_order}")
        print_status(names_order == ["Анна", "Борис", "Виктор"], "Сортировка по имени (asc) верна.")

        # Тест 3: Сортировка по дате по убыванию (сначала новые)
        print("\n -> Тест 3: sort_by=interview_date, sort_order=desc")
        params3 = {"sort_by": "interview_date", "sort_order": "desc"}
        response3 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params3)
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Проверяем статус ответа перед попыткой парсить JSON
        if response3.status_code != 200:
            print_status(False, f"Ошибка сервера (статус {response3.status_code}) при запросе сортировки: {response1.text}")
        response3.raise_for_status() # Это выбросит исключение, если статус 4xx/5xx
        # ------------------------
        data3 = response3.json()
        dates_order_names = [item.get('full_name') for item in data3]  # Проверяем по именам, т.к. их порядок уникален
        print(f"    Получен порядок кандидатов по дате: {dates_order_names}")
        print_status(dates_order_names == ["Анна", "Борис", "Виктор"], "Сортировка по дате (desc) верна.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ СОРТИРОВКИ ДАННЫХ В КАСТОМНЫХ ТАБЛИЦАХ ПРОЙДЕН! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP.")
        print(f"URL: {e.request.method} {e.request.url}")
        print(f"Статус: {e.response.status_code}")
        print(f"Ответ: {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


# (Вставьте сюда вашу функцию register_and_login)
def register_and_login():
    unique_id = int(time.time())
    email = f"sort_tester_{unique_id}@example.com"
    password = "password123"
    reg_payload = {"email": email, "password": password, "full_name": "Sort Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


if __name__ == "__main__":
    run_sorting_test()