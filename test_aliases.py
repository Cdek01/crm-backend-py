# # test_aliases.py
# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ ---
# BASE_URL = "http://127.0.0.1:8005"
#
# # BASE_URL = "http://89.111.169.47:8005"
#
#
# # ВАЖНО: Укажите здесь тот же токен, что и в вашем .env файле
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # -----------------
#
# UNIQUE_ID = int(time.time())
#
#
# def print_status(ok, message):
#     """Выводит статус операции."""
#     if ok:
#         print(f"✅ [SUCCESS] {message}")
#     else:
#         print(f"❌ [FAILURE] {message}")
#         # Завершаем скрипт при первой же ошибке
#         exit(1)
#
#
# def run_aliases_test():
#     """
#     Выполняет полный цикл тестирования API для псевдонимов.
#     """
#     token = None
#     headers = {}
#
#     try:
#         # --- ШАГ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ ---
#         print("-" * 50)
#         print("1. РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ")
#         user_email = f"alias_tester_{UNIQUE_ID}@example.com"
#         password = "password123"
#         reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
#         requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#
#         auth_payload_form = {'username': user_email, 'password': password}
#         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
#         auth_response.raise_for_status()
#         token = auth_response.json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#         print_status(True, "Успешно зарегистрирован и получен токен.")
#
#         # --- ШАГ 2: ПОДГОТОВКА СРЕДЫ (СОЗДАНИЕ КАСТОМНОЙ ТАБЛИЦЫ) ---
#         print("-" * 50)
#         print("2. ПОДГОТОВКА СРЕДЫ")
#         # Создаем кастомную таблицу "Кандидаты", чтобы было что переименовывать
#         entity_payload = {"name": "candidates", "display_name": "Кандидаты"}
#         response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=entity_payload)
#         response.raise_for_status()
#         entity_type_id = response.json()['id']
#         # Создаем в ней колонку
#         attr_payload = {"name": "expected_salary", "display_name": "Ожидаемая ЗП", "value_type": "integer"}
#         response = requests.post(f"{BASE_URL}/api/meta/entity-types/{entity_type_id}/attributes", headers=headers,
#                                  json=attr_payload)
#         response.raise_for_status()
#         print_status(True, "Создана кастомная таблица 'candidates' с колонкой 'expected_salary'.")
#
#         # --- ШАГ 3: УСТАНОВКА ПСЕВДОНИМОВ ---
#         print("-" * 50)
#         print("3. УСТАНОВКА ПСЕВДОНИМОВ (POST /api/aliases/)")
#
#         # 3.1. Устанавливаем псевдоним для стандартной таблицы 'leads'
#         alias1_payload = {
#             "table_name": "leads",
#             "attribute_name": "organization_name",
#             "display_name": "Название Компании-Клиента"
#         }
#         response1 = requests.post(f"{BASE_URL}/api/aliases/", headers=headers, json=alias1_payload)
#         response1.raise_for_status()
#         print_status(True, f"Установлен псевдоним для 'leads.organization_name'")
#
#         # 3.2. Устанавливаем псевдоним для кастомной таблицы 'candidates'
#         alias2_payload = {
#             "table_name": "candidates",
#             "attribute_name": "expected_salary",
#             "display_name": "Зарплатные ожидания (руб.)"
#         }
#         response2 = requests.post(f"{BASE_URL}/api/aliases/", headers=headers, json=alias2_payload)
#         response2.raise_for_status()
#         print_status(True, f"Установлен псевдоним для 'candidates.expected_salary'")
#
#         # --- ШАГ 4: ПОЛУЧЕНИЕ ВСЕХ ПСЕВДОНИМОВ ---
#         print("-" * 50)
#         print("4. ПРОВЕРКА ПОЛУЧЕНИЯ ВСЕХ ПСЕВДОНИМОВ (GET /api/aliases/)")
#
#         get_response = requests.get(f"{BASE_URL}/api/aliases/", headers=headers)
#         get_response.raise_for_status()
#         all_aliases = get_response.json()
#
#         print("Полученные данные:", json.dumps(all_aliases, indent=2, ensure_ascii=False))
#
#         # Проверяем, что оба псевдонима на месте и корректны
#         expected_aliases_count = 2
#         print_status(
#             len(all_aliases) == expected_aliases_count,
#             f"Получено {len(all_aliases)} таблицы с псевдонимами, ожидалось {expected_aliases_count}."
#         )
#         print_status(
#             all_aliases.get("leads", {}).get("organization_name") == alias1_payload["display_name"],
#             "Псевдоним для 'leads' корректен."
#         )
#         print_status(
#             all_aliases.get("candidates", {}).get("expected_salary") == alias2_payload["display_name"],
#             "Псевдоним для 'candidates' корректен."
#         )
#
#         # --- ШАГ 5: УДАЛЕНИЕ (СБРОС) ПСЕВДОНИМА ---
#         print("-" * 50)
#         print("5. ПРОВЕРКА УДАЛЕНИЯ ПСЕВДОНИМА (DELETE /api/aliases/{table}/{attr})")
#
#         # Удаляем псевдоним для 'leads.organization_name'
#         delete_response = requests.delete(f"{BASE_URL}/api/aliases/leads/organization_name", headers=headers)
#         print_status(
#             delete_response.status_code == 204,
#             "Сервер успешно обработал запрос на удаление псевдонима (статус 204)."
#         )
#
#         # Снова запрашиваем все псевдонимы, чтобы проверить результат
#         get_after_delete_response = requests.get(f"{BASE_URL}/api/aliases/", headers=headers)
#         aliases_after_delete = get_after_delete_response.json()
#
#         print("Данные после удаления:", json.dumps(aliases_after_delete, indent=2, ensure_ascii=False))
#
#         # Проверяем, что псевдоним для 'leads' исчез, а для 'candidates' остался
#         print_status(
#             "leads" not in aliases_after_delete,
#             "Псевдоним для 'leads' успешно удален из списка."
#         )
#         print_status(
#             "candidates" in aliases_after_delete,
#             "Псевдоним для 'candidates' остался на месте."
#         )
#
#         # --- ШАГ 6: ПРОВЕРКА ОБРАБОТКИ ОШИБОК ---
#         print("-" * 50)
#         print("6. ПРОВЕРКА ОБРАБОТКИ ОШИБОК")
#
#         # Пытаемся удалить несуществующий псевдоним
#         non_existent_delete = requests.delete(f"{BASE_URL}/api/aliases/non_existent_table/non_existent_attr",
#                                               headers=headers)
#         print_status(
#             non_existent_delete.status_code == 404,
#             "Сервер корректно вернул ошибку 404 при попытке удалить несуществующий псевдоним."
#         )
#
#         print("-" * 50)
#         print("\n🎉 ВСЕ ТЕСТЫ ДЛЯ API ПСЕВДОНИМОВ ПРОШЛИ УСПЕШНО! 🎉")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
#         print(f"URL запроса: {e.request.method} {e.request.url}")
#         if e.request.body:
#             try:
#                 body = json.loads(e.request.body)
#                 print(f"Тело запроса: {json.dumps(body, indent=2, ensure_ascii=False)}")
#             except:
#                 print(f"Тело запроса: {e.request.body}")
#         print(f"Статус код: {e.response.status_code}")
#         print(f"Ответ сервера: {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА")
#         print(f"Ошибка: {e}")
#
#
# # Запускаем наш тест
# if __name__ == "__main__":
#     run_aliases_test()


# test_table_aliases.py
import requests
import json
import time

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8005"
# ВАЖНО: Укажите здесь тот же токен, что и в вашем .env файле
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# -----------------

UNIQUE_ID = int(time.time())


def print_status(ok, message):
    """Выводит статус операции."""
    if ok:
        print(f"✅ [SUCCESS] {message}")
    else:
        print(f"❌ [FAILURE] {message}")
        exit(1)


def run_table_aliases_test():
    """
    Выполняет полный цикл тестирования API для псевдонимов таблиц.
    """
    token = None
    headers = {}

    try:
        # --- ШАГ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ ---
        print("-" * 50)
        print("1. РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ")
        user_email = f"table_alias_tester_{UNIQUE_ID}@example.com"
        password = "password123"
        reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
        requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()

        auth_payload_form = {'username': user_email, 'password': password}
        auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
        auth_response.raise_for_status()
        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print_status(True, "Успешно зарегистрирован и получен токен.")

        # --- ШАГ 2: ПОДГОТОВКА СРЕДЫ (СОЗДАНИЕ КАСТОМНОЙ ТАБЛИЦЫ) ---
        print("-" * 50)
        print("2. ПОДГОТОВКА СРЕДЫ")
        entity_payload = {"name": f"custom_projects_{UNIQUE_ID}", "display_name": "Проекты"}
        response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=entity_payload)
        response.raise_for_status()
        print_status(True, f"Создана кастомная таблица '{entity_payload['name']}'.")

        # --- ШАГ 3: УСТАНОВКА ПСЕВДОНИМОВ ---
        print("-" * 50)
        print("3. УСТАНОВКА ПСЕВДОНИМОВ (POST /api/aliases/tables)")

        # 3.1. Устанавливаем псевдоним для стандартной таблицы 'leads'
        alias1_payload = {"table_name": "leads", "display_name": "Воронка Продаж"}
        response1 = requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers, json=alias1_payload)
        response1.raise_for_status()
        print_status(True, "Установлен псевдоним для таблицы 'leads'.")

        # 3.2. Устанавливаем псевдоним для кастомной таблицы
        alias2_payload = {"table_name": entity_payload['name'], "display_name": "Наши Проекты"}
        response2 = requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers, json=alias2_payload)
        response2.raise_for_status()
        print_status(True, f"Установлен псевдоним для таблицы '{entity_payload['name']}'.")

        # --- ШАГ 4: ПОЛУЧЕНИЕ И ПРОВЕРКА ВСЕХ ПСЕВДОНИМОВ ---
        print("-" * 50)
        print("4. ПРОВЕРКА ПОЛУЧЕНИЯ ВСЕХ ПСЕВДОНИМОВ (GET /api/aliases/tables)")

        get_response = requests.get(f"{BASE_URL}/api/aliases/tables", headers=headers)
        get_response.raise_for_status()
        all_aliases = get_response.json()

        print("Полученные данные:", json.dumps(all_aliases, indent=2, ensure_ascii=False))

        print_status(len(all_aliases) == 2, f"Получено {len(all_aliases)} псевдонимов, как и ожидалось.")
        print_status(all_aliases.get("leads") == alias1_payload["display_name"], "Псевдоним для 'leads' корректен.")
        print_status(all_aliases.get(entity_payload['name']) == alias2_payload["display_name"],
                     "Псевдоним для кастомной таблицы корректен.")

        # --- ШАГ 5: ОБНОВЛЕНИЕ ПСЕВДОНИМА ---
        print("-" * 50)
        print("5. ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕГО ПСЕВДОНИМА")

        update_payload = {"table_name": "leads", "display_name": "Новые Заявки"}
        update_response = requests.post(f"{BASE_URL}/api/aliases/tables", headers=headers, json=update_payload)
        update_response.raise_for_status()

        get_after_update = requests.get(f"{BASE_URL}/api/aliases/tables", headers=headers).json()
        print_status(
            get_after_update.get("leads") == update_payload["display_name"],
            "Псевдоним для 'leads' успешно обновлен."
        )

        # --- ШАГ 6: УДАЛЕНИЕ (СБРОС) ПСЕВДОНИМА ---
        print("-" * 50)
        print("6. ПРОВЕРКА УДАЛЕНИЯ ПСЕВДОНИМА (DELETE /api/aliases/tables/{table_name})")

        delete_response = requests.delete(f"{BASE_URL}/api/aliases/tables/leads", headers=headers)
        print_status(
            delete_response.status_code == 204,
            "Сервер успешно обработал запрос на удаление (статус 204)."
        )

        get_after_delete = requests.get(f"{BASE_URL}/api/aliases/tables", headers=headers).json()
        print("Данные после удаления:", json.dumps(get_after_delete, indent=2, ensure_ascii=False))

        print_status("leads" not in get_after_delete, "Псевдоним для 'leads' успешно удален.")
        print_status(entity_payload['name'] in get_after_delete, "Псевдоним для кастомной таблицы остался.")

        # --- ШАГ 7: ПРОВЕРКА ОБРАБОТКИ ОШИБОК ---
        print("-" * 50)
        print("7. ПРОВЕРКА ОБРАБОТКИ ОШИБОК")

        non_existent_delete = requests.delete(f"{BASE_URL}/api/aliases/tables/non_existent_table", headers=headers)
        print_status(
            non_existent_delete.status_code == 404,
            "Сервер корректно вернул 404 при попытке удалить несуществующий псевдоним."
        )

        print("-" * 50)
        print("\n🎉 ВСЕ ТЕСТЫ ДЛЯ ПСЕВДОНИМОВ ТАБЛИЦ ПРОШЛИ УСПЕШНО! 🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP.")
        print(f"URL: {e.request.method} {e.request.url}")
        print(f"Статус: {e.response.status_code}")
        print(f"Ответ: {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


if __name__ == "__main__":
    run_table_aliases_test()