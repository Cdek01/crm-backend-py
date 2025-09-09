# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
# BASE_URL = "http://89.111.169.47:8005"   # "http://127.0.0.1:8005"
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
# def register_and_login():
#     unique_id = int(time.time())
#     email = f"select_tester_{unique_id}@example.com"
#     password = "password123"
#     reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
#                    "registration_token": CORRECT_REGISTRATION_TOKEN}
#     requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#     auth_payload = {'username': email, 'password': password}
#     token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
#
# def run_select_type_test():
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("ШАГ 1: АВТОРИЗАЦИЯ И СОЗДАНИЕ СПИСКА ОПЦИЙ")
#         headers = register_and_login()
#
#         # 1.1 Создаем список "Статусы задачи"
#         list_payload = {"name": "Статусы задачи"}
#         list_resp = requests.post(f"{BASE_URL}/api/meta/select-lists/", headers=headers, json=list_payload).json()
#         list_id = list_resp['id']
#
#         # 1.2 Наполняем его опциями
#         options_map = {}  # { "text": id }
#         for option_text in ["Новая", "В работе", "Выполнена"]:
#             opt_payload = {"value": option_text}
#             opt_resp = requests.post(f"{BASE_URL}/api/meta/select-lists/{list_id}/options", headers=headers,
#                                      json=opt_payload).json()
#             options_map[option_text] = opt_resp['id']
#
#         print_status(True, f"Создан список 'Статусы задачи' (ID: {list_id}) с 3 опциями.")
#
#         # --- ШАГ 2: СОЗДАНИЕ ТАБЛИЦЫ И КОЛОНКИ ТИПА 'select' ---
#         print_header("ШАГ 2: СОЗДАНИЕ ТАБЛИЦЫ С КОЛОНКОЙ ТИПА 'select'")
#
#         table_name = f"tasks_{int(time.time())}"
#         table_config = {"name": table_name, "display_name": "Задачи"}
#         table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']
#
#         # Создаем обычную колонку
#         requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
#                       json={"name": "title", "display_name": "Название", "value_type": "string"}).raise_for_status()
#
#         # Создаем нашу колонку типа 'select', связывая ее со списком
#         select_attr_payload = {
#             "name": "task_status",
#             "display_name": "Статус",
#             "value_type": "select",
#             "select_list_id": list_id
#         }
#         requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
#                       json=select_attr_payload).raise_for_status()
#
#         print_status(True, "Создана таблица 'Задачи' с колонкой 'Статус' типа 'select'.")
#
#         # --- ШАГ 3: СОЗДАНИЕ ЗАПИСИ С ВЫБРАННОЙ ОПЦИЕЙ ---
#         print_header("ШАГ 3: СОЗДАНИЕ ЗАПИСИ С ВЫБОРОМ ОПЦИИ ИЗ СПИСКА")
#
#         record_payload = {
#             "title": "Протестировать новую функцию",
#             "task_status": options_map["В работе"]  # <-- Передаем ID опции
#         }
#         create_resp = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=record_payload).json()
#         record_id = create_resp[0]['id']
#
#         print_status(True, f"Создана запись с ID: {record_id} и статусом 'В работе'.")
#
#         # --- ШАГ 4: ПРОВЕРКА СОХРАНЕНИЯ ---
#         print_header("ШАГ 4: ПРОВЕРКА, ЧТО ЗНАЧЕНИЕ СОХРАНИЛОСЬ КОРРЕКТНО")
#
#         get_resp = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_id}", headers=headers).json()
#
#         print(f" -> Полученные данные: {get_resp}")
#         print_status(
#             get_resp.get("task_status") == options_map["В работе"],
#             f"Сохраненное значение (ID={get_resp.get('task_status')}) совпадает с ожидаемым (ID={options_map['В работе']})."
#         )
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ КОЛОНОК ТИПА 'SELECT' ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
#
#     except Exception as e:
#         print('❌ ОШИБКА:')
#
#
# # # ... (обработка ошибок)
# # # --- ОСНОВНОЙ ТЕСТ ---
# # def run_select_lists_test():
# #     list_id = None
# #     options = {}  # Словарь для хранения созданных опций {name: id}
# #
# #     try:
# #         # --- ШАГ 1: АВТОРИЗАЦИЯ ---
# #         print_header("ШАГ 1: АВТОРИЗАЦИЯ")
# #         headers = register_and_login()
# #
# #         # --- ШАГ 2: СОЗДАНИЕ СПИСКА ---
# #         print_header("ШАГ 2: СОЗДАНИЕ НОВОГО СПИСКА 'Статусы Проекта'")
# #         list_payload = {"name": "Статусы Проекта"}
# #         resp = requests.post(f"{BASE_URL}/api/meta/select-lists/", headers=headers, json=list_payload)
# #         resp.raise_for_status()
# #         list_data = resp.json()
# #         list_id = list_data['id']
# #         print_status(True, f"Список успешно создан с ID: {list_id}")
# #
# #         # --- ШАГ 3: ПРОВЕРКА НАЛИЧИЯ В ОБЩЕМ СПИСКЕ ---
# #         resp = requests.get(f"{BASE_URL}/api/meta/select-lists/", headers=headers)
# #         all_lists = resp.json()
# #         found = any(l['id'] == list_id and l['name'] == "Статусы Проекта" for l in all_lists)
# #         print_status(found, "Созданный список найден в общем перечне.")
# #
# #         # --- ШАГ 4: ДОБАВЛЕНИЕ ОПЦИЙ ---
# #         print_header(f"ШАГ 4: ДОБАВЛЕНИЕ ОПЦИЙ В СПИСОК ID={list_id}")
# #         options_to_add = ["Планирование", "В работе", "Завершено"]
# #         for option_value in options_to_add:
# #             payload = {"value": option_value}
# #             url = f"{BASE_URL}/api/meta/select-lists/{list_id}/options"
# #             resp = requests.post(url, headers=headers, json=payload)
# #             resp.raise_for_status()
# #             # Сохраняем ID созданной опции для дальнейших тестов
# #             options[option_value] = resp.json()['id']
# #             print(f" -> Добавлена опция '{option_value}' с ID: {options[option_value]}")
# #
# #         # Проверяем, что все опции добавились
# #         resp = requests.get(f"{BASE_URL}/api/meta/select-lists/{list_id}", headers=headers).json()
# #         option_values = {opt['value'] for opt in resp['options']}
# #         print_status(len(option_values) == 3, f"В списке теперь {len(option_values)} опции.")
# #
# #         # --- ШАГ 5: ОБНОВЛЕНИЕ ОПЦИИ ---
# #         print_header("ШАГ 5: ОБНОВЛЕНИЕ ОПЦИИ 'В работе'")
# #         option_id_to_update = options["В работе"]
# #         new_value = "В активной разработке"
# #         update_payload = {"value": new_value}
# #         url = f"{BASE_URL}/api/meta/select-lists/{list_id}/options/{option_id_to_update}"
# #         resp = requests.put(url, headers=headers, json=update_payload)
# #         resp.raise_for_status()
# #         print_status(resp.json()['value'] == new_value, "Текст опции успешно обновлен.")
# #
# #         # --- ШАГ 6: УДАЛЕНИЕ ОПЦИИ ---
# #         print_header("ШАГ 6: УДАЛЕНИЕ ОПЦИИ 'Планирование'")
# #         option_id_to_delete = options["Планирование"]
# #         url = f"{BASE_URL}/api/meta/select-lists/{list_id}/options/{option_id_to_delete}"
# #         resp = requests.delete(url, headers=headers)
# #         print_status(resp.status_code == 204, "Запрос на удаление прошел успешно (статус 204).")
# #
# #         # --- ШАГ 7: ФИНАЛЬНАЯ ПРОВЕРКА ---
# #         print_header("ШАГ 7: ФИНАЛЬНАЯ ПРОВЕРКА СОСТАВА СПИСКА")
# #         final_resp = requests.get(f"{BASE_URL}/api/meta/select-lists/{list_id}", headers=headers).json()
# #         final_option_values = {opt['value'] for opt in final_resp['options']}
# #
# #         print(f" -> В списке остались опции: {final_option_values}")
# #         print_status(len(final_option_values) == 2, "В списке осталось корректное количество опций (2).")
# #         print_status("Планирование" not in final_option_values, "Опция 'Планирование' удалена.")
# #         print_status("В активной разработке" in final_option_values,
# #                      "Обновленная опция 'В активной разработке' на месте.")
# #
# #         print("\n" + "=" * 60)
# #         print("🎉🎉🎉 ТЕСТ CRUD-ОПЕРАЦИЙ ДЛЯ ВЫПАДАЮЩИХ СПИСКОВ ПРОЙДЕН! 🎉🎉🎉")
# #
# #     except requests.exceptions.HTTPError as e:
# #         print(f"\n❌ ОШИБКА HTTP.")
# #         print(f"   URL: {e.request.method} {e.request.url}")
# #         print(f"   Статус: {e.response.status_code}")
# #         print(f"   Ответ: {e.response.text}")
# #     except Exception as e:
# #         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
#
#
# # Вставьте сюда вашу рабочую функцию register_and_login
#
#
# if __name__ == "__main__":
#     # run_select_lists_test()
#     run_select_type_test()


import requests
import json
import time

# --- НАСТРОЙКИ ---
# BASE_URL = "http://127.0.0.1:8005"
BASE_URL = "http://89.111.169.47:8005"   # "http://127.0.0.1:8005"

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
    email = f"select_tester_{unique_id}@example.com"
    password = "password123"
    reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def get_current_state(headers, table_name):
    """Получает текущий список записей и возвращает его."""
    response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
    response.raise_for_status()
    return response.json()


def move_task(headers, table_name, current_state, task_to_move_id, after_task_id, before_task_id):
    """Эмулирует перетаскивание одной задачи."""
    after_pos = None
    if after_task_id:
        after_pos = next(item['position'] for item in current_state if item['id'] == after_task_id)

    before_pos = None
    if before_task_id:
        before_pos = next(item['position'] for item in current_state if item['id'] == before_task_id)

    payload = {
        "entity_id": task_to_move_id,
        "after_position": after_pos,
        "before_position": before_pos
    }

    url = f"{BASE_URL}/api/data/{table_name}/position"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    print(f" -> Перемещение ID {task_to_move_id} завершено. Новая позиция: {response.json().get('new_position')}")


def verify_order(state, expected_ids, test_name):
    """Проверяет, что порядок ID в `state` соответствует `expected_ids`."""
    actual_ids = [item['id'] for item in state]
    print(f" -> Ожидаемый порядок: {expected_ids}")
    print(f" -> Фактический порядок: {actual_ids}")
    print_status(actual_ids == expected_ids, test_name)


# --- ОСНОВНОЙ ТЕСТ ---
def run_extended_ordering_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ 6 ЗАПИСЕЙ")
        headers = register_and_login()

        table_name = f"tasks_ext_order_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Задачи (расширенная сортировка)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']
        requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                      json={"name": "title", "display_name": "Название", "value_type": "string"}).raise_for_status()

        # Создаем 6 задач и запоминаем их ID
        tasks = {}
        for i in range(1, 7):
            title = f"Задача {i}"
            task_id = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={"title": title}).json()[
                'id']
            tasks[title] = task_id
            time.sleep(0.01)  # Гарантируем разные position

        print(f" -> Созданы задачи: {tasks}")

        # --- ШАГ 2: ПРОВЕРКА ИСХОДНОГО ПОРЯДКА ---
        print_header("ШАГ 2: ПРОВЕРКА ИСХОДНОГО ПОРЯДКА (1, 2, 3, 4, 5, 6)")
        state1 = get_current_state(headers, table_name)
        expected_order1 = [tasks['Задача 1'], tasks['Задача 2'], tasks['Задача 3'], tasks['Задача 4'],
                           tasks['Задача 5'], tasks['Задача 6']]
        verify_order(state1, expected_order1, "Исходный порядок соответствует порядку создания.")

        # --- ШАГ 3: ПЕРЕМЕЩЕНИЕ ПОСЛЕДНЕГО В НАЧАЛО ---
        print_header("ШАГ 3: ПЕРЕМЕЩЕНИЕ 'Задачи 6' В НАЧАЛО")
        move_task(headers, table_name, state1, tasks['Задача 6'], after_task_id=None, before_task_id=tasks['Задача 1'])
        state2 = get_current_state(headers, table_name)
        expected_order2 = [tasks['Задача 6'], tasks['Задача 1'], tasks['Задача 2'], tasks['Задача 3'],
                           tasks['Задача 4'], tasks['Задача 5']]
        verify_order(state2, expected_order2, "Порядок '6, 1, 2, 3, 4, 5' установлен корректно.")

        # --- ШАГ 4: ПЕРЕМЕЩЕНИЕ ПЕРВОГО В КОНЕЦ ---
        print_header("ШАГ 4: ПЕРЕМЕЩЕНИЕ 'Задачи 6' (ТЕПЕРЬ ПЕРВОЙ) В КОНЕЦ")
        move_task(headers, table_name, state2, tasks['Задача 6'], after_task_id=tasks['Задача 5'], before_task_id=None)
        state3 = get_current_state(headers, table_name)
        expected_order3 = [tasks['Задача 1'], tasks['Задача 2'], tasks['Задача 3'], tasks['Задача 4'],
                           tasks['Задача 5'], tasks['Задача 6']]
        verify_order(state3, expected_order3, "Порядок вернулся к исходному '1, 2, 3, 4, 5, 6'.")

        # --- ШАГ 5: СЛОЖНОЕ ПЕРЕМЕЩЕНИЕ В СЕРЕДИНУ ---
        print_header("ШАГ 5: ПЕРЕМЕЩЕНИЕ 'Задачи 4' МЕЖДУ 'Задачей 1' И 'Задачей 2'")
        move_task(headers, table_name, state3, tasks['Задача 4'], after_task_id=tasks['Задача 1'],
                  before_task_id=tasks['Задача 2'])
        state4 = get_current_state(headers, table_name)
        expected_order4 = [tasks['Задача 1'], tasks['Задача 4'], tasks['Задача 2'], tasks['Задача 3'],
                           tasks['Задача 5'], tasks['Задача 6']]
        verify_order(state4, expected_order4, "Порядок '1, 4, 2, 3, 5, 6' установлен корректно.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 РАСШИРЕННЫЙ ТЕСТ СОРТИРОВКИ СТРОК ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


if __name__ == "__main__":
    run_extended_ordering_test()