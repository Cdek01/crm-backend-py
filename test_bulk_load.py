# test_bulk_load.py
import requests
import time
import json

# --- НАСТРОЙКИ ---
# BASE_URL = "http://127.0.0.1:8005"
BASE_URL = "http://89.111.169.47:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"  # Укажите ваш токен
# -----------------

UNIQUE_ID = int(time.time())


def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}"); exit(1)


def run_test():
    # --- Шаг 1: Регистрация и вход ---
    print("--- 1. Авторизация ---")
    user_email = f"bulk_loader_{UNIQUE_ID}@example.com"
    password = "password123"
    reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()

    auth_payload = {"username": user_email, "password": password}
    token_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
    token_response.raise_for_status()
    token = token_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print_status(True, "Пользователь успешно авторизован.")

    # --- Шаг 2: Подготовка и отправка данных для массовой загрузки ---
    print("\n--- 2. Массовая загрузка лидов ---")
    leads_to_load = [
        {"organization_name": f"Bulk Company A {UNIQUE_ID}", "rating": 5},
        {"organization_name": f"Bulk Company B {UNIQUE_ID}", "rating": 4, "lead_status": "In Progress"},
        {"organization_name": f"Bulk Company C {UNIQUE_ID}", "rating": 3, "source": "Import"},
    ]

    print(f"Отправка {len(leads_to_load)} записей на /api/leads/bulk-load...")
    bulk_response = requests.post(f"{BASE_URL}/api/leads/bulk-load", headers=headers, json=leads_to_load)

    print(f"Сервер ответил со статусом: {bulk_response.status_code}")
    print(f"Тело ответа: {bulk_response.text}")

    bulk_response.raise_for_status()
    created_count = bulk_response.json().get("created_count")

    print_status(
        created_count == len(leads_to_load),
        f"Сервер корректно вернул количество созданных записей: {created_count}"
    )

    # --- Шаг 3: Проверка результата ---
    print("\n--- 3. Проверка результата ---")
    list_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
    list_response.raise_for_status()
    total_leads_in_db = len(list_response.json())

    print(f"Всего лидов в базе данных для этого пользователя: {total_leads_in_db}")
    print_status(
        total_leads_in_db == len(leads_to_load),
        "Количество записей в БД совпадает с количеством загруженных."
    )

    print("\n🎉 Все тесты для массовой загрузки пройдены успешно!")


if __name__ == "__main__":
    run_test()