# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ ---
# BASE_URL = "http://89.111.169.47:8005"
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
#
# # -----------------
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
# # --- Вспомогательные функции ---
# # ... (вставьте сюда `print_status`, `print_header`, `register_and_login`)
#
# def run_time_filter_test():
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
#         headers = register_and_login()
#
#         table_name = f"meetings_{int(time.time())}"
#         table_config = {"name": table_name, "display_name": "Встречи (time тест)"}
#         table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']
#
#         attributes = [
#             {"name": "topic", "display_name": "Тема встречи", "value_type": "string"},
#             {"name": "start_time", "display_name": "Время начала", "value_type": "time"},
#         ]
#         for attr in attributes:
#             requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
#                           json=attr).raise_for_status()
#
#         # --- ШАГ 2: НАПОЛНЕНИЕ ДАННЫМИ ---
#         print_header("ШАГ 2: НАПОЛНЕНИЕ ТАБЛИЦЫ ДАННЫМИ О ВСТРЕЧАХ")
#
#         test_data = [
#             {"topic": "Утренний планер", "start_time": "09:00:00"},
#             {"topic": "Синхронизация с отделом продаж", "start_time": "11:30:00"},
#             {"topic": "Обед", "start_time": "14:00:00"},
#             {"topic": "Встреча с клиентом", "start_time": "15:00:00"},
#             {"topic": "Вечерний отчет", "start_time": "18:00:00"},
#         ]
#         for item in test_data:
#             requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=item).raise_for_status()
#
#         print_status(True, "5 тестовых записей успешно созданы.")
#
#         # --- ШАГ 3: ТЕСТИРОВАНИЕ ФИЛЬТРОВ ---
#         print_header("ШАГ 3: ТЕСТЫ ФИЛЬТРАЦИИ ПО ВРЕМЕНИ")
#
#         # Тест 1: Точное совпадение
#         print("\n -> Тест 1: Найти встречу ровно в 14:00 (ожидается 1)")
#         filters1 = [{"field": "start_time", "op": "is", "value": "14:00:00"}]
#         resp1 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
#                              params={"filters": json.dumps(filters1)}).json()
#         print_status(len(resp1) == 1 and resp1[0]['topic'] == "Обед", f"Найдено {len(resp1)} записей.")
#
#         # Тест 2: После
#         print("\n -> Тест 2: Найти все встречи после 12:00 (ожидается 3)")
#         filters2 = [{"field": "start_time", "op": "is_after", "value": "12:00:00"}]
#         resp2 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
#                              params={"filters": json.dumps(filters2)}).json()
#         print_status(len(resp2) == 3, f"Найдено {len(resp2)} записей.")
#
#         # Тест 3: Включительно или до
#         print("\n -> Тест 3: Найти все встречи в 15:00 или раньше (ожидается 4)")
#         filters3 = [{"field": "start_time", "op": "is_on_or_before", "value": "15:00:00"}]
#         resp3 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
#                              params={"filters": json.dumps(filters3)}).json()
#         print_status(len(resp3) == 4, f"Найдено {len(resp3)} записей.")
#
#         # Тест 4: Диапазон
#         print("\n -> Тест 4: Найти встречи между 10:00 и 15:00 (ожидается 3)")
#         filters4 = [{"field": "start_time", "op": "is_within", "value": ["10:00:00", "15:00:00"]}]
#         resp4 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
#                              params={"filters": json.dumps(filters4)}).json()
#         print_status(len(resp4) == 3, f"Найдено {len(resp4)} записей.")
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ТЕСТ ФИЛЬТРАЦИИ ПО ВРЕМЕНИ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА В СКРИПТЕ: {e}")
#
# def register_and_login():
#     unique_id = int(time.time())
#     email = f"bool_tester_{unique_id}@example.com"
#     password = "password123"
#     reg_payload = {"email": email, "password": password, "full_name": "Boolean Tester",
#                    "registration_token": CORRECT_REGISTRATION_TOKEN}
#     requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#     auth_payload = {'username': email, 'password': password}
#     token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
# if __name__ == "__main__":
#     run_time_filter_test()













# на фильтрацию пустых строк


import requests
import time
import sys
import json

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Вспомогательные функции ---
test_failed = False  # Глобальный флаг для отслеживания ошибок


def print_status(ok, message):
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}\n")
        test_failed = True


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login():
    try:
        auth_payload = {'username': EMAIL, 'password': PASSWORD}
        token_resp = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_resp.raise_for_status()
        return {'Authorization': f'Bearer {token_resp.json()["access_token"]}'}
    except Exception as e:
        print(f"Критическая ошибка при авторизации: {e}")
        return None


# --- Основная функция демонстрации ---
def run_blank_filter_test():
    headers = login()
    if not headers: return

    ids = {}
    table_name = f"blank_filter_test_{int(time.time())}"

    try:
        # --- ШАГ 1: Подготовка ---
        print_header("Шаг 1: Создание и наполнение тестовой таблицы")

        # Создаем таблицу и колонки
        type_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                                  json={"name": table_name, "display_name": "Тест фильтра по пустоте"})
        type_resp.raise_for_status();
        ids['table_id'] = type_resp.json()["id"]

        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}/attributes", headers=headers,
                      json={"name": "contact_name", "display_name": "Имя контакта",
                            "value_type": "string"}).raise_for_status()
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}/attributes", headers=headers,
                      json={"name": "phone_number", "display_name": "Телефон",
                            "value_type": "string"}).raise_for_status()

        # Наполняем данными: 2 с телефоном, 1 без.
        # Для создания пустой записи просто не передаем ключ 'phone_number'.
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                      json={"contact_name": "Контакт с телефоном", "phone_number": "79001112233"}).raise_for_status()
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                      json={"contact_name": "Контакт БЕЗ телефона"}).raise_for_status()
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                      json={"contact_name": "Еще один с телефоном", "phone_number": "79998887766"}).raise_for_status()

        print_status(True, "Тестовые данные (2 с телефоном, 1 без) успешно загружены.")

        # --- ТЕСТ 1: Фильтр по ПУСТОМУ значению (op: 'blank') ---
        print_header("Тест 1: Поиск записей, где 'Телефон' ПУСТО")

        filters_blank = [{"field": "phone_number", "op": "blank"}]
        params_blank = {'filters': json.dumps(filters_blank)}

        resp_blank = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params_blank)
        resp_blank.raise_for_status()
        data_blank = resp_blank.json()

        print(f" -> Запрос: {resp_blank.url}")
        print(f" -> Получено записей: {data_blank.get('total')}")

        # Проверки
        print_status(data_blank.get('total') == 1, "Ожидалась 1 запись.")
        if data_blank.get('total') == 1:
            found_name = data_blank['data'][0].get('contact_name')
            print_status(
                found_name == "Контакт БЕЗ телефона",
                f"Найдена правильная запись: '{found_name}'."
            )

        # --- ТЕСТ 2: Фильтр по НЕ ПУСТОМУ значению (op: 'not_blank') ---
        print_header("Тест 2: Поиск записей, где 'Телефон' НЕ ПУСТО")

        filters_not_blank = [{"field": "phone_number", "op": "not_blank"}]
        params_not_blank = {'filters': json.dumps(filters_not_blank)}

        resp_not_blank = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params_not_blank)
        resp_not_blank.raise_for_status()
        data_not_blank = resp_not_blank.json()

        print(f" -> Запрос: {resp_not_blank.url}")
        print(f" -> Получено записей: {data_not_blank.get('total')}")

        # Проверки
        print_status(data_not_blank.get('total') == 2, "Ожидалось 2 записи.")
        if data_not_blank.get('total') == 2:
            found_names = {row.get('contact_name') for row in data_not_blank['data']}
            expected_names = {"Контакт с телефоном", "Еще один с телефоном"}
            print_status(
                found_names == expected_names,
                f"Найдены правильные записи: {found_names}"
            )

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    finally:
        # --- ОЧИСТКА ---
        if 'table_id' in ids:
            print_header("Очистка (удаление тестовой таблицы)")
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}", headers=headers)
            print(f" -> Временная таблица '{table_name}' удалена.")

        # Финальный вердикт
        if not test_failed:
            print("\n" + "🎉" * 20 + "\n Все тесты фильтрации по (не)пустым значениям пройдены! \n" + "🎉" * 20)
        else:
            sys.exit(1)


if __name__ == "__main__":
    run_blank_filter_test()