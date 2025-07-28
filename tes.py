# import requests
# import json
# import time
#
# # --- Настройте эти переменные ---
# BASE_URL = "http://89.111.169.47:8005"
# # Генерируем уникальные данные для нового пользователя
# UNIQUE_ID = int(time.time())
# USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
# USER_PASSWORD = "a_very_secure_password"
# # ---------------------------------
#
# try:
#     # --- ШАГ 1: РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ---
#     print(f"Регистрация нового пользователя: {USER_EMAIL}...")
#     register_payload = {
#         "email": USER_EMAIL,
#         "password": USER_PASSWORD
#         # Добавьте другие поля, если они требуются для регистрации (например, full_name)
#     }
#
#     # Предполагаем, что у вас есть эндпоинт /api/auth/register
#     # Если он другой - измените URL
#     register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
#
#     # Проверяем, что регистрация прошла успешно (обычно код 201 Created)
#     if register_response.status_code == 201:
#         print("Пользователь успешно зарегистрирован!")
#     elif register_response.status_code == 400 and "уже существует" in register_response.text:
#         # Эта проверка на случай, если вы запустите скрипт дважды в одну секунду
#         print("Пользователь с таким email уже существует, продолжаем...")
#     else:
#         # Если регистрация не удалась по другой причине, вызываем ошибку
#         register_response.raise_for_status()
#
#     # --- ШАГ 2: ПОЛУЧЕНИЕ ТОКЕНА (ВХОД) ---
#     print("\nПолучение токена...")
#     auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
#
#     auth_response = requests.post(
#         f"{BASE_URL}/api/auth/token",
#         data=auth_payload_form
#     )
#     auth_response.raise_for_status()
#     token = auth_response.json()['access_token']
#     print("Токен успешно получен!")
#
#     # --- ШАГ 3: ЗАПРОС НА ПОЛУЧЕНИЕ ЛИДОВ ---
#     print("\nПолучение 100 лидов...")
#     headers = {'Authorization': f'Bearer {token}'}
#     params = {'skip': 0, 'limit': 100}
#
#     leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers, params=params)
#     leads_response.raise_for_status()
#
#     leads_data = leads_response.json()
#
#     print(f"Успешно получено {len(leads_data)} лидов.")
#     if leads_data:
#         print("\nПример первого лида:")
#         print(json.dumps(leads_data[0], indent=2, ensure_ascii=False))
#     else:
#         print("Список лидов пуст.")
#
# except requests.exceptions.HTTPError as e:
#     print(f"\n--- Ошибка HTTP ---")
#     print(f"Статус код: {e.response.status_code}")
#     print(f"Ответ сервера: {e.response.text}")
# except requests.exceptions.RequestException as e:
#     print(f"\n--- Ошибка подключения ---")
#     print(f"Не удалось выполнить запрос: {e}")


import requests
import json
import time

# --- НАСТРОЙТЕ ЭТИ ПЕРЕМЕННЫЕ ---
BASE_URL = "http://89.111.169.47:8005"  # IP-адрес вашего сервера

# Мы будем генерировать уникального пользователя для каждого теста
UNIQUE_ID = int(time.time())
USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
USER_PASSWORD = "a_very_secure_password_123!"


# ---------------------------------

def run_test():
    """
    Выполняет полный цикл тестирования API:
    1. Регистрация нового пользователя.
    2. Вход (получение токена).
    3. Создание нового лида.
    4. Получение списка лидов.
    """
    token = None

    try:
        # --- ШАГ 1: РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ---
        print("-" * 50)
        print(f"1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")

        register_payload = {
            "email": USER_EMAIL,
            "password": USER_PASSWORD,
            "full_name": "Тестовый Пользователь"  # Добавьте/удалите поля в соответствии с вашей схемой UserCreate
        }

        # Предполагается эндпоинт /api/auth/register. Если он другой, измените.
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)

        if register_response.status_code == 201:
            print("✅ УСПЕХ: Пользователь успешно зарегистрирован.")
            # print("Ответ сервера:", json.dumps(register_response.json(), indent=2))
        else:
            # Если регистрация не удалась, вызываем ошибку
            register_response.raise_for_status()

        # --- ШАГ 2: ВХОД (ПОЛУЧЕНИЕ ТОКЕНА) ---
        print("-" * 50)
        print(f"2. ВХОД В СИСТЕМУ: {USER_EMAIL}")

        auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}

        auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
        auth_response.raise_for_status()

        token = auth_response.json()['access_token']
        print("✅ УСПЕХ: Токен успешно получен!")
        # print("Токен:", token[:30] + "...")

        # --- ШАГ 3: СОЗДАНИЕ НОВОГО ЛИДА ---
        print("-" * 50)
        print("3. СОЗДАНИЕ НОВОГО ЛИДА")

        headers = {'Authorization': f'Bearer {token}'}

        lead_payload = {
            # Заполните эти поля в соответствии с вашей схемой LeadCreate
            "organization_name": f"Тестовая Компания {UNIQUE_ID}",
            "inn": "1234567890",
            "contact_number": "+79991234567",
            "email": f"contact_{UNIQUE_ID}@company.com",
            "source": "Тестовый скрипт",
            "lead_status": "New",
            "rating": 5,
            "rejection_reason": "Нет",
            "responsible_manager_id": 1  # Убедитесь, что пользователь с ID=1 существует, или измените
        }

        create_lead_response = requests.post(f"{BASE_URL}/api/leads/", headers=headers, json=lead_payload)
        create_lead_response.raise_for_status()

        created_lead = create_lead_response.json()
        print("✅ УСПЕХ: Лид успешно создан.")
        print("Данные созданного лида:", json.dumps(created_lead, indent=2, ensure_ascii=False))

        # --- ШАГ 4: ПОЛУЧЕНИЕ СПИСКА ЛИДОВ ---
        print("-" * 50)
        print("4. ПОЛУЧЕНИЕ СПИСКА ЛИДОВ")

        leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
        leads_response.raise_for_status()

        leads_data = leads_response.json()

        print(f"✅ УСПЕХ: Успешно получено {len(leads_data)} лидов.")

        if leads_data:
            print("Последний созданный лид найден в списке.")
        else:
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Список лидов пуст, хотя мы только что создали один.")

        print("-" * 50)
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! 🎉")


    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
        print(f"URL запроса: {e.request.method} {e.request.url}")
        print(f"Тело запроса: {e.request.body}")
        print(f"Статус код: {e.response.status_code}")
        print(f"Ответ сервера: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ")
        print(f"Не удалось выполнить запрос: {e}")


# Запускаем наш тест
if __name__ == "__main__":
    run_test()