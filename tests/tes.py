# # # # # import requests
# # # # # import json
# # # # # import time
# # # # #
# # # # # # --- Настройте эти переменные ---
# # # # # BASE_URL = "http://89.111.169.47:8005"
# # # # # # Генерируем уникальные данные для нового пользователя
# # # # # UNIQUE_ID = int(time.time())
# # # # # USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
# # # # # USER_PASSWORD = "a_very_secure_password"
# # # # # # ---------------------------------
# # # # #
# # # # # try:
# # # # #     # --- ШАГ 1: РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ---
# # # # #     print(f"Регистрация нового пользователя: {USER_EMAIL}...")
# # # # #     register_payload = {
# # # # #         "email": USER_EMAIL,
# # # # #         "password": USER_PASSWORD
# # # # #         # Добавьте другие поля, если они требуются для регистрации (например, full_name)
# # # # #     }
# # # # #
# # # # #     # Предполагаем, что у вас есть эндпоинт /api/auth/register
# # # # #     # Если он другой - измените URL
# # # # #     register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
# # # # #
# # # # #     # Проверяем, что регистрация прошла успешно (обычно код 201 Created)
# # # # #     if register_response.status_code == 201:
# # # # #         print("Пользователь успешно зарегистрирован!")
# # # # #     elif register_response.status_code == 400 and "уже существует" in register_response.text:
# # # # #         # Эта проверка на случай, если вы запустите скрипт дважды в одну секунду
# # # # #         print("Пользователь с таким email уже существует, продолжаем...")
# # # # #     else:
# # # # #         # Если регистрация не удалась по другой причине, вызываем ошибку
# # # # #         register_response.raise_for_status()
# # # # #
# # # # #     # --- ШАГ 2: ПОЛУЧЕНИЕ ТОКЕНА (ВХОД) ---
# # # # #     print("\nПолучение токена...")
# # # # #     auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
# # # # #
# # # # #     auth_response = requests.post(
# # # # #         f"{BASE_URL}/api/auth/token",
# # # # #         data=auth_payload_form
# # # # #     )
# # # # #     auth_response.raise_for_status()
# # # # #     token = auth_response.json()['access_token']
# # # # #     print("Токен успешно получен!")
# # # # #
# # # # #     # --- ШАГ 3: ЗАПРОС НА ПОЛУЧЕНИЕ ЛИДОВ ---
# # # # #     print("\nПолучение 100 лидов...")
# # # # #     headers = {'Authorization': f'Bearer {token}'}
# # # # #     params = {'skip': 0, 'limit': 100}
# # # # #
# # # # #     leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers, params=params)
# # # # #     leads_response.raise_for_status()
# # # # #
# # # # #     leads_data = leads_response.json()
# # # # #
# # # # #     print(f"Успешно получено {len(leads_data)} лидов.")
# # # # #     if leads_data:
# # # # #         print("\nПример первого лида:")
# # # # #         print(json.dumps(leads_data[0], indent=2, ensure_ascii=False))
# # # # #     else:
# # # # #         print("Список лидов пуст.")
# # # # #
# # # # # except requests.exceptions.HTTPError as e:
# # # # #     print(f"\n--- Ошибка HTTP ---")
# # # # #     print(f"Статус код: {e.response.status_code}")
# # # # #     print(f"Ответ сервера: {e.response.text}")
# # # # # except requests.exceptions.RequestException as e:
# # # # #     print(f"\n--- Ошибка подключения ---")
# # # # #     print(f"Не удалось выполнить запрос: {e}")
# # # #
# # # #
# # # # import requests
# # # # import json
# # # # import time
# # # #
# # # # # --- НАСТРОЙТЕ ЭТИ ПЕРЕМЕННЫЕ ---
# # # # BASE_URL = "http://89.111.169.47:8005"  # IP-адрес вашего сервера
# # # #
# # # # # Мы будем генерировать уникального пользователя для каждого теста
# # # # UNIQUE_ID = int(time.time())
# # # # USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
# # # # USER_PASSWORD = "a_very_secure_password_123!"
# # # #
# # # #
# # # # # ---------------------------------
# # # #
# # # # def run_test():
# # # #     """
# # # #     Выполняет полный цикл тестирования API:
# # # #     1. Регистрация нового пользователя.
# # # #     2. Вход (получение токена).
# # # #     3. Создание нового лида.
# # # #     4. Получение списка лидов.
# # # #     """
# # # #     token = None
# # # #
# # # #     try:
# # # #         # --- ШАГ 1: РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ ---
# # # #         print("-" * 50)
# # # #         print(f"1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")
# # # #
# # # #         register_payload = {
# # # #             "email": USER_EMAIL,
# # # #             "password": USER_PASSWORD,
# # # #             "full_name": "Тестовый Пользователь"  # Добавьте/удалите поля в соответствии с вашей схемой UserCreate
# # # #         }
# # # #
# # # #         # Предполагается эндпоинт /api/auth/register. Если он другой, измените.
# # # #         register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
# # # #
# # # #         if register_response.status_code == 201:
# # # #             print("✅ УСПЕХ: Пользователь успешно зарегистрирован.")
# # # #             # print("Ответ сервера:", json.dumps(register_response.json(), indent=2))
# # # #         else:
# # # #             # Если регистрация не удалась, вызываем ошибку
# # # #             register_response.raise_for_status()
# # # #
# # # #         # --- ШАГ 2: ВХОД (ПОЛУЧЕНИЕ ТОКЕНА) ---
# # # #         print("-" * 50)
# # # #         print(f"2. ВХОД В СИСТЕМУ: {USER_EMAIL}")
# # # #
# # # #         auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
# # # #
# # # #         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
# # # #         auth_response.raise_for_status()
# # # #
# # # #         token = auth_response.json()['access_token']
# # # #         print("✅ УСПЕХ: Токен успешно получен!")
# # # #         # print("Токен:", token[:30] + "...")
# # # #
# # # #         # --- ШАГ 3: СОЗДАНИЕ НОВОГО ЛИДА ---
# # # #         print("-" * 50)
# # # #         print("3. СОЗДАНИЕ НОВОГО ЛИДА")
# # # #
# # # #         headers = {'Authorization': f'Bearer {token}'}
# # # #
# # # #         lead_payload = {
# # # #             # Заполните эти поля в соответствии с вашей схемой LeadCreate
# # # #             "organization_name": f"Тестовая Компания {UNIQUE_ID}",
# # # #             "inn": "1234567890",
# # # #             "contact_number": "+79991234567",
# # # #             "email": f"contact_{UNIQUE_ID}@company.com",
# # # #             "source": "Тестовый скрипт",
# # # #             "lead_status": "New",
# # # #             "rating": 5,
# # # #             "rejection_reason": "Нет",
# # # #             "responsible_manager_id": 1  # Убедитесь, что пользователь с ID=1 существует, или измените
# # # #         }
# # # #
# # # #         create_lead_response = requests.post(f"{BASE_URL}/api/leads/", headers=headers, json=lead_payload)
# # # #         create_lead_response.raise_for_status()
# # # #
# # # #         created_lead = create_lead_response.json()
# # # #         print("✅ УСПЕХ: Лид успешно создан.")
# # # #         print("Данные созданного лида:", json.dumps(created_lead, indent=2, ensure_ascii=False))
# # # #
# # # #         # --- ШАГ 4: ПОЛУЧЕНИЕ СПИСКА ЛИДОВ ---
# # # #         print("-" * 50)
# # # #         print("4. ПОЛУЧЕНИЕ СПИСКА ЛИДОВ")
# # # #
# # # #         leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
# # # #         leads_response.raise_for_status()
# # # #
# # # #         leads_data = leads_response.json()
# # # #
# # # #         print(f"✅ УСПЕХ: Успешно получено {len(leads_data)} лидов.")
# # # #
# # # #         if leads_data:
# # # #             print("Последний созданный лид найден в списке.")
# # # #         else:
# # # #             print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Список лидов пуст, хотя мы только что создали один.")
# # # #
# # # #         print("-" * 50)
# # # #         print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! 🎉")
# # # #
# # # #
# # # #     except requests.exceptions.HTTPError as e:
# # # #         print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
# # # #         print(f"URL запроса: {e.request.method} {e.request.url}")
# # # #         print(f"Тело запроса: {e.request.body}")
# # # #         print(f"Статус код: {e.response.status_code}")
# # # #         print(f"Ответ сервера: {e.response.text}")
# # # #     except requests.exceptions.RequestException as e:
# # # #         print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ")
# # # #         print(f"Не удалось выполнить запрос: {e}")
# # # #
# # # #
# # # # # Запускаем наш тест
# # # # if __name__ == "__main__":
# # # #     run_test()
# # #
# # #
# # # import requests
# # # import json
# # # import time
# # #
# # # # --- НАСТРОЙТЕ ЭТИ ПЕРЕМЕННЫЕ ---
# # # BASE_URL = "http://89.111.169.47:8005"  # IP-адрес вашего сервера
# # #
# # # # Мы будем генерировать уникального пользователя для каждого теста
# # # UNIQUE_ID = int(time.time())
# # # USER_EMAIL = f"testuser_{UNIQUE_ID}@example.com"
# # # USER_PASSWORD = "a_very_secure_password_123!"
# # #
# # #
# # # # ---------------------------------
# # #
# # # def run_test():
# # #     """
# # #     Выполняет полный цикл тестирования API для лидов:
# # #     1. Регистрация.
# # #     2. Вход.
# # #     3. Создание лида.
# # #     4. Получение списка лидов.
# # #     5. Получение созданного лида по ID.
# # #     6. Обновление лида.
# # #     7. Удаление лида.
# # #     """
# # #     token = None
# # #     created_lead_id = None
# # #
# # #     try:
# # #         # --- ШАГ 1: РЕГИСТРАЦИЯ ---
# # #         print("-" * 50)
# # #         print(f"1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")
# # #         register_payload = {"email": USER_EMAIL, "password": USER_PASSWORD, "full_name": "Тестовый Пользователь"}
# # #         register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
# # #         register_response.raise_for_status()
# # #         print("✅ УСПЕХ: Пользователь зарегистрирован.")
# # #
# # #         # --- ШАГ 2: ВХОД ---
# # #         print("-" * 50)
# # #         print(f"2. ВХОД В СИСТЕМУ: {USER_EMAIL}")
# # #         auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
# # #         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
# # #         auth_response.raise_for_status()
# # #         token = auth_response.json()['access_token']
# # #         headers = {'Authorization': f'Bearer {token}'}
# # #         print("✅ УСПЕХ: Токен получен.")
# # #
# # #         # --- ШАГ 3: СОЗДАНИЕ ЛИДА ---
# # #         print("-" * 50)
# # #         print("3. СОЗДАНИЕ НОВОГО ЛИДА")
# # #         lead_payload = {
# # #             "organization_name": f"Initial Company {UNIQUE_ID}",
# # #             "inn": "1234567890",
# # #             "contact_number": "+79991234567",
# # #             "email": f"contact_{UNIQUE_ID}@company.com",
# # #             "source": "Тестовый скрипт",
# # #             "lead_status": "New",
# # #         }
# # #         create_lead_response = requests.post(f"{BASE_URL}/api/leads/", headers=headers, json=lead_payload)
# # #         create_lead_response.raise_for_status()
# # #         created_lead = create_lead_response.json()
# # #         created_lead_id = created_lead['id']
# # #         print(f"✅ УСПЕХ: Лид с ID={created_lead_id} успешно создан.")
# # #
# # #         # --- ШАГ 4: ПОЛУЧЕНИЕ СПИСКА ЛИДОВ ---
# # #         print("-" * 50)
# # #         print("4. ПОЛУЧЕНИЕ СПИСКА ЛИДОВ")
# # #         leads_response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
# # #         leads_response.raise_for_status()
# # #         leads_data = leads_response.json()
# # #         print(f"✅ УСПЕХ: Получено {len(leads_data)} лидов.")
# # #
# # #         # Проверяем, что наш лид есть в списке
# # #         found = any(lead['id'] == created_lead_id for lead in leads_data)
# # #         if not found:
# # #             raise Exception("Созданный лид не найден в общем списке!")
# # #
# # #         # --- ШАГ 5: ПОЛУЧЕНИЕ ЛИДА ПО ID ---
# # #         print("-" * 50)
# # #         print(f"5. ПОЛУЧЕНИЕ ЛИДА ПО ID: {created_lead_id}")
# # #         get_lead_response = requests.get(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers)
# # #         get_lead_response.raise_for_status()
# # #         fetched_lead = get_lead_response.json()
# # #         assert fetched_lead['id'] == created_lead_id
# # #         print(f"✅ УСПЕХ: Лид с ID={created_lead_id} успешно получен.")
# # #
# # #         # --- ШАГ 6: ОБНОВЛЕНИЕ ЛИДА ---
# # #         print("-" * 50)
# # #         print(f"6. ОБНОВЛЕНИЕ ЛИДА С ID: {created_lead_id}")
# # #         update_payload = {
# # #             "organization_name": f"Updated Company Name {UNIQUE_ID}",
# # #             "lead_status": "In Progress"
# # #         }
# # #         update_lead_response = requests.put(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers,
# # #                                             json=update_payload)
# # #         update_lead_response.raise_for_status()
# # #         updated_lead = update_lead_response.json()
# # #
# # #         assert updated_lead['organization_name'] == update_payload['organization_name']
# # #         assert updated_lead['lead_status'] == update_payload['lead_status']
# # #         print("✅ УСПЕХ: Лид успешно обновлен.")
# # #         print("Обновленные данные:", json.dumps(updated_lead, indent=2, ensure_ascii=False))
# # #
# # #         # --- ШАГ 7: УДАЛЕНИЕ ЛИДА ---
# # #         print("-" * 50)
# # #         print(f"7. УДАЛЕНИЕ ЛИДА С ID: {created_lead_id}")
# # #         delete_lead_response = requests.delete(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers)
# # #         # Успешное удаление возвращает код 204 No Content
# # #         if delete_lead_response.status_code != 204:
# # #             raise Exception(
# # #                 f"Ошибка при удалении. Статус-код: {delete_lead_response.status_code}, Ответ: {delete_lead_response.text}")
# # #         print(f"✅ УСПЕХ: Лид с ID={created_lead_id} успешно удален.")
# # #
# # #         # Проверим, что лид действительно удален (должны получить ошибку 404)
# # #         get_deleted_lead_response = requests.get(f"{BASE_URL}/api/leads/{created_lead_id}", headers=headers)
# # #         if get_deleted_lead_response.status_code == 404:
# # #             print("✅ УСПЕХ: Проверка подтвердила, что лид удален (получен ответ 404).")
# # #         else:
# # #             raise Exception("Лид не был удален, так как он все еще доступен по ID!")
# # #
# # #         print("-" * 50)
# # #         print("\n🎉 ВСЕ CRUD-ТЕСТЫ ДЛЯ ЛИДОВ ПРОШЛИ УСПЕШНО! 🎉")
# # #
# # #     except requests.exceptions.HTTPError as e:
# # #         print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
# # #         print(f"URL запроса: {e.request.method} {e.request.url}")
# # #         # Печатаем тело, только если оно не пустое
# # #         if e.request.body:
# # #             print(f"Тело запроса: {e.request.body}")
# # #         print(f"Статус код: {e.response.status_code}")
# # #         print(f"Ответ сервера: {e.response.text}")
# # #     except Exception as e:
# # #         print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА")
# # #         print(f"Ошибка: {e}")
# # #
# # #
# # # # Запускаем наш тест
# # # if __name__ == "__main__":
# # #     run_test()
# #
# #
# # import requests
# # import json
# # import time
# #
# # # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
# #
# # # Адрес вашего запущенного API
# # # BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# # BASE_URL = "http://89.111.169.47:8005"
# # # ВАЖНО: Укажите здесь тот же секретный токен, что и в вашем .env файле
# # CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# #
# # # --- Конфигурация новой таблицы ---
# # # name - системное имя (только латиница, цифры, '_'), используется в URL
# # # display_name - человекочитаемое имя для интерфейса
# # TABLE_CONFIG = {
# #     "name": f"contracts_{int(time.time())}",  # Генерируем уникальное имя, чтобы избежать конфликтов
# #     "display_name": "Договоры"
# # }
# #
# # # --- Конфигурация колонок для этой таблицы ---
# # # value_type может быть: "string", "integer", "float", "date", "boolean"
# # ATTRIBUTES_CONFIG = [
# #     {"name": "contract_number", "display_name": "Номер договора", "value_type": "string"},
# #     {"name": "contract_sum", "display_name": "Сумма договора", "value_type": "float"},
# #     {"name": "is_signed", "display_name": "Подписан", "value_type": "boolean"},
# #     {"name": "signing_date", "display_name": "Дата подписания", "value_type": "date"}
# # ]
# #
# #
# # # ----------------------------------------------------
# #
# # def print_status(ok, message):
# #     """Выводит красивый статус операции."""
# #     if ok:
# #         print(f"✅ [SUCCESS] {message}")
# #     else:
# #         print(f"❌ [FAILURE] {message}")
# #         exit(1)
# #
# #
# # def run_creation_script():
# #     """
# #     Выполняет полный цикл: Регистрация -> Авторизация -> Создание таблицы и колонок.
# #     """
# #     headers = {}
# #
# #     try:
# #         # --- ШАГ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ ---
# #         print("-" * 60)
# #         print("ШАГ 1: Регистрация нового пользователя и авторизация...")
# #
# #         # Генерируем уникальные данные для нового пользователя
# #         unique_id = int(time.time())
# #         user_email = f"table_creator_{unique_id}@example.com"
# #         user_password = "a_very_secure_password_123!"
# #
# #         # 1.1. Регистрация
# #         register_payload = {
# #             "email": user_email,
# #             "password": user_password,
# #             "full_name": f"Table Creator {unique_id}",
# #             "registration_token": CORRECT_REGISTRATION_TOKEN
# #         }
# #         reg_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
# #         # Проверяем, что регистрация прошла успешно (код 201)
# #         if reg_response.status_code != 201:
# #             print_status(False, f"Ошибка регистрации: {reg_response.text}")
# #
# #         # 1.2. Вход (получение токена)
# #         auth_payload_form = {'username': user_email, 'password': user_password}
# #         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
# #         auth_response.raise_for_status()
# #
# #         token = auth_response.json()['access_token']
# #         headers = {'Authorization': f'Bearer {token}'}
# #         print_status(True, f"Успешно зарегистрирован и авторизован пользователь: {user_email}")
# #
# #         # --- ШАГ 2: СОЗДАНИЕ ТАБЛИЦЫ ---
# #         print("\n" + "-" * 60)
# #         print(f"ШАГ 2: Создание таблицы '{TABLE_CONFIG['display_name']}' (POST /api/meta/entity-types)")
# #
# #         response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=TABLE_CONFIG)
# #         response.raise_for_status()
# #
# #         entity_type_data = response.json()
# #         entity_type_id = entity_type_data['id']
# #
# #         print_status(True, f"Таблица успешно создана с ID: {entity_type_id}")
# #         print("Бэкенд автоматически создал для нее разрешения (permissions)...")
# #
# #         # --- ШАГ 3: ДОБАВЛЕНИЕ КОЛОНОК ---
# #         print("\n" + "-" * 60)
# #         print(f"ШАГ 3: Добавление колонок в таблицу (ID: {entity_type_id})...")
# #
# #         if not ATTRIBUTES_CONFIG:
# #             print(" -> Список колонок для добавления пуст. Пропускаем шаг.")
# #         else:
# #             for attr_payload in ATTRIBUTES_CONFIG:
# #                 url = f"{BASE_URL}/api/meta/entity-types/{entity_type_id}/attributes"
# #                 attr_response = requests.post(url, headers=headers, json=attr_payload)
# #                 attr_response.raise_for_status()
# #                 print(f" -> Добавлена колонка: '{attr_payload['display_name']}'")
# #             print_status(True, f"Успешно добавлено {len(ATTRIBUTES_CONFIG)} колонок.")
# #
# #         print("\n" + "-" * 60)
# #         print("\n🎉🎉🎉 ВСЕ ГОТОВО! 🎉🎉🎉")
# #         print(f"Таблица '{TABLE_CONFIG['display_name']}' с системным именем '{TABLE_CONFIG['name']}' создана.")
# #         print("\nЧТО ДЕЛАТЬ ДАЛЬШЕ:")
# #         print("1. Перезапустите ваш FastAPI сервер (uvicorn).")
# #         print("2. Зайдите в админ-панель -> Роли.")
# #         print("3. При создании/редактировании роли вы увидите новые разрешения, например:")
# #         print(f"   - data:view:{TABLE_CONFIG['name']}")
# #         print(f"   - data:edit:{TABLE_CONFIG['name']}")
# #         print("4. Назначьте эти права нужным ролям, чтобы дать пользователям доступ к новой таблице.")
# #
# #     except requests.exceptions.HTTPError as e:
# #         print(f"\n❌ ОШИБКА HTTP.")
# #         print(f"URL запроса: {e.request.method} {e.request.url}")
# #         print(f"Статус код: {e.response.status_code}")
# #         print(f"Ответ сервера: {e.response.text}")
# #     except Exception as e:
# #         print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
# #
# #
# # if __name__ == "__main__":
# #     run_creation_script()
#
#
# # import requests
# # import json
# #
# # # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
# #
# # # Адрес вашего запущенного API
# # BASE_URL = "http://127.0.0.1:8005"
# # # BASE_URL = "http://89.111.169.47:8005"
# #
# # # --- Данные пользователя, которому вы дали доступ ---   SELECT id, email FROM users WHERE email = 'user@example.com';
# # USER_EMAIL = "user2@example.com"
# # USER_PASSWORD = "password_b"
# #
# # # --- Системное имя кастомной таблицы для просмотра ---
# # # Это поле 'name', а не 'display_name'
# # # TABLE_NAME_TO_VIEW = "klienty"  # <--- ЗАМЕНИТЕ НА ИМЯ ВАШЕЙ ТАБЛИЦЫ
# #
#
#
# # ----------------------------------------------------
#
# # def print_status(ok, message):
# #     """Выводит красивый статус операции."""
# #     if ok:
# #         print(f"✅ [SUCCESS] {message}")
# #     else:
# #         print(f"❌ [FAILURE] {message}")
# #         exit(1)
# #
# #
# # def list_accessible_tables():
# #     """
# #     Авторизуется, получает права пользователя и на их основе
# #     фильтрует общий список таблиц, чтобы показать только доступные.
# #     """
# #     headers = {}
# #
# #     try:
# #         # --- ШАГ 1: АВТОРИЗАЦИЯ И ПОЛУЧЕНИЕ ПРАВ ---
# #         print("-" * 60)
# #         print(f"ШАГ 1: Авторизация и получение прав для {USER_EMAIL}...")
# #
# #         # 1.1. Получаем токен
# #         auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
# #         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
# #         auth_response.raise_for_status()
# #         token = auth_response.json()['access_token']
# #         headers = {'Authorization': f'Bearer {token}'}
# #
# #         # 1.2. Получаем данные о пользователе, включая его разрешения
# #         me_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
# #         me_response.raise_for_status()
# #         user_data = me_response.json()
# #         user_permissions = set(user_data.get("permissions", []))
# #
# #         print_status(True, f"Получено {len(user_permissions)} уникальных разрешений.")
# #         # print("Разрешения пользователя:", user_permissions)
# #
# #         # --- ШАГ 2: ПОЛУЧЕНИЕ ОБЩЕГО СПИСКА ВСЕХ ТАБЛИЦ ---
# #         print("\n" + "-" * 60)
# #         print("ШАГ 2: Получение общего списка всех кастомных таблиц...")
# #
# #         # Запрашиваем все кастомные таблицы, созданные в этом тенанте
# #         meta_response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
# #         meta_response.raise_for_status()
# #         all_custom_tables = meta_response.json()
# #
# #         print(f" -> Найдено всего кастомных таблиц в тенанте: {len(all_custom_tables)}")
# #
# #         # --- ШАГ 3: ФИЛЬТРАЦИЯ И ВЫВОД РЕЗУЛЬТАТА ---
# #         print("\n" + "-" * 60)
# #         print("ШАГ 3: Фильтрация таблиц на основе прав пользователя...")
# #
# #         accessible_tables = []
# #
# #         # Проверяем доступ к стандартным сущностям
# #         if "leads:view" in user_permissions:
# #             accessible_tables.append({"display_name": "Лиды (стандартная)", "system_name": "leads"})
# #         if "legal_entities:view" in user_permissions:
# #             accessible_tables.append({"display_name": "Юр. лица (стандартная)", "system_name": "legal-entities"})
# #         if "individuals:view" in user_permissions:
# #             accessible_tables.append({"display_name": "Физ. лица (стандартная)", "system_name": "individuals"})
# #
# #         # Проверяем доступ к кастомным таблицам
# #         for table in all_custom_tables:
# #             view_permission_name = f"data:view:{table['name']}"
# #             if view_permission_name in user_permissions:
# #                 accessible_tables.append({
# #                     "display_name": table['display_name'],
# #                     "system_name": table['name']
# #                 })
# #
# #         print_status(True, f"Найдено доступных для просмотра таблиц: {len(accessible_tables)}")
# #
# #         # --- ШАГ 4: ВЫВОД СПИСКА ---
# #         print("\n" + "-" * 60)
# #         print("СПИСОК ТАБЛИЦ, ДОСТУПНЫХ ПОЛЬЗОВАТЕЛЮ:")
# #
# #         if not accessible_tables:
# #             print("\nУ пользователя нет доступа ни к одной таблице.")
# #         else:
# #             for table in accessible_tables:
# #                 print(f"  - {table['display_name']} (системное имя: {table['system_name']})")
# #
# #         print("\n" + "-" * 60)
# #
# #     except requests.exceptions.HTTPError as e:
# #         print(f"\n❌ ОШИБКА HTTP.")
# #         print(f"Статус код: {e.response.status_code}")
# #         print(f"Ответ сервера: {e.response.text}")
# #     except Exception as e:
# #         print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
# #
# #
# # if __name__ == "__main__":
# #     list_accessible_tables()
#
#
# import requests
# import time
#
# # --- НАСТРОЙКИ ---
# # BASE_URL = "http://127.0.0.1:8005"
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
# BASE_URL = "http://89.111.169.47:8005"
#
# # -----------------
#
# def print_status(ok, message):
#     if ok:
#         print(f"✅ [PASS] {message}")
#     else:
#         print(f"❌ [FAIL] {message}")
#         exit(1)
#
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
#
# # ... (функция register_and_login из предыдущего скрипта)
#
# def run_rename_test():
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
#         headers = register_and_login()
#
#         initial_name = "Старое Имя"
#         table_config = {"name": f"rename_test_{int(time.time())}", "display_name": initial_name}
#
#         response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config)
#         response.raise_for_status()
#         table_id = response.json()['id']
#         print_status(True, f"Создана таблица '{initial_name}' с ID: {table_id}")
#
#         # --- ШАГ 2: ИЗМЕНЕНИЕ ИМЕНИ ---
#         print_header("ШАГ 2: ИЗМЕНЕНИЕ ОТОБРАЖАЕМОГО ИМЕНИ")
#
#         new_name = "НОВОЕ ОБНОВЛЕННОЕ ИМЯ"
#         update_payload = {"display_name": new_name}
#
#         url = f"{BASE_URL}/api/meta/entity-types/{table_id}"
#         update_response = requests.put(url, headers=headers, json=update_payload)
#         update_response.raise_for_status()
#
#         updated_table_data = update_response.json()
#         print_status(update_response.status_code == 200, "Запрос на обновление прошел успешно (статус 200).")
#         print_status(
#             updated_table_data.get('display_name') == new_name,
#             f"API в ответе вернуло новое имя: '{updated_table_data.get('display_name')}'"
#         )
#
#         # --- ШАГ 3: ФИНАЛЬНАЯ ПРОВЕРКА ---
#         print_header("ШАГ 3: ПРОВЕРКА, ЧТО ИЗМЕНЕНИЯ СОХРАНИЛИСЬ")
#
#         get_response = requests.get(url, headers=headers)
#         get_response.raise_for_status()
#         final_table_data = get_response.json()
#
#         print(f" -> Повторный GET-запрос вернул имя: '{final_table_data.get('display_name')}'")
#         print_status(
#             final_table_data.get('display_name') == new_name,
#             "Изменения успешно сохранены и подтверждены."
#         )
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ НА ИЗМЕНЕНИЕ ИМЕНИ ТАБЛИЦЫ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP.")
#         print(f"URL: {e.request.method} {e.request.url}")
#         print(f"Статус: {e.response.status_code}")
#         print(f"Ответ: {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
#
#
# # (Вставьте сюда функцию register_and_login из предыдущего скрипта)
# def register_and_login():
#     unique_id = int(time.time())
#     email = f"rename_tester_{unique_id}@example.com"
#     password = "password123"
#     reg_payload = {"email": email, "password": password, "full_name": "Rename Tester",
#                    "registration_token": CORRECT_REGISTRATION_TOKEN}
#     requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#     auth_payload = {'username': email, 'password': password}
#     token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
#
# if __name__ == "__main__":
#     run_rename_test()


