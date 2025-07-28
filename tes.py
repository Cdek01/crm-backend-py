import requests
import json
import time

# --- Настройте эти переменные ---
BASE_URL = "http://89.111.169.47:8005"
# Генерируем уникальные данные для нового пользователя
UNIQUE_ID = int(time.time())
USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
USER_PASSWORD = "a_very_secure_password"
# ---------------------------------

try:
    # --- ШАГ 1: РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ---
    print(f"Регистрация нового пользователя: {USER_EMAIL}...")
    register_payload = {
        "email": USER_EMAIL,
        "password": USER_PASSWORD
        # Добавьте другие поля, если они требуются для регистрации (например, full_name)
    }

    # Предполагаем, что у вас есть эндпоинт /api/auth/register
    # Если он другой - измените URL
    register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)

    # Проверяем, что регистрация прошла успешно (обычно код 201 Created)
    if register_response.status_code == 201:
        print("Пользователь успешно зарегистрирован!")
    elif register_response.status_code == 400 and "уже существует" in register_response.text:
        # Эта проверка на случай, если вы запустите скрипт дважды в одну секунду
        print("Пользователь с таким email уже существует, продолжаем...")
    else:
        # Если регистрация не удалась по другой причине, вызываем ошибку
        register_response.raise_for_status()

    # --- ШАГ 2: ПОЛУЧЕНИЕ ТОКЕНА (ВХОД) ---
    print("\nПолучение токена...")
    auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}

    auth_response = requests.post(
        f"{BASE_URL}/api/auth/token",
        data=auth_payload_form
    )
    auth_response.raise_for_status()
    token = auth_response.json()['access_token']
    print("Токен успешно получен!")

    # --- ШАГ 3: ЗАПРОС НА ПОЛУЧЕНИЕ ЛИДОВ ---
    print("\nПолучение 100 лидов...")
    headers = {'Authorization': f'Bearer {token}'}
    params = {'skip': 0, 'limit': 100}

    leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers, params=params)
    leads_response.raise_for_status()

    leads_data = leads_response.json()

    print(f"Успешно получено {len(leads_data)} лидов.")
    if leads_data:
        print("\nПример первого лида:")
        print(json.dumps(leads_data[0], indent=2, ensure_ascii=False))
    else:
        print("Список лидов пуст.")

except requests.exceptions.HTTPError as e:
    print(f"\n--- Ошибка HTTP ---")
    print(f"Статус код: {e.response.status_code}")
    print(f"Ответ сервера: {e.response.text}")
except requests.exceptions.RequestException as e:
    print(f"\n--- Ошибка подключения ---")
    print(f"Не удалось выполнить запрос: {e}")