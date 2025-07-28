# # import requests
# # import json
# # import time
# #
# # # --- Настройте эти переменные ---
# # BASE_URL = "http://89.111.169.47:8005"
# # # Генерируем уникальные данные для нового пользователя
# # UNIQUE_ID = int(time.time())
# # USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
# # USER_PASSWORD = "a_very_secure_password"
# # # ---------------------------------
# #
# # try:
# #     # --- ШАГ 1: РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ---
# #     print(f"Регистрация нового пользователя: {USER_EMAIL}...")
# #     register_payload = {
# #         "email": USER_EMAIL,
# #         "password": USER_PASSWORD
# #         # Добавьте другие поля, если они требуются для регистрации (например, full_name)
# #     }
# #
# #     # Предполагаем, что у вас есть эндпоинт /api/auth/register
# #     # Если он другой - измените URL
# #     register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
# #
# #     # Проверяем, что регистрация прошла успешно (обычно код 201 Created)
# #     if register_response.status_code == 201:
# #         print("Пользователь успешно зарегистрирован!")
# #     elif register_response.status_code == 400 and "уже существует" in register_response.text:
# #         # Эта проверка на случай, если вы запустите скрипт дважды в одну секунду
# #         print("Пользователь с таким email уже существует, продолжаем...")
# #     else:
# #         # Если регистрация не удалась по другой причине, вызываем ошибку
# #         register_response.raise_for_status()
# #
# #     # --- ШАГ 2: ПОЛУЧЕНИЕ ТОКЕНА (ВХОД) ---
# #     print("\nПолучение токена...")
# #     auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
# #
# #     auth_response = requests.post(
# #         f"{BASE_URL}/api/auth/token",
# #         data=auth_payload_form
# #     )
# #     auth_response.raise_for_status()
# #     token = auth_response.json()['access_token']
# #     print("Токен успешно получен!")
# #
# #     # --- ШАГ 3: ЗАПРОС НА ПОЛУЧЕНИЕ ЛИДОВ ---
# #     print("\nПолучение 100 лидов...")
# #     headers = {'Authorization': f'Bearer {token}'}
# #     params = {'skip': 0, 'limit': 100}
# #
# #     leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers, params=params)
# #     leads_response.raise_for_status()
# #
# #     leads_data = leads_response.json()
# #
# #     print(f"Успешно получено {len(leads_data)} лидов.")
# #     if leads_data:
# #         print("\nПример первого лида:")
# #         print(json.dumps(leads_data[0], indent=2, ensure_ascii=False))
# #     else:
# #         print("Список лидов пуст.")
# #
# # except requests.exceptions.HTTPError as e:
# #     print(f"\n--- Ошибка HTTP ---")
# #     print(f"Статус код: {e.response.status_code}")
# #     print(f"Ответ сервера: {e.response.text}")
# # except requests.exceptions.RequestException as e:
# #     print(f"\n--- Ошибка подключения ---")
# #     print(f"Не удалось выполнить запрос: {e}")
#
#
# import requests
# import json
# import time
#
# # --- НАСТРОЙТЕ ЭТИ ПЕРЕМЕННЫЕ ---
# BASE_URL = "http://89.111.169.47:8005"  # IP-адрес вашего сервера
#
# # Мы будем генерировать уникального пользователя для каждого теста
# UNIQUE_ID = int(time.time())
# USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
# USER_PASSWORD = "a_very_secure_password_123!"
#
#
# # ---------------------------------
#
# def run_test():
#     """
#     Выполняет полный цикл тестирования API:
#     1. Регистрация нового пользователя.
#     2. Вход (получение токена).
#     3. Создание нового лида.
#     4. Получение списка лидов.
#     """
#     token = None
#
#     try:
#         # --- ШАГ 1: РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ---
#         print("-" * 50)
#         print(f"1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")
#
#         register_payload = {
#             "email": USER_EMAIL,
#             "password": USER_PASSWORD,
#             "full_name": "Тестовый Пользователь"  # Добавьте/удалите поля в соответствии с вашей схемой UserCreate
#         }
#
#         # Предполагается эндпоинт /api/auth/register. Если он другой, измените.
#         register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
#
#         if register_response.status_code == 201:
#             print("✅ УСПЕХ: Пользователь успешно зарегистрирован.")
#             # print("Ответ сервера:", json.dumps(register_response.json(), indent=2))
#         else:
#             # Если регистрация не удалась, вызываем ошибку
#             register_response.raise_for_status()
#
#         # --- ШАГ 2: ВХОД (ПОЛУЧЕНИЕ ТОКЕНА) ---
#         print("-" * 50)
#         print(f"2. ВХОД В СИСТЕМУ: {USER_EMAIL}")
#
#         auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
#
#         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
#         auth_response.raise_for_status()
#
#         token = auth_response.json()['access_token']
#         print("✅ УСПЕХ: Токен успешно получен!")
#         # print("Токен:", token[:30] + "...")
#
#         # --- ШАГ 3: СОЗДАНИЕ НОВОГО ЛИДА ---
#         print("-" * 50)
#         print("3. СОЗДАНИЕ НОВОГО ЛИДА")
#
#         headers = {'Authorization': f'Bearer {token}'}
#
#         lead_payload = {
#             # Заполните эти поля в соответствии с вашей схемой LeadCreate
#             "organization_name": f"Тестовая Компания {UNIQUE_ID}",
#             "inn": "1234567890",
#             "contact_number": "+79991234567",
#             "email": f"contact_{UNIQUE_ID}@company.com",
#             "source": "Тестовый скрипт",
#             "lead_status": "New",
#             "rating": 5,
#             "rejection_reason": "Нет",
#             "responsible_manager_id": 1  # Убедитесь, что пользователь с ID=1 существует, или измените
#         }
#
#         create_lead_response = requests.post(f"{BASE_URL}/api/leads/", headers=headers, json=lead_payload)
#         create_lead_response.raise_for_status()
#
#         created_lead = create_lead_response.json()
#         print("✅ УСПЕХ: Лид успешно создан.")
#         print("Данные созданного лида:", json.dumps(created_lead, indent=2, ensure_ascii=False))
#
#         # --- ШАГ 4: ПОЛУЧЕНИЕ СПИСКА ЛИДОВ ---
#         print("-" * 50)
#         print("4. ПОЛУЧЕНИЕ СПИСКА ЛИДОВ")
#
#         leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
#         leads_response.raise_for_status()
#
#         leads_data = leads_response.json()
#
#         print(f"✅ УСПЕХ: Успешно получено {len(leads_data)} лидов.")
#
#         if leads_data:
#             print("Последний созданный лид найден в списке.")
#         else:
#             print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Список лидов пуст, хотя мы только что создали один.")
#
#         print("-" * 50)
#         print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! 🎉")
#
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
#         print(f"URL запроса: {e.request.method} {e.request.url}")
#         print(f"Тело запроса: {e.request.body}")
#         print(f"Статус код: {e.response.status_code}")
#         print(f"Ответ сервера: {e.response.text}")
#     except requests.exceptions.RequestException as e:
#         print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ")
#         print(f"Не удалось выполнить запрос: {e}")
#
#
# # Запускаем наш тест
# if __name__ == "__main__":
#     run_test()


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
    Выполняет полный цикл тестирования API для лидов:
    1. Регистрация.
    2. Вход.
    3. Создание лида.
    4. Получение списка лидов.
    5. Получение созданного лида по ID.
    6. Обновление лида.
    7. Удаление лида.
    """
    token = None
    created_lead_id = None

    try:
        # --- ШАГ 1: РЕГИСТРАЦИЯ ---
        print("-" * 50)
        print(f"1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")
        register_payload = {"email": USER_EMAIL, "password": USER_PASSWORD, "full_name": "Тестовый Пользователь"}
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
        register_response.raise_for_status()
        print("✅ УСПЕХ: Пользователь зарегистрирован.")

        # --- ШАГ 2: ВХОД ---
        print("-" * 50)
        print(f"2. ВХОД В СИСТЕМУ: {USER_EMAIL}")
        auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
        auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
        auth_response.raise_for_status()
        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print("✅ УСПЕХ: Токен получен.")

        # --- ШАГ 3: СОЗДАНИЕ ЛИДА ---
        print("-" * 50)
        print("3. СОЗДАНИЕ НОВОГО ЛИДА")
        lead_payload = {
            "organization_name": f"Initial Company {UNIQUE_ID}",
            "inn": "1234567890",
            "contact_number": "+79991234567",
            "email": f"contact_{UNIQUE_ID}@company.com",
            "source": "Тестовый скрипт",
            "lead_status": "New",
        }
        create_lead_response = requests.post(f"{BASE_URL}/api/leads/", headers=headers, json=lead_payload)
        create_lead_response.raise_for_status()
        created_lead = create_lead_response.json()
        created_lead_id = created_lead['id']
        print(f"✅ УСПЕХ: Лид с ID={created_lead_id} успешно создан.")

        # --- ШАГ 4: ПОЛУЧЕНИЕ СПИСКА ЛИДОВ ---
        print("-" * 50)
        print("4. ПОЛУЧЕНИЕ СПИСКА ЛИДОВ")
        leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
        leads_response.raise_for_status()
        leads_data = leads_response.json()
        print(f"✅ УСПЕХ: Получено {len(leads_data)} лидов.")

        # Проверяем, что наш лид есть в списке
        found = any(lead['id'] == created_lead_id for lead in leads_data)
        if not found:
            raise Exception("Созданный лид не найден в общем списке!")

        # --- ШАГ 5: ПОЛУЧЕНИЕ ЛИДА ПО ID ---
        print("-" * 50)
        print(f"5. ПОЛУЧЕНИЕ ЛИДА ПО ID: {created_lead_id}")
        get_lead_response = requests.get(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers)
        get_lead_response.raise_for_status()
        fetched_lead = get_lead_response.json()
        assert fetched_lead['id'] == created_lead_id
        print(f"✅ УСПЕХ: Лид с ID={created_lead_id} успешно получен.")

        # --- ШАГ 6: ОБНОВЛЕНИЕ ЛИДА ---
        print("-" * 50)
        print(f"6. ОБНОВЛЕНИЕ ЛИДА С ID: {created_lead_id}")
        update_payload = {
            "organization_name": f"Updated Company Name {UNIQUE_ID}",
            "lead_status": "In Progress"
        }
        update_lead_response = requests.put(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers,
                                            json=update_payload)
        update_lead_response.raise_for_status()
        updated_lead = update_lead_response.json()

        assert updated_lead['organization_name'] == update_payload['organization_name']
        assert updated_lead['lead_status'] == update_payload['lead_status']
        print("✅ УСПЕХ: Лид успешно обновлен.")
        print("Обновленные данные:", json.dumps(updated_lead, indent=2, ensure_ascii=False))

        # --- ШАГ 7: УДАЛЕНИЕ ЛИДА ---
        print("-" * 50)
        print(f"7. УДАЛЕНИЕ ЛИДА С ID: {created_lead_id}")
        delete_lead_response = requests.delete(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers)
        # Успешное удаление возвращает код 204 No Content
        if delete_lead_response.status_code != 204:
            raise Exception(
                f"Ошибка при удалении. Статус-код: {delete_lead_response.status_code}, Ответ: {delete_lead_response.text}")
        print(f"✅ УСПЕХ: Лид с ID={created_lead_id} успешно удален.")

        # Проверим, что лид действительно удален (должны получить ошибку 404)
        get_deleted_lead_response = requests.get(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers)
        if get_deleted_lead_response.status_code == 404:
            print("✅ УСПЕХ: Проверка подтвердила, что лид удален (получен ответ 404).")
        else:
            raise Exception("Лид не был удален, так как он все еще доступен по ID!")

        print("-" * 50)
        print("\n🎉 ВСЕ CRUD-ТЕСТЫ ДЛЯ ЛИДОВ ПРОШЛИ УСПЕШНО! 🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
        print(f"URL запроса: {e.request.method} {e.request.url}")
        # Печатаем тело, только если оно не пустое
        if e.request.body:
            print(f"Тело запроса: {e.request.body}")
        print(f"Статус код: {e.response.status_code}")
        print(f"Ответ сервера: {e.response.text}")
    except Exception as e:
        print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА")
        print(f"Ошибка: {e}")


# Запускаем наш тест
if __name__ == "__main__":
    run_test()
