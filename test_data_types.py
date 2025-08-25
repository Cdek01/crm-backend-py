# # import requests
# # import json
# # import time
# # from datetime import datetime, timedelta
# #
# # # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
# #
# # BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# #
# # # --- Данные СУЩЕСТВУЮЩЕГО пользователя ---
# # USER_EMAIL = "user-b@example.com"
# # USER_PASSWORD = "password-b"
# #
# #
# #
# # # ----------------------------------------------------
# #
# # # --- Вспомогательные функции ---
# # def print_status(ok, message):
# #     if ok:
# #         print(f"✅ [PASS] {message}")
# #     else:
# #         print(f"❌ [FAIL] {message}"); exit(1)
# #
# #
# # def print_header(title):
# #     print("\n" + "=" * 60)
# #     print(f" {title} ".center(60, "="))
# #     print("=" * 60)
# #
# #
# # def login(email, password):
# #     """
# #     Авторизуется под существующим пользователем.
# #     Возвращает словарь с заголовками для аутентификации.
# #     """
# #     auth_payload = {'username': email, 'password': password}
# #     auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
# #     auth_response.raise_for_status()  # Выбросит исключение, если авторизация не удалась
# #     token = auth_response.json()['access_token']
# #     return {'Authorization': f'Bearer {token}'}
# #
# #
# # # --- ОСНОВНОЙ ТЕСТ ---
# # def run_data_types_test():
# #     try:
# #         # --- ШАГ 1: ПОДГОТОВКА ---
# #         print_header("ШАГ 1: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТИПИЗИРОВАННОЙ ТАБЛИЦЫ")
# #
# #         # Используем простую функцию входа
# #         headers = login(USER_EMAIL, USER_PASSWORD)
# #         print(f" -> Успешная авторизация под пользователем: {USER_EMAIL}")
# #
# #         table_name = f"typed_assets_{int(time.time())}"
# #         table_config = {"name": table_name, "display_name": "Типизированные Активы"}
# #         table_id_response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config)
# #         table_id_response.raise_for_status()
# #         table_id = table_id_response.json()['id']
# #
# #         attributes = [
# #             {"name": "asset_name", "display_name": "Название", "value_type": "string"},
# #             {"name": "inventory_number", "display_name": "Инв. номер", "value_type": "integer"},
# #             {"name": "cost", "display_name": "Стоимость", "value_type": "float"},
# #             {"name": "purchase_date", "display_name": "Дата покупки", "value_type": "date"},
# #             {"name": "is_active", "display_name": "Активен", "value_type": "boolean"},
# #         ]
# #         for attr in attributes:
# #             requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
# #                           json=attr).raise_for_status()
# #
# #         print_status(True, f"Создана таблица '{table_name}' со всеми типами колонок.")
# #
# #         # --- ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ЗАПИСИ ---
# #         print_header("ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ТИПИЗИРОВАННОЙ ЗАПИСИ")
# #
# #         date_value = datetime.now()
# #         record_payload = {
# #             "asset_name": "Ноутбук",
# #             "inventory_number": 10512,
# #             "cost": 1500.99,
# #             "purchase_date": date_value.isoformat(),
# #             "is_active": True
# #         }
# #         create_resp = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=record_payload)
# #         create_resp.raise_for_status()
# #         created_record = create_resp.json()[0]
# #         record_id = created_record['id']
# #
# #         print(f" -> Создана запись с ID: {record_id}")
# #
# #         # Проверяем типы и значения
# #         print_status(created_record.get('asset_name') == "Ноутбук", "Тип 'string' сохранился корректно.")
# #         print_status(created_record.get('inventory_number') == 10512, "Тип 'integer' сохранился корректно.")
# #         print_status(created_record.get('cost') == 1500.99, "Тип 'float' сохранился корректно.")
# #         print_status(created_record.get('is_active') is True, "Тип 'boolean' сохранился корректно.")
# #         print_status(
# #             created_record.get('purchase_date', '').startswith(date_value.isoformat()[:19]),
# #             "Тип 'date' сохранился корректно."
# #         )
# #
# #         # --- ШАГ 3: ПРОВЕРКА СОРТИРОВКИ ПО РАЗНЫМ ТИПАМ ---
# #         print_header("ШАГ 3: ПРОВЕРКА СОРТИРОВКИ ПО ТИПИЗИРОВАННЫМ ПОЛЯМ")
# #
# #         # Добавим еще две записи для сортировки
# #         requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={
# #             "asset_name": "Стол", "inventory_number": 500, "cost": 350.0,
# #             "purchase_date": (datetime.now() - timedelta(days=10)).isoformat(), "is_active": True
# #         })
# #         requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={
# #             "asset_name": "Кресло", "inventory_number": 20000, "cost": 500.50,
# #             "purchase_date": (datetime.now() + timedelta(days=5)).isoformat(), "is_active": False
# #         })
# #
# #         # Проверяем сортировку по float
# #         params = {"sort_by": "cost", "sort_order": "desc"}
# #         resp = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)
# #         resp.raise_for_status()
# #         sorted_by_cost = [item.get('cost') for item in resp.json()]
# #         print(f" -> Сортировка по стоимости (desc): {sorted_by_cost}")
# #         print_status(sorted_by_cost == [1500.99, 500.50, 350.0], "Сортировка по 'float' работает.")
# #
# #         # Проверяем сортировку по boolean
# #         params = {"sort_by": "is_active", "sort_order": "desc"}
# #         resp = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)
# #         resp.raise_for_status()
# #         sorted_by_active = [item.get('is_active') for item in resp.json()]
# #         print(f" -> Сортировка по активности (desc): {sorted_by_active}")
# #         print_status(sorted_by_active == [True, True, False], "Сортировка по 'boolean' работает.")
# #
# #         print("\n" + "=" * 60)
# #         print("🎉🎉🎉 ТЕСТ ТИПОВ ДАННЫХ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
# #
# #     except requests.exceptions.HTTPError as e:
# #         print(f"\n❌ ОШИБКА HTTP.")
# #         print(f"   URL: {e.request.method} {e.request.url}")
# #         print(f"   Статус: {e.response.status_code}")
# #         print(f"   Ответ: {e.response.text}")
# #     except Exception as e:
# #         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
# #
# #
# # if __name__ == "__main__":
# #     run_data_types_test()
#
#
# import requests
# import json
# import time
# from datetime import datetime, timedelta
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
# BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005"
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
#
# # -----------------
#
# # --- Вспомогательные функции ---
# def print_status(ok, message):
#     if ok:
#         print(f"✅ [PASS] {message}")
#     else:
#         print(f"❌ [FAIL] {message}"); exit(1)
#
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
#
# def register_and_login(email, password, full_name):
#     """
#     Регистрирует нового пользователя (если его нет) и затем входит в систему.
#     Возвращает словарь с заголовками для аутентификации.
#     """
#     reg_payload = {
#         "email": email, "password": password, "full_name": full_name,
#         "registration_token": CORRECT_REGISTRATION_TOKEN
#     }
#     reg_response = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
#     if reg_response.status_code not in [201, 400]: reg_response.raise_for_status()
#     if reg_response.status_code == 400 and "уже существует" not in reg_response.text: reg_response.raise_for_status()
#
#     auth_payload = {'username': email, 'password': password}
#     auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
#     auth_response.raise_for_status()
#     token = auth_response.json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
#
# # --- ОСНОВНОЙ ТЕСТ ---
# def run_data_types_test():
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("ШАГ 1: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТИПИЗИРОВАННОЙ ТАБЛИЦЫ")
#
#         unique_id = int(time.time())
#         test_email = f"datatype_tester_{unique_id}@example.com"
#         headers = register_and_login(test_email, "password123", "DataType Tester")
#         print(f" -> Успешная регистрация и авторизация под: {test_email}")
#
#         table_name = f"typed_assets_{unique_id}"
#         table_config = {"name": table_name, "display_name": "Типизированные Активы"}
#         table_id_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config)
#         table_id = table_id_resp.json()['id']
#
#         attributes = [
#             {"name": "asset_name", "display_name": "Название", "value_type": "string"},
#             {"name": "inventory_number", "display_name": "Инв. номер", "value_type": "integer"},
#             {"name": "cost", "display_name": "Стоимость", "value_type": "float"},
#             {"name": "purchase_date", "display_name": "Дата покупки", "value_type": "date"},
#             {"name": "is_active", "display_name": "Активен", "value_type": "boolean"},
#         ]
#         for attr in attributes:
#             requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
#                           json=attr).raise_for_status()
#
#         print_status(True, f"Создана таблица '{table_name}' со всеми типами колонок.")
#
#         # --- ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ЗАПИСИ ---
#         print_header("ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ТИПИЗИРОВАННОЙ ЗАПИСИ")
#
#         date_value = datetime.now()
#         record_payload = {
#             "asset_name": "Ноутбук", "inventory_number": 10512, "cost": 1500.99,
#             "purchase_date": date_value.isoformat(), "is_active": True
#         }
#         create_resp = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=record_payload)
#         create_resp.raise_for_status()
#         created_record = create_resp.json()[0]
#         record_id = created_record['id']
#
#         print(f" -> Создана запись с ID: {record_id}")
#
#         # Проверка типов и значений
#         print_status(created_record.get('asset_name') == "Ноутбук", "Тип 'string' сохранился корректно.")
#         print_status(created_record.get('inventory_number') == 10512, "Тип 'integer' сохранился корректно.")
#         print_status(created_record.get('cost') == 1500.99, "Тип 'float' сохранился корректно.")
#         print_status(created_record.get('is_active') is True, "Тип 'boolean' сохранился корректно.")
#         print_status(created_record.get('purchase_date', '').startswith(date_value.isoformat()[:19]),
#                      "Тип 'date' сохранился корректно.")
#
#         # Проверка системных полей
#         print_status(created_record.get('created_at') is not None, "Системное поле 'created_at' заполнено.")
#         print_status(created_record.get('updated_at') is None,
#                      "Системное поле 'updated_at' пустое при создании (это правильно).")
#
#         # --- ШАГ 3: ПРОВЕРКА СОРТИРОВКИ И ОБНОВЛЕНИЯ ---
#         print_header("ШАГ 3: ПРОВЕРКА СОРТИРОВКИ И ОБНОВЛЕНИЯ")
#
#         requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={
#             "asset_name": "Стол", "inventory_number": 500, "cost": 350.0,
#             "purchase_date": (datetime.now() - timedelta(days=10)).isoformat(), "is_active": True
#         })
#         requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={
#             "asset_name": "Кресло", "inventory_number": 20000, "cost": 500.50,
#             "purchase_date": (datetime.now() + timedelta(days=5)).isoformat(), "is_active": False
#         })
#
#         params = {"sort_by": "cost", "sort_order": "desc"}
#         resp = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)
#         sorted_by_cost = [item.get('cost') for item in resp.json()]
#         print(f" -> Сортировка по стоимости (desc): {sorted_by_cost}")
#         print_status(sorted_by_cost == [1500.99, 500.50, 350.0], "Сортировка по 'float' работает.")
#
#         print("\n -> Проверяем обновление поля 'updated_at'...")
#         time.sleep(1)  # Небольшая пауза, чтобы время обновления гарантированно отличалось
#         update_payload = {"asset_name": "Ноутбук (обновлено)"}
#         requests.put(f"{BASE_URL}/api/data/{table_name}/{record_id}", headers=headers,
#                      json=update_payload).raise_for_status()
#
#         updated_record_resp = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_id}", headers=headers).json()
#
#         print_status(updated_record_resp.get('updated_at') is not None,
#                      "Системное поле 'updated_at' заполнилось после обновления.")
#         print_status(
#             updated_record_resp.get('updated_at') > updated_record_resp.get('created_at'),
#             "Время обновления позже времени создания."
#         )
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ ТИПОВ ДАННЫХ И СИСТЕМНЫХ ПОЛЕЙ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP.")
#         print(f"   URL: {e.request.method} {e.request.url}")
#         print(f"   Статус: {e.response.status_code}")
#         print(f"   Ответ: {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
#
#
# if __name__ == "__main__":
#     run_data_types_test()


import requests
import json
import time

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
# BASE_URL = "http://127.0.0.1:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
BASE_URL = "http://89.111.169.47:8005"

# -----------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}"); exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def register_and_login(email, password, full_name):
    """
    Регистрирует нового пользователя (если его нет) и затем входит в систему.
    Возвращает словарь с заголовками для аутентификации.
    """
    reg_payload = {
        "email": email, "password": password, "full_name": full_name,
        "registration_token": CORRECT_REGISTRATION_TOKEN
    }
    reg_response = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    if reg_response.status_code not in [201, 400]: reg_response.raise_for_status()
    if reg_response.status_code == 400 and "уже существует" not in reg_response.text: reg_response.raise_for_status()

    auth_payload = {'username': email, 'password': password}
    auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
    auth_response.raise_for_status()
    token = auth_response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}

def get_table_details(headers, table_id):
    """Получает детальную информацию о таблице, включая ее атрибуты."""
    response = requests.get(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers)
    response.raise_for_status()
    return response.json()


# --- ОСНОВНОЙ ТЕСТ ---
def run_ordering_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ С КОЛОНКАМИ")
        headers = register_and_login()

        table_name = f"assets_order_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Активы"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        # Создаем колонки и сразу собираем их ID и имена
        created_attributes = {}  # Словарь {name: id}
        attributes_to_create = [
            {"name": "title", "display_name": "Название", "value_type": "string"},
            {"name": "price", "display_name": "Цена", "value_type": "float"},
            {"name": "status", "display_name": "Статус", "value_type": "string"},
        ]
        for attr in attributes_to_create:
            url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
            resp = requests.post(url, headers=headers, json=attr).json()
            created_attributes[resp['name']] = resp['id']

        print_status(True, f"Создана таблица '{table_name}' с 3 колонками.")

        # --- ШАГ 2: ПРОВЕРКА ИСХОДНОГО ПОРЯДКА ---
        print_header("ШАГ 2: ПРОВЕРКА ИСХОДНОГО ПОРЯДКА (ПО УМОЛЧАНИЮ)")

        initial_details = get_table_details(headers, table_id)
        # Отфильтровываем системные атрибуты
        initial_custom_attrs = [a for a in initial_details['attributes'] if a['name'] in created_attributes]
        initial_order_names = [a['name'] for a in initial_custom_attrs]

        print(f" -> Получен исходный порядок колонок: {initial_order_names}")
        expected_initial_order = ["title", "price", "status"]
        print_status(
            initial_order_names == expected_initial_order,
            "Исходный порядок соответствует порядку создания (по ID)."
        )

        # --- ШАГ 3: СОХРАНЕНИЕ НОВОГО ПОРЯДКА ---
        print_header("ШАГ 3: СОХРАНЕНИЕ НОВОГО ПОРЯДКА")

        # Перемешиваем: Статус, Цена, Название
        new_order_ids = [
            created_attributes['status'],
            created_attributes['price'],
            created_attributes['title']
        ]

        order_payload = {"attribute_ids": new_order_ids}
        order_url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes/order"

        print(f" -> Отправляем POST на {order_url} с новым порядком ID: {new_order_ids}")
        order_response = requests.post(order_url, headers=headers, json=order_payload)
        order_response.raise_for_status()

        print_status(order_response.status_code == 200, "Запрос на сохранение порядка прошел успешно.")

        # --- ШАГ 4: ФИНАЛЬНАЯ ПРОВЕРКА ---
        print_header("ШАГ 4: ПРОВЕРКА, ЧТО НОВЫЙ ПОРЯДОК ПРИМЕНИЛСЯ")

        final_details = get_table_details(headers, table_id)
        final_custom_attrs = [a for a in final_details['attributes'] if a['name'] in created_attributes]
        final_order_names = [a['name'] for a in final_custom_attrs]

        print(f" -> Получен новый порядок колонок: {final_order_names}")
        expected_final_order = ["status", "price", "title"]
        print_status(
            final_order_names == expected_final_order,
            "Финальный порядок колонок соответствует сохраненному."
        )

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ СОХРАНЕНИЯ ПОРЯДКА КОЛОНОК ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print("❌ ОШИБКА HTTP:")
    except Exception as e:
        print("❌ ОШИБКА HTTP:")


# ... (обработка ошибок)

# Вставьте сюда вашу рабочую функцию register_and_login
def register_and_login():
    unique_id = int(time.time())
    email = f"order_tester_{unique_id}@example.com"
    password = "password123"
    reg_payload = {"email": email, "password": password, "full_name": "Order Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


if __name__ == "__main__":
    run_ordering_test()