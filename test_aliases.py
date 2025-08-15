# # # # test_aliases.py
# # # import requests
# # # import json
# # # import time
# # #
# # # # --- НАСТРОЙКИ ---
# # # BASE_URL = "http://127.0.0.1:8005"
# # #
# # # # BASE_URL = "http://89.111.169.47:8005"
# # #
# # #
# # # # ВАЖНО: Укажите здесь тот же токен, что и в вашем .env файле
# # # CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # # # -----------------
# # #
# # # UNIQUE_ID = int(time.time())
# # #
# # #
# # # def print_status(ok, message):
# # #     """Выводит статус операции."""
# # #     if ok:
# # #         print(f"✅ [SUCCESS] {message}")
# # #     else:
# # #         print(f"❌ [FAILURE] {message}")
# # #         # Завершаем скрипт при первой же ошибке
# # #         exit(1)
# # #
# # #
# # # def run_aliases_test():
# # #     """
# # #     Выполняет полный цикл тестирования API для псевдонимов.
# # #     """
# # #     token = None
# # #     headers = {}
# # #
# # #     try:
# # #         # --- ШАГ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ ---
# # #         print("-" * 50)
# # #         print("1. РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ")
# # #         user_email = f"alias_tester_{UNIQUE_ID}@example.com"
# # #         password = "password123"
# # #         reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
# # #         requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
# # #
# # #         auth_payload_form = {'username': user_email, 'password': password}
# # #         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
# # #         auth_response.raise_for_status()
# # #         token = auth_response.json()['access_token']
# # #         headers = {'Authorization': f'Bearer {token}'}
# # #         print_status(True, "Успешно зарегистрирован и получен токен.")
# # #
# # #         # --- ШАГ 2: ПОДГОТОВКА СРЕДЫ (СОЗДАНИЕ КАСТОМНОЙ ТАБЛИЦЫ) ---
# # #         print("-" * 50)
# # #         print("2. ПОДГОТОВКА СРЕДЫ")
# # #         # Создаем кастомную таблицу "Кандидаты", чтобы было что переименовывать
# # #         entity_payload = {"name": "candidates", "display_name": "Кандидаты"}
# # #         response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=entity_payload)
# # #         response.raise_for_status()
# # #         entity_type_id = response.json()['id']
# # #         # Создаем в ней колонку
# # #         attr_payload = {"name": "expected_salary", "display_name": "Ожидаемая ЗП", "value_type": "integer"}
# # #         response = requests.post(f"{BASE_URL}/api/meta/entity-types/{entity_type_id}/attributes", headers=headers,
# # #                                  json=attr_payload)
# # #         response.raise_for_status()
# # #         print_status(True, "Создана кастомная таблица 'candidates' с колонкой 'expected_salary'.")
# # #
# # #         # --- ШАГ 3: УСТАНОВКА ПСЕВДОНИМОВ ---
# # #         print("-" * 50)
# # #         print("3. УСТАНОВКА ПСЕВДОНИМОВ (POST /api/aliases/)")
# # #
# # #         # 3.1. Устанавливаем псевдоним для стандартной таблицы 'leads'
# # #         alias1_payload = {
# # #             "table_name": "leads",
# # #             "attribute_name": "organization_name",
# # #             "display_name": "Название Компании-Клиента"
# # #         }
# # #         response1 = requests.post(f"{BASE_URL}/api/aliases/", headers=headers, json=alias1_payload)
# # #         response1.raise_for_status()
# # #         print_status(True, f"Установлен псевдоним для 'leads.organization_name'")
# # #
# # #         # 3.2. Устанавливаем псевдоним для кастомной таблицы 'candidates'
# # #         alias2_payload = {
# # #             "table_name": "candidates",
# # #             "attribute_name": "expected_salary",
# # #             "display_name": "Зарплатные ожидания (руб.)"
# # #         }
# # #         response2 = requests.post(f"{BASE_URL}/api/aliases/", headers=headers, json=alias2_payload)
# # #         response2.raise_for_status()
# # #         print_status(True, f"Установлен псевдоним для 'candidates.expected_salary'")
# # #
# # #         # --- ШАГ 4: ПОЛУЧЕНИЕ ВСЕХ ПСЕВДОНИМОВ ---
# # #         print("-" * 50)
# # #         print("4. ПРОВЕРКА ПОЛУЧЕНИЯ ВСЕХ ПСЕВДОНИМОВ (GET /api/aliases/)")
# # #
# # #         get_response = requests.get(f"{BASE_URL}/api/aliases/", headers=headers)
# # #         get_response.raise_for_status()
# # #         all_aliases = get_response.json()
# # #
# # #         print("Полученные данные:", json.dumps(all_aliases, indent=2, ensure_ascii=False))
# # #
# # #         # Проверяем, что оба псевдонима на месте и корректны
# # #         expected_aliases_count = 2
# # #         print_status(
# # #             len(all_aliases) == expected_aliases_count,
# # #             f"Получено {len(all_aliases)} таблицы с псевдонимами, ожидалось {expected_aliases_count}."
# # #         )
# # #         print_status(
# # #             all_aliases.get("leads", {}).get("organization_name") == alias1_payload["display_name"],
# # #             "Псевдоним для 'leads' корректен."
# # #         )
# # #         print_status(
# # #             all_aliases.get("candidates", {}).get("expected_salary") == alias2_payload["display_name"],
# # #             "Псевдоним для 'candidates' корректен."
# # #         )
# # #
# # #         # --- ШАГ 5: УДАЛЕНИЕ (СБРОС) ПСЕВДОНИМА ---
# # #         print("-" * 50)
# # #         print("5. ПРОВЕРКА УДАЛЕНИЯ ПСЕВДОНИМА (DELETE /api/aliases/{table}/{attr})")
# # #
# # #         # Удаляем псевдоним для 'leads.organization_name'
# # #         delete_response = requests.delete(f"{BASE_URL}/api/aliases/leads/organization_name", headers=headers)
# # #         print_status(
# # #             delete_response.status_code == 204,
# # #             "Сервер успешно обработал запрос на удаление псевдонима (статус 204)."
# # #         )
# # #
# # #         # Снова запрашиваем все псевдонимы, чтобы проверить результат
# # #         get_after_delete_response = requests.get(f"{BASE_URL}/api/aliases/", headers=headers)
# # #         aliases_after_delete = get_after_delete_response.json()
# # #
# # #         print("Данные после удаления:", json.dumps(aliases_after_delete, indent=2, ensure_ascii=False))
# # #
# # #         # Проверяем, что псевдоним для 'leads' исчез, а для 'candidates' остался
# # #         print_status(
# # #             "leads" not in aliases_after_delete,
# # #             "Псевдоним для 'leads' успешно удален из списка."
# # #         )
# # #         print_status(
# # #             "candidates" in aliases_after_delete,
# # #             "Псевдоним для 'candidates' остался на месте."
# # #         )
# # #
# # #         # --- ШАГ 6: ПРОВЕРКА ОБРАБОТКИ ОШИБОК ---
# # #         print("-" * 50)
# # #         print("6. ПРОВЕРКА ОБРАБОТКИ ОШИБОК")
# # #
# # #         # Пытаемся удалить несуществующий псевдоним
# # #         non_existent_delete = requests.delete(f"{BASE_URL}/api/aliases/non_existent_table/non_existent_attr",
# # #                                               headers=headers)
# # #         print_status(
# # #             non_existent_delete.status_code == 404,
# # #             "Сервер корректно вернул ошибку 404 при попытке удалить несуществующий псевдоним."
# # #         )
# # #
# # #         print("-" * 50)
# # #         print("\n🎉 ВСЕ ТЕСТЫ ДЛЯ API ПСЕВДОНИМОВ ПРОШЛИ УСПЕШНО! 🎉")
# # #
# # #     except requests.exceptions.HTTPError as e:
# # #         print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
# # #         print(f"URL запроса: {e.request.method} {e.request.url}")
# # #         if e.request.body:
# # #             try:
# # #                 body = json.loads(e.request.body)
# # #                 print(f"Тело запроса: {json.dumps(body, indent=2, ensure_ascii=False)}")
# # #             except:
# # #                 print(f"Тело запроса: {e.request.body}")
# # #         print(f"Статус код: {e.response.status_code}")
# # #         print(f"Ответ сервера: {e.response.text}")
# # #     except Exception as e:
# # #         print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА")
# # #         print(f"Ошибка: {e}")
# # #
# # #
# # # # Запускаем наш тест
# # # if __name__ == "__main__":
# # #     run_aliases_test()
# #
# #
# # # test_table_aliases.py
# # import requests
# # import json
# # import time
# #
# # # --- НАСТРОЙКИ ---
# # # BASE_URL = "http://127.0.0.1:8005"
# # BASE_URL = "http://89.111.169.47:8005"  # Или http://89.111.169.47:8005, если тестируете на сервере
# #
# # # ВАЖНО: Укажите здесь тот же токен, что и в вашем .env файле
# # CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # # -----------------
# #
# # UNIQUE_ID = int(time.time())
# #
# #
# # def print_status(ok, message):
# #     """Выводит статус операции."""
# #     if ok:
# #         print(f"✅ [SUCCESS] {message}")
# #     else:
# #         print(f"❌ [FAILURE] {message}")
# #         exit(1)
# #
# #
# # def run_table_aliases_test():
# #     """
# #     Выполняет полный цикл тестирования API для псевдонимов таблиц.
# #     """
# #     token = None
# #     headers = {}
# #
# #     try:
# #         # --- ШАГ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ ---
# #         print("-" * 50)
# #         print("1. РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ")
# #         user_email = f"table_alias_tester_{UNIQUE_ID}@example.com"
# #         password = "password123"
# #         reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
# #         requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
# #
# #         auth_payload_form = {'username': user_email, 'password': password}
# #         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
# #         auth_response.raise_for_status()
# #         token = auth_response.json()['access_token']
# #         headers = {'Authorization': f'Bearer {token}'}
# #         print_status(True, "Успешно зарегистрирован и получен токен.")
# #
# #         # --- ШАГ 2: ПОДГОТОВКА СРЕДЫ (СОЗДАНИЕ КАСТОМНОЙ ТАБЛИЦЫ) ---
# #         print("-" * 50)
# #         print("2. ПОДГОТОВКА СРЕДЫ")
# #         entity_payload = {"name": f"custom_projects_{UNIQUE_ID}", "display_name": "Проекты"}
# #         response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=entity_payload)
# #         response.raise_for_status()
# #         print_status(True, f"Создана кастомная таблица '{entity_payload['name']}'.")
# #
# #         # --- ШАГ 3: УСТАНОВКА ПСЕВДОНИМОВ ---
# #         print("-" * 50)
# #         print("3. УСТАНОВКА ПСЕВДОНИМОВ (POST /api/aliases/tables)")
# #
# #         # 3.1. Устанавливаем псевдоним для стандартной таблицы 'leads'
# #         alias1_payload = {"table_name": "leads", "display_name": "Воронка Продаж"}
# #         response1 = requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers, json=alias1_payload)
# #         response1.raise_for_status()
# #         print_status(True, "Установлен псевдоним для таблицы 'leads'.")
# #
# #         # 3.2. Устанавливаем псевдоним для кастомной таблицы
# #         alias2_payload = {"table_name": entity_payload['name'], "display_name": "Наши Проекты"}
# #         response2 = requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers, json=alias2_payload)
# #         response2.raise_for_status()
# #         print_status(True, f"Установлен псевдоним для таблицы '{entity_payload['name']}'.")
# #
# #         # --- ШАГ 4: ПОЛУЧЕНИЕ И ПРОВЕРКА ВСЕХ ПСЕВДОНИМОВ ---
# #         print("-" * 50)
# #         print("4. ПРОВЕРКА ПОЛУЧЕНИЯ ВСЕХ ПСЕВДОНИМОВ (GET /api/aliases/tables)")
# #
# #         get_response = requests.get(f"{BASE_URL}/api/aliases/tables", headers=headers)
# #         get_response.raise_for_status()
# #         all_aliases = get_response.json()
# #
# #         print("Полученные данные:", json.dumps(all_aliases, indent=2, ensure_ascii=False))
# #
# #         print_status(len(all_aliases) == 2, f"Получено {len(all_aliases)} псевдонимов, как и ожидалось.")
# #         print_status(all_aliases.get("leads") == alias1_payload["display_name"], "Псевдоним для 'leads' корректен.")
# #         print_status(all_aliases.get(entity_payload['name']) == alias2_payload["display_name"],
# #                      "Псевдоним для кастомной таблицы корректен.")
# #
# #         # --- ШАГ 5: ОБНОВЛЕНИЕ ПСЕВДОНИМА ---
# #         print("-" * 50)
# #         print("5. ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕГО ПСЕВДОНИМА")
# #
# #         update_payload = {"table_name": "leads", "display_name": "Новые Заявки"}
# #         update_response = requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers, json=update_payload)
# #         update_response.raise_for_status()
# #
# #         get_after_update = requests.get(f"{BASE_URL}/api/aliases/tables", headers=headers).json()
# #         print_status(
# #             get_after_update.get("leads") == update_payload["display_name"],
# #             "Псевдоним для 'leads' успешно обновлен."
# #         )
# #
# #         # --- ШАГ 6: УДАЛЕНИЕ (СБРОС) ПСЕВДОНИМА ---
# #         print("-" * 50)
# #         print("6. ПРОВЕРКА УДАЛЕНИЯ ПСЕВДОНИМА (DELETE /api/aliases/tables/{table_name})")
# #
# #         delete_response = requests.delete(f"{BASE_URL}/api/aliases/tables/leads", headers=headers)
# #         print_status(
# #             delete_response.status_code == 204,
# #             "Сервер успешно обработал запрос на удаление (статус 204)."
# #         )
# #
# #         get_after_delete = requests.get(f"{BASE_URL}/api/aliases/tables", headers=headers).json()
# #         print("Данные после удаления:", json.dumps(get_after_delete, indent=2, ensure_ascii=False))
# #
# #         print_status("leads" not in get_after_delete, "Псевдоним для 'leads' успешно удален.")
# #         print_status(entity_payload['name'] in get_after_delete, "Псевдоним для кастомной таблицы остался.")
# #
# #         # --- ШАГ 7: ПРОВЕРКА ОБРАБОТКИ ОШИБОК ---
# #         print("-" * 50)
# #         print("7. ПРОВЕРКА ОБРАБОТКИ ОШИБОК")
# #
# #         non_existent_delete = requests.delete(f"{BASE_URL}/api/aliases/tables/non_existent_table", headers=headers)
# #         print_status(
# #             non_existent_delete.status_code == 404,
# #             "Сервер корректно вернул 404 при попытке удалить несуществующий псевдоним."
# #         )
# #
# #         print("-" * 50)
# #         print("\n🎉 ВСЕ ТЕСТЫ ДЛЯ ПСЕВДОНИМОВ ТАБЛИЦ ПРОШЛИ УСПЕШНО! 🎉")
# #
# #     except requests.exceptions.HTTPError as e:
# #         print(f"\n❌ ОШИБКА HTTP.")
# #         print(f"URL: {e.request.method} {e.request.url}")
# #         print(f"Статус: {e.response.status_code}")
# #         print(f"Ответ: {e.response.text}")
# #     except Exception as e:
# #         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
# #
# #
# # if __name__ == "__main__":
# #     run_table_aliases_test()
#
#
# # # test_alias_override.py
# # import requests
# # import json
# # import time
# #
# # # --- НАСТРОЙКИ ---
# # # Укажите адрес вашего запущенного API
# # # BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# # BASE_URL = "http://89.111.169.47:8005"  # Или http://89.111.169.47:8005, если тестируете на сервере
# #
# # # ВАЖНО: Укажите здесь тот же секретный токен, что и в вашем .env файле
# # CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # # -----------------
# #
# # # Генерируем уникальные имена для каждого запуска теста
# # UNIQUE_ID = int(time.time())
# #
# #
# # def print_status(ok, message):
# #     """Выводит красивый статус операции."""
# #     if ok:
# #         print(f"✅ [SUCCESS] {message}")
# #     else:
# #         print(f"❌ [FAILURE] {message}")
# #         # Немедленно завершаем скрипт при первой же ошибке
# #         exit(1)
# #
# #
# # def run_test():
# #     """
# #     Выполняет полный цикл тестирования:
# #     Создание -> Переименование -> Проверка.
# #     """
# #     headers = {}
# #     entity_type_id = None
# #     table_system_name = f"test_projects_{UNIQUE_ID}"
# #     attribute_system_name = "project_budget"
# #
# #     try:
# #         # --- ШАГ 1: АВТОРИЗАЦИЯ ---
# #         print("-" * 60)
# #         print("ШАГ 1: Регистрация и авторизация...")
# #         user_email = f"alias_override_tester_{UNIQUE_ID}@example.com"
# #         password = "password123"
# #
# #         reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
# #         reg_response = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
# #         reg_response.raise_for_status()
# #
# #         auth_payload_form = {'username': user_email, 'password': password}
# #         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
# #         auth_response.raise_for_status()
# #
# #         token = auth_response.json()['access_token']
# #         headers = {'Authorization': f'Bearer {token}'}
# #         print_status(True, "Успешно зарегистрирован и получен токен.")
# #
# #         # --- ШАГ 2: СОЗДАНИЕ ИСХОДНОЙ СТРУКТУРЫ ---
# #         print("-" * 60)
# #         print("ШАГ 2: Создание кастомной таблицы и колонки...")
# #
# #         # Создаем таблицу
# #         table_payload = {"name": table_system_name, "display_name": "Исходное Имя Таблицы"}
# #         response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_payload)
# #         response.raise_for_status()
# #         entity_type_id = response.json()['id']
# #         print(f" -> Создана таблица '{table_system_name}' с ID: {entity_type_id}")
# #
# #         # Создаем в ней колонку
# #         attr_payload = {"name": attribute_system_name, "display_name": "Исходный Бюджет", "value_type": "integer"}
# #         response = requests.post(f"{BASE_URL}/api/meta/entity-types/{entity_type_id}/attributes", headers=headers,
# #                                  json=attr_payload)
# #         response.raise_for_status()
# #         print(f" -> В таблицу добавлена колонка '{attribute_system_name}'")
# #         print_status(True, "Исходная структура успешно создана.")
# #
# #         # --- ШАГ 3: УСТАНОВКА ПСЕВДОНИМОВ ---
# #         print("-" * 60)
# #         print("ШАГ 3: Установка новых имен (псевдонимов)...")
# #
# #         # Определяем новые имена, которые мы хотим видеть
# #         new_table_display_name = "Проекты (с псевдонимом)"
# #         new_attribute_display_name = "Бюджет проекта (с псевдонимом)"
# #
# #         # Устанавливаем псевдоним для таблицы
# #         alias_table_payload = {"table_name": table_system_name, "display_name": new_table_display_name}
# #         response = requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers, json=alias_table_payload)
# #         response.raise_for_status()
# #         print(f" -> Таблица '{table_system_name}' переименована в '{new_table_display_name}'")
# #
# #         # Устанавливаем псевдоним для колонки
# #         alias_attr_payload = {"table_name": table_system_name, "attribute_name": attribute_system_name,
# #                               "display_name": new_attribute_display_name}
# #         response = requests.post(f"{BASE_URL}/api/aliases/", headers=headers, json=alias_attr_payload)
# #         response.raise_for_status()
# #         print(f" -> Колонка '{attribute_system_name}' переименована в '{new_attribute_display_name}'")
# #         print_status(True, "Псевдонимы успешно установлены.")
# #
# #         # --- ШАГ 4: ПРОВЕРКА РЕЗУЛЬТАТА ---
# #         print("-" * 60)
# #         print(f"ШАГ 4: Проверка результата через GET /api/meta/entity-types/{entity_type_id}")
# #
# #         response = requests.get(f"{BASE_URL}/api/meta/entity-types/{entity_type_id}", headers=headers)
# #         response.raise_for_status()
# #
# #         data = response.json()
# #         print("Получены следующие данные от сервера:")
# #         print(json.dumps(data, indent=2, ensure_ascii=False))
# #
# #         # Проверка имени таблицы
# #         print("\nПроверяем...")
# #         print_status(
# #             data.get('display_name') == new_table_display_name,
# #             f"Имя таблицы корректно: '{data.get('display_name')}'."
# #         )
# #
# #         # Проверка имени колонки
# #         found_attribute = next((attr for attr in data.get('attributes', []) if attr['name'] == attribute_system_name),
# #                                None)
# #
# #         print_status(found_attribute is not None, f"Колонка '{attribute_system_name}' найдена в ответе.")
# #
# #         if found_attribute:
# #             print_status(
# #                 found_attribute.get('display_name') == new_attribute_display_name,
# #                 f"Имя колонки корректно: '{found_attribute.get('display_name')}'."
# #             )
# #
# #         print("-" * 60)
# #         print("\n🎉🎉🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! API работает как ожидалось. 🎉🎉🎉\n")
# #
# #     except requests.exceptions.HTTPError as e:
# #         print(f"\n❌ ОШИБКА HTTP.")
# #         print(f"URL запроса: {e.request.method} {e.request.url}")
# #         if e.request.body:
# #             try:
# #                 # Пытаемся красиво напечатать тело запроса
# #                 body = json.loads(e.request.body)
# #                 print(f"Тело запроса: {json.dumps(body, indent=2, ensure_ascii=False)}")
# #             except:
# #                 print(f"Тело запроса: {e.request.body}")
# #         print(f"Статус код: {e.response.status_code}")
# #         print(f"Ответ сервера: {e.response.text}")
# #     except Exception as e:
# #         print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
# #
# #
# # # Запускаем наш тест
# # if __name__ == "__main__":
# #     run_test()
#
#
# # test_full_list_alias_fix.py
# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ ---
# # Укажите адрес вашего запущенного API
# BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
#
# # ВАЖНО: Укажите здесь тот же секретный токен, что и в вашем .env файле
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # -----------------
#
# UNIQUE_ID = int(time.time())
#
#
# def print_status(ok, message):
#     """Выводит красивый статус операции."""
#     if ok:
#         print(f"✅ [PASS] {message}")
#     else:
#         print(f"❌ [FAIL] {message}")
#         exit(1)
#
#
# def run_full_list_alias_test():
#     """
#     Тестирует, что GET /api/meta/entity-types (список)
#     корректно возвращает псевдонимы для таблиц и их колонок.
#     """
#     headers = {}
#
#     # Системные имена, которые не меняются
#     projects_system_name = f"test_projects_{UNIQUE_ID}"
#     tasks_system_name = f"test_tasks_{UNIQUE_ID}"
#
#     try:
#         # --- ШАГ 1: АВТОРИЗАЦИЯ ---
#         print("-" * 60)
#         print("ШАГ 1: Регистрация и авторизация...")
#         user_email = f"list_alias_tester_{UNIQUE_ID}@example.com"
#         password = "password123"
#         reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
#         requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#         auth_payload_form = {'username': user_email, 'password': password}
#         token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form).json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#         print_status(True, "Авторизация успешна.")
#
#         # --- ШАГ 2: СОЗДАНИЕ СТРУКТУРЫ С ИСХОДНЫМИ ИМЕНАМИ ---
#         print("\n" + "-" * 60)
#         print("ШАГ 2: Создание двух тестовых таблиц с колонками...")
#         # Таблица 1: Проекты
#         p_payload = {"name": projects_system_name, "display_name": "Исходные Проекты"}
#         p_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=p_payload).json()['id']
#         requests.post(f"{BASE_URL}/api/meta/entity-types/{p_id}/attributes", headers=headers,
#                       json={"name": "budget", "display_name": "Исходный Бюджет",
#                             "value_type": "integer"}).raise_for_status()
#         print(f" -> Создана таблица 'Проекты' ({projects_system_name})")
#         # Таблица 2: Задачи
#         t_payload = {"name": tasks_system_name, "display_name": "Исходные Задачи"}
#         t_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=t_payload).json()['id']
#         requests.post(f"{BASE_URL}/api/meta/entity-types/{t_id}/attributes", headers=headers,
#                       json={"name": "executor", "display_name": "Исходный Исполнитель",
#                             "value_type": "string"}).raise_for_status()
#         print(f" -> Создана таблица 'Задачи' ({tasks_system_name})")
#         print_status(True, "Исходная структура создана.")
#
#         # --- ШАГ 3: УСТАНОВКА ПСЕВДОНИМОВ ---
#         print("\n" + "-" * 60)
#         print("ШАГ 3: Установка новых имен (псевдонимов)...")
#         NEW_PROJECTS_NAME = "Мои Проекты (алиас)"
#         NEW_BUDGET_NAME = "Денежки (алиас)"
#         NEW_TASKS_NAME = "Мои Задачи (алиас)"
#         NEW_EXECUTOR_NAME = "Ответственный (алиас)"
#
#         # Переименовываем таблицы
#         requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers,
#                       json={"table_name": projects_system_name, "display_name": NEW_PROJECTS_NAME}).raise_for_status()
#         requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers,
#                       json={"table_name": tasks_system_name, "display_name": NEW_TASKS_NAME}).raise_for_status()
#         # Переименовываем колонки
#         requests.post(f"{BASE_URL}/api/aliases/", headers=headers,
#                       json={"table_name": projects_system_name, "attribute_name": "budget",
#                             "display_name": NEW_BUDGET_NAME}).raise_for_status()
#         requests.post(f"{BASE_URL}/api/aliases/", headers=headers,
#                       json={"table_name": tasks_system_name, "attribute_name": "executor",
#                             "display_name": NEW_EXECUTOR_NAME}).raise_for_status()
#         print_status(True, "Все псевдонимы успешно установлены.")
#
#         # --- ШАГ 4: ГЛАВНАЯ ПРОВЕРКА ---
#         print("\n" + "-" * 60)
#         print("ШАГ 4: Проверка результата через GET /api/meta/entity-types (список)")
#
#         response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
#         response.raise_for_status()
#         all_tables_data = response.json()
#
#         print("Получены следующие данные от сервера:")
#         print(json.dumps(all_tables_data, indent=2, ensure_ascii=False))
#
#         # Ищем наши таблицы в общем списке
#         projects_data = next((t for t in all_tables_data if t['name'] == projects_system_name), None)
#         tasks_data = next((t for t in all_tables_data if t['name'] == tasks_system_name), None)
#
#         print_status(projects_data is not None, "Таблица 'Проекты' найдена в общем списке.")
#         print_status(tasks_data is not None, "Таблица 'Задачи' найдена в общем списке.")
#
#         # Проверяем псевдонимы для "Проектов"
#         if projects_data:
#             print("\nПроверяем таблицу 'Проекты':")
#             print_status(projects_data['display_name'] == NEW_PROJECTS_NAME,
#                          f" -> Имя таблицы корректно: '{projects_data['display_name']}'")
#             budget_attr = next((a for a in projects_data['attributes'] if a['name'] == 'budget'), None)
#             print_status(budget_attr is not None, " -> Колонка 'budget' найдена.")
#             if budget_attr:
#                 print_status(budget_attr['display_name'] == NEW_BUDGET_NAME,
#                              f" -> Имя колонки корректно: '{budget_attr['display_name']}'")
#
#         # Проверяем псевдонимы для "Задач"
#         if tasks_data:
#             print("\nПроверяем таблицу 'Задачи':")
#             print_status(tasks_data['display_name'] == NEW_TASKS_NAME,
#                          f" -> Имя таблицы корректно: '{tasks_data['display_name']}'")
#             executor_attr = next((a for a in tasks_data['attributes'] if a['name'] == 'executor'), None)
#             print_status(executor_attr is not None, " -> Колонка 'executor' найдена.")
#             if executor_attr:
#                 print_status(executor_attr['display_name'] == NEW_EXECUTOR_NAME,
#                              f" -> Имя колонки корректно: '{executor_attr['display_name']}'")
#
#         print("\n" + "-" * 60)
#         print("🎉🎉🎉 ФИНАЛЬНЫЙ ФИКС ПОДТВЕРЖДЕН! API работает как ожидалось. 🎉🎉🎉")
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
# # Запускаем наш тест
# if __name__ == "__main__":
#     run_full_list_alias_test()
#
#
# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
#
# BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
#
# # Секретный токен для регистрации новых пользователей
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
#
# # ----------------------------------------------------
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
# def register_and_login(email, password, full_name):
#     """Вспомогательная функция для регистрации и входа."""
#     # 1. Регистрация
#     reg_payload = {
#         "email": email,
#         "password": password,
#         "full_name": full_name,
#         "registration_token": CORRECT_REGISTRATION_TOKEN
#     }
#     reg_response = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
#     if reg_response.status_code != 201:
#         raise Exception(f"Ошибка регистрации для {email}: {reg_response.text}")
#
#     # 2. Вход
#     auth_payload = {'username': email, 'password': password}
#     auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
#     auth_response.raise_for_status()
#
#     token = auth_response.json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
#
# def create_custom_table(headers, table_config):
#     """Вспомогательная функция для создания кастомной таблицы."""
#     response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config)
#     response.raise_for_status()
#     return response.json()
#
#
# def get_visible_tables(headers):
#     """Получает список видимых кастомных таблиц для текущего пользователя."""
#     response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
#     response.raise_for_status()
#     return response.json()
#
#
# def run_multi_tenancy_test():
#     try:
#         unique_id = int(time.time())
#
#         # --- КЛИЕНТ А ---
#         print_header("СОЗДАНИЕ КЛИЕНТА А И ЕГО ТАБЛИЦЫ")
#         user_a_email = f"user1@example.com"
#         user_a_password = "password_a"
#         user_a_headers = register_and_login(user_a_email, user_a_password, "Пользователь Альфа")
#         print(f" -> Пользователь '{user_a_email}' и его тенант созданы.")
#
#         table_a_config = {"name": f"alpha_projects_{unique_id}", "display_name": "Проекты Альфа"}
#         create_custom_table(user_a_headers, table_a_config)
#         print(f" -> Для клиента А создана таблица '{table_a_config['display_name']}'.")
#
#         # --- КЛИЕНТ Б ---
#         print_header("СОЗДАНИЕ КЛИЕНТА Б И ЕГО ТАБЛИЦЫ")
#         user_b_email = f"user2@example.com"
#         user_b_password = "password_b"
#         user_b_headers = register_and_login(user_b_email, user_b_password, "Пользователь Бета")
#         print(f" -> Пользователь '{user_b_email}' и его тенант созданы.")
#
#         table_b_config = {"name": f"beta_tasks_{unique_id}", "display_name": "Задачи Бета"}
#         create_custom_table(user_b_headers, table_b_config)
#         print(f" -> Для клиента Б создана таблица '{table_b_config['display_name']}'.")
#
#         # --- ПРОВЕРКА ИЗОЛЯЦИИ ---
#         print_header("ПРОВЕРКА ИЗОЛЯЦИИ ДАННЫХ")
#
#         # Проверяем, что видит Пользователь А
#         print(f"\nПроверяем видимость для {user_a_email}...")
#         visible_to_a = get_visible_tables(user_a_headers)
#         visible_names_a = {table['name'] for table in visible_to_a}
#
#         print(f" -> Пользователь А видит таблицы: {visible_names_a}")
#         print_status(len(visible_to_a) == 1, "Пользователь А видит ровно одну таблицу.")
#         print_status(table_a_config['name'] in visible_names_a, "Пользователь А видит свою таблицу 'Проекты Альфа'.")
#         print_status(table_b_config['name'] not in visible_names_a,
#                      "Пользователь А НЕ видит чужую таблицу 'Задачи Бета'.")
#
#         # Проверяем, что видит Пользователь Б
#         print(f"\nПроверяем видимость для {user_b_email}...")
#         visible_to_b = get_visible_tables(user_b_headers)
#         visible_names_b = {table['name'] for table in visible_to_b}
#
#         print(f" -> Пользователь Б видит таблицы: {visible_names_b}")
#         print_status(len(visible_to_b) == 1, "Пользователь Б видит ровно одну таблицу.")
#         print_status(table_b_config['name'] in visible_names_b, "Пользователь Б видит свою таблицу 'Задачи Бета'.")
#         print_status(table_a_config['name'] not in visible_names_b,
#                      "Пользователь Б НЕ видит чужую таблицу 'Проекты Альфа'.")
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ НА МУЛЬТИ-ТЕНАНТНОСТЬ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
#         print("Данные клиентов надежно изолированы.")
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
# if __name__ == "__main__":
#     run_multi_tenancy_test()


# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
#
# # BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# BASE_URL = "http://89.111.169.47:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
#
# # Секретный токен для регистрации новых пользователей
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
#
# # ----------------------------------------------------
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
# def register_and_login():
#     """Регистрирует нового пользователя и возвращает заголовки с токеном."""
#     unique_id = int(time.time())
#     email = f"attr_tester_{unique_id}@example.com"
#     password = "password123"
#
#     reg_payload = {"email": email, "password": password, "full_name": "Attributet Tester",
#                    "registration_token": CORRECT_REGISTRATION_TOKEN}
#     requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#
#     auth_payload = {'username': email, 'password': password}
#     token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
#
# def get_table_details(headers, table_id):
#     """Получает детальную информацию о таблице, включая ее атрибуты."""
#     response = requests.get(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers)
#     response.raise_for_status()
#     return response.json()
#
#
# def run_attribute_test():
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
#         headers = register_and_login()
#
#         table_config = {"name": f"candidates_{int(time.time())}", "display_name": "Кандидаты"}
#         table_response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config)
#         table_response.raise_for_status()
#         table_id = table_response.json()['id']
#         print_status(True, f"Создана тестовая таблица 'Кандидаты' с ID: {table_id}")
#
#         # --- ШАГ 2: СОЗДАНИЕ КОЛОНОК ---
#         print_header("ШАГ 2: СОЗДАНИЕ ТРЕХ КОЛОНОК")
#
#         attrs_to_create = [
#             {"name": "full_name", "display_name": "ФИО", "value_type": "string"},
#             {"name": "salary_expectation", "display_name": "Ожидаемая ЗП", "value_type": "integer"},
#             {"name": "contact_phone", "display_name": "Контактный телефон", "value_type": "string"},
#         ]
#
#         for attr in attrs_to_create:
#             url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
#             requests.post(url, headers=headers, json=attr).raise_for_status()
#             print(f" -> Создана колонка '{attr['display_name']}'")
#
#         # --- ШАГ 3: ПРОВЕРКА СОЗДАНИЯ ---
#         print_header("ШАГ 3: ПРОВЕРКА, ЧТО ВСЕ КОЛОНКИ СОЗДАНЫ")
#
#         table_details = get_table_details(headers, table_id)
#         # Отфильтровываем системные атрибуты (sms_*, phone_number, etc.)
#         custom_attributes = [attr for attr in table_details['attributes'] if
#                              not attr['name'].startswith('sms_') and attr['name'] not in (
#                              'phone_number', 'message_text', 'send_sms_trigger')]
#
#         print(f" -> В таблице найдено {len(custom_attributes)} пользовательских колонок.")
#         print_status(len(custom_attributes) == 3, "Количество созданных колонок совпадает с ожидаемым.")
#
#         created_attr_names = {attr['name'] for attr in custom_attributes}
#         print_status('salary_expectation' in created_attr_names, "Колонка 'salary_expectation' присутствует.")
#
#         # --- ШАГ 4: УДАЛЕНИЕ ОДНОЙ КОЛОНКИ ---
#         print_header("ШАГ 4: УДАЛЕНИЕ КОЛОНКИ 'contact_phone'")
#
#         # Находим ID колонки, которую хотим удалить
#         attr_to_delete = next((attr for attr in custom_attributes if attr['name'] == 'contact_phone'), None)
#         print_status(attr_to_delete is not None, "Найдена колонка 'contact_phone' для удаления.")
#
#         if attr_to_delete:
#             attr_id_to_delete = attr_to_delete['id']
#             url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes/{attr_id_to_delete}"
#             delete_response = requests.delete(url, headers=headers)
#
#             print_status(delete_response.status_code == 204, "Запрос на удаление прошел успешно (статус 204).")
#
#         # --- ШАГ 5: ФИНАЛЬНАЯ ПРОВЕРКА ---
#         print_header("ШАГ 5: ПРОВЕРКА, ЧТО КОЛОНКА УДАЛЕНА, А ОСТАЛЬНЫЕ НА МЕСТЕ")
#
#         final_table_details = get_table_details(headers, table_id)
#         final_custom_attributes = [attr for attr in final_table_details['attributes'] if
#                                    not attr['name'].startswith('sms_') and attr['name'] not in (
#                                    'phone_number', 'message_text', 'send_sms_trigger')]
#
#         print(f" -> В таблице осталось {len(final_custom_attributes)} пользовательских колонок.")
#         print_status(len(final_custom_attributes) == 2, "Итоговое количество колонок совпадает с ожидаемым.")
#
#         final_attr_names = {attr['name'] for attr in final_custom_attributes}
#         print_status('contact_phone' not in final_attr_names, "Колонка 'contact_phone' успешно удалена.")
#         print_status('full_name' in final_attr_names, "Колонка 'full_name' осталась на месте.")
#         print_status('salary_expectation' in final_attr_names, "Колонка 'salary_expectation' осталась на месте.")
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ ЖИЗНЕННОГО ЦИКЛА КОЛОНОК ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
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
# if __name__ == "__main__":
#     run_attribute_test()


# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
#
# # BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# BASE_URL = "http://89.111.169.47:8005"
#
# # Секретный токен для регистрации новых пользователей
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
#
# # ----------------------------------------------------
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
# def register_and_login():
#     """Регистрирует нового пользователя и возвращает заголовки с токеном."""
#     unique_id = int(time.time())
#     email = f"table_deleter_{unique_id}@example.com"
#     password = "password123"
#
#     reg_payload = {"email": email, "password": password, "full_name": "Table Deleter",
#                    "registration_token": CORRECT_REGISTRATION_TOKEN}
#     requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#
#     auth_payload = {'username': email, 'password': password}
#     token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
#
# def run_table_deletion_test():
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ДВУХ ТАБЛИЦ")
#         headers = register_and_login()
#
#         # Таблица 1 (для удаления)
#         table_to_delete_config = {"name": f"projects_to_delete_{int(time.time())}",
#                                   "display_name": "Проекты на удаление"}
#         response1 = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_to_delete_config)
#         response1.raise_for_status()
#         table_to_delete_id = response1.json()['id']
#         print(f" -> Создана таблица '{table_to_delete_config['display_name']}' с ID: {table_to_delete_id}")
#
#         # Таблица 2 (для проверки)
#         table_to_keep_config = {"name": f"tasks_to_keep_{int(time.time())}", "display_name": "Задачи для проверки"}
#         response2 = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_to_keep_config)
#         response2.raise_for_status()
#         table_to_keep_id = response2.json()['id']
#         print(f" -> Создана таблица '{table_to_keep_config['display_name']}' с ID: {table_to_keep_id}")
#
#         # --- ШАГ 2: ПРОВЕРКА СОЗДАНИЯ ---
#         list_response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
#         all_tables = list_response.json()
#         table_names = {t['name'] for t in all_tables}
#
#         print_status(
#             table_to_delete_config['name'] in table_names and table_to_keep_config['name'] in table_names,
#             "Обе таблицы присутствуют в общем списке."
#         )
#
#         # --- ШАГ 3: УДАЛЕНИЕ ОДНОЙ ТАБЛИЦЫ ---
#         print_header(f"ШАГ 3: УДАЛЕНИЕ ТАБЛИЦЫ ID={table_to_delete_id}")
#
#         delete_url = f"{BASE_URL}/api/meta/entity-types/{table_to_delete_id}"
#         delete_response = requests.delete(delete_url, headers=headers)
#
#         print_status(delete_response.status_code == 204, "Запрос на удаление таблицы прошел успешно (статус 204).")
#
#         # --- ШАГ 4: ФИНАЛЬНАЯ ПРОВЕРКА ---
#         print_header("ШАГ 4: ПРОВЕРКА ПОСЛЕДСТВИЙ УДАЛЕНИЯ")
#
#         # Проверка 1: Удаленная таблица должна возвращать 404
#         print(f" -> Проверяем доступ к удаленной таблице ID={table_to_delete_id}...")
#         deleted_table_response = requests.get(delete_url, headers=headers)
#         print_status(deleted_table_response.status_code == 404, "Удаленная таблица недоступна (получен статус 404).")
#
#         # Проверка 2: Вторая таблица должна остаться
#         print(f" -> Проверяем доступ к оставшейся таблице ID={table_to_keep_id}...")
#         kept_table_response = requests.get(f"{BASE_URL}/api/meta/entity-types/{table_to_keep_id}", headers=headers)
#         print_status(kept_table_response.status_code == 200, "Вторая таблица осталась на месте и доступна.")
#
#         # Проверка 3: Общий список должен содержать только одну таблицу
#         final_list_response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
#         final_all_tables = final_list_response.json()
#         final_table_names = {t['name'] for t in final_all_tables}
#
#         print(f" -> В общем списке остались таблицы: {final_table_names}")
#         print_status(len(final_all_tables) == 1, "В общем списке осталась только одна таблица.")
#         print_status(table_to_keep_config['name'] in final_table_names,
#                      "Оставшаяся таблица корректно присутствует в списке.")
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ НА УДАЛЕНИЕ ТАБЛИЦ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
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
# if __name__ == "__main__":
#     run_table_deletion_test()












# Что будет делать скрипт:
# Авторизуется под user@example.com.
# Получит список всех его разрешений с сервера (для наглядности).
# В цикле пройдет по списку ваших кастомных таблиц.
# Для каждой таблицы:
# Попытается получить список записей (GET /api/data/{table_name}).
# Попытается создать новую тестовую запись (POST /api/data/{table_name}).
# В конце выведет сводный отчет, какие действия разрешены, а какие — корректно заблокированы.
import requests
import json
from faker import Faker
import time
# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---

BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера

# --- Данные пользователя, чьи права мы проверяем ---
USER_EMAIL = "user1@example.com"
USER_PASSWORD = "password_a"
#         user_a_email = f"user1@example.com"
#         user_a_password = "password_a"
# --- Список системных имен таблиц для проверки ---
TABLES_TO_TEST = [
    "leads_custom",
    "archived_leads",
    "monitoring",
    "deals",
    "contracts",
    "founders_directors",
]

# ----------------------------------------------------------------------
fake = Faker('ru_RU')


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def run_permission_test():
    print_header(f"ПРОВЕРКА ПРАВ ДОСТУПА ДЛЯ ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")

    try:
        # --- ШАГ 1: АВТОРИЗАЦИЯ И ПОЛУЧЕНИЕ ПРАВ ---
        print("\n--- Шаг 1: Авторизация и получение списка реальных прав ---")
        auth_payload = {'username': USER_EMAIL, 'password': USER_PASSWORD}
        auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)

        if auth_response.status_code != 200:
            print(
                f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться. Проверьте email и пароль. Ответ: {auth_response.text}")
            return

        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        me_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        user_permissions = set(me_response.json().get("permissions", []))

        print(f"✅ Пользователь успешно авторизован.")
        print(f"✅ Сервер сообщает, что у пользователя {len(user_permissions)} прав:")
        for perm in sorted(list(user_permissions)):
            print(f"   - {perm}")

        # --- ШАГ 2: ЦИКЛ ПРОВЕРКИ ТАБЛИЦ ---
        for table_name in TABLES_TO_TEST:
            print_header(f"ПРОВЕРКА ТАБЛИЦЫ: '{table_name}'")

            # --- 2.1 Проверка на ПРОСМОТР (GET) ---
            print(f"\n -> 1. Попытка просмотра (GET /api/data/{table_name})")
            view_permission_needed = f"data:view:{table_name}"

            get_response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)

            if get_response.status_code == 200:
                print(f"   ✅ [УСПЕХ] Доступ на просмотр есть (статус 200).")
                if view_permission_needed not in user_permissions:
                    print(f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ есть, но права '{view_permission_needed}' нет в списке!")
            elif get_response.status_code == 403:
                print(f"   ✅ [КОРРЕКТНО ЗАБЛОКИРОВАНО] Доступ на просмотр запрещен (статус 403).")
                if view_permission_needed in user_permissions:
                    print(
                        f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ запрещен, хотя право '{view_permission_needed}' есть в списке!")
            else:
                print(f"   ❌ [ОШИБКА] Неожиданный статус ответа: {get_response.status_code} - {get_response.text}")

            # --- 2.2 Проверка на СОЗДАНИЕ (POST) ---
            print(f"\n -> 2. Попытка создания (POST /api/data/{table_name})")
            create_permission_needed = f"data:create:{table_name}"
            # Отправляем минимально необходимые данные
            post_payload = {"test_field": f"test_value_{int(time.time())}"}

            post_response = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=post_payload)

            # Для создания успешный статус - 201
            if post_response.status_code == 201:
                print(f"   ✅ [УСПЕХ] Доступ на создание есть (статус 201).")
                if create_permission_needed not in user_permissions:
                    print(f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ есть, но права '{create_permission_needed}' нет в списке!")
            elif post_response.status_code == 403:
                print(f"   ✅ [КОРРЕКТНО ЗАБЛОКИРОВАНО] Доступ на создание запрещен (статус 403).")
                if create_permission_needed in user_permissions:
                    print(
                        f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ запрещен, хотя право '{create_permission_needed}' есть в списке!")
            else:
                print(f"   ❌ [ОШИБКА] Неожиданный статус ответа: {post_response.status_code} - {post_response.text}")

        print("\n" + "=" * 60)
        print("ПРОВЕРКА ПРАВ ЗАВЕРШЕНА.")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА В СКРИПТЕ: {e}")


if __name__ == "__main__":
    run_permission_test()