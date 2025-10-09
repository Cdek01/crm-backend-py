import requests
import json
import time

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8000"
# BASE_URL = "http://89.111.169.47:8005"

CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"


def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}"); exit(1)
def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def register_and_login():
    unique_id = int(time.time())
    email = f"976@example.com"
    password = "AntonShlips97(1985)"
    reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def run_text_select_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
        headers = register_and_login()

        table_name = f"requests_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Заявки (text select)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        options_to_create = ["Техническая поддержка", "Вопрос по оплате", "Предложение"]
        attribute_payload = {
            "name": "request_type",
            "display_name": "Тип заявки",
            "value_type": "select",
            "list_items": options_to_create
        }
        requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                      json=attribute_payload).raise_for_status()
        print_status(True, f"Создана таблица '{table_name}' с колонкой-списком.")

        # --- ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ---
        print_header("ШАГ 2: СОЗДАНИЕ ЗАПИСИ С ТЕКСТОВЫМ ЗНАЧЕНИЕМ")

        payload1 = {"request_type": "Техническая поддержка"}
        record_id_1 = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload1).json()[0]['id']

        payload2 = {"request_type": "Вопрос по оплате"}
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload2).raise_for_status()

        record_1_data = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_id_1}", headers=headers).json()

        print(f" -> Создана запись #{record_id_1}. Полученное значение: '{record_1_data.get('request_type')}'")
        print_status(record_1_data.get('request_type') == "Техническая поддержка", "Значение сохранилось корректно.")

        # --- ШАГ 3: ОБНОВЛЕНИЕ ---
        print_header("ШАГ 3: ОБНОВЛЕНИЕ ЗАПИСИ")

        update_payload = {"request_type": "Предложение"}
        requests.put(f"{BASE_URL}/api/data/{table_name}/{record_id_1}", headers=headers,
                     json=update_payload).raise_for_status()

        updated_record_data = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_id_1}", headers=headers).json()
        print(f" -> Запись #{record_id_1} обновлена. Новое значение: '{updated_record_data.get('request_type')}'")
        print_status(updated_record_data.get('request_type') == "Предложение", "Значение успешно обновлено.")

        # --- ШАГ 4: ПРОВЕРКА ВАЛИДАЦИИ ---
        print_header("ШАГ 4: ПРОВЕРКА ВАЛИДАЦИИ (НЕГАТИВНЫЙ ТЕСТ)")

        invalid_payload = {"request_type": "Спам"}
        invalid_resp = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=invalid_payload)

        print(f" -> Попытка создать запись со значением 'Спам'. Статус ответа: {invalid_resp.status_code}")
        print(f" -> Тело ответа: {invalid_resp.text}")
        print_status(
            invalid_resp.status_code == 400,
            "Сервер корректно отклонил запрос с недопустимым значением (статус 400)."
        )

        # --- ШАГ 5: ПРОВЕРКА ФИЛЬТРАЦИИ ---
        print_header("ШАГ 5: ПРОВЕРКА ФИЛЬТРАЦИИ ПО ТЕКСТУ")

        print("\n -> Поиск по новому значению 'Предложение' (ожидается 1)")
        filters1 = [{"field": "request_type", "value": "Предложение"}]
        resp1 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters1)}).json()
        print_status(len(resp1) == 1, f"Найдено {len(resp1)} записей.")

        print("\n -> Поиск по старому значению 'Техническая поддержка' (ожидается 0)")
        filters2 = [{"field": "request_type", "value": "Техническая поддержка"}]
        resp2 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters2)}).json()
        print_status(len(resp2) == 0, f"Найдено {len(resp2)} записей.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ ВЫПАДАЮЩИХ СПИСКОВ С ТЕКСТОМ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


# ... (вставьте сюда `register_and_login`, `print_status`, `print_header`)

if __name__ == "__main__":
    run_text_select_test()




















# def run_inline_select_test():
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
#         headers = register_and_login()
#
#         table_name = f"tasks_inline_select_{int(time.time())}"
#         table_config = {"name": table_name, "display_name": "Задачи (inline select тест)"}
#         table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']
#
#         print_status(True, f"Создана тестовая таблица '{table_name}' с ID: {table_id}")
#
#         # --- ШАГ 2: СОЗДАНИЕ КОЛОНКИ-СПИСКА ОДНИМ ЗАПРОСОМ ---
#         print_header("ШАГ 2: СОЗДАНИЕ КОЛОНКИ С ОПЦИЯМИ")
#
#         options_to_create = ["To Do", "In Progress", "Done"]
#         attribute_payload = {
#             "name": "task_status",
#             "display_name": "Статус",
#             "value_type": "select",
#             "list_items": options_to_create
#         }
#
#         url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
#         create_attr_response = requests.post(url, headers=headers, json=attribute_payload)
#         create_attr_response.raise_for_status()
#
#         created_attribute = create_attr_response.json()
#         print_status(True, f"Запрос на создание колонки и списка прошел успешно.{created_attribute}")
#
#         # --- ШАГ 3: ПРОВЕРКА СТРУКТУРЫ КОЛОНКИ ---
#         print_header("ШАГ 3: ПРОВЕРКА СОЗДАННОЙ КОЛОНКИ")
#
#         # Получаем полную структуру таблицы
#         table_details = requests.get(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers).json()
#
#         # Находим наш атрибут
#         status_attribute = next((attr for attr in table_details['attributes'] if attr['name'] == 'task_status'), None)
#
#         print_status(status_attribute is not None, "Колонка 'task_status' найдена в структуре таблицы.")
#
#         # Проверяем, что ID списка был создан и присвоен
#         select_list_id = status_attribute.get('select_list_id')
#         print(f" -> ID связанного списка: {select_list_id}")
#         print_status(
#             select_list_id is not None and isinstance(select_list_id, int),
#             "Колонка корректно связана со списком опций (select_list_id установлен)."
#         )
#
#         # --- ШАГ 4: ПРОВЕРКА СОДЕРЖИМОГО СПИСКА ---
#         print_header("ШАГ 4: ПРОВЕРКА АВТОМАТИЧЕСКИ СОЗДАННОГО СПИСКА ОПЦИЙ")
#
#         list_details_url = f"{BASE_URL}/api/meta/select-lists/{select_list_id}"
#         list_details_response = requests.get(list_details_url, headers=headers)
#         list_details_response.raise_for_status()
#         list_data = list_details_response.json()
#
#         print(f" -> Получены опции для списка ID={select_list_id}: {list_data}")
#
#         # Проверяем количество
#         print_status(
#             len(list_data.get('options', [])) == len(options_to_create),
#             f"Создано корректное количество опций ({len(options_to_create)})."
#         )
#
#         # Проверяем содержимое
#         option_values = {opt['value'] for opt in list_data.get('options', [])}
#         print_status(
#             option_values == set(options_to_create),
#             "Содержимое опций совпадает с переданным в `list_items`."
#         )
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ АВТОСОЗДАНИЯ СПИСКОВ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
#
#
# # ... (вставьте сюда `register_and_login`, `print_status`, `print_header`)
#
# if __name__ == "__main__":
#     run_inline_select_test()