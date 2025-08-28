# # import requests
# # import json
# # import random
# # from faker import Faker
# # import time
# #
# # # --- НАСТРОЙКИ ---
# # BASE_URL = "http://127.0.0.1:8005"  # Укажите адрес вашего запущенного сервера
# # # BASE_URL = "http://89.111.169.47:8005" # Пример для удаленного сервера
# #
# # # Инициализируем Faker для генерации случайных данных
# # fake = Faker("ru_RU")
# #
# #
# # # --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КРАСИВОГО ВЫВОДА ---
# #
# # def print_header(title):
# #     print("\n" + "=" * 80)
# #     print(f" {title.upper()} ".center(80, "="))
# #     print("=" * 80)
# #
# #
# # def print_request(method, url, payload=None, headers=None):
# #     print(f">>> REQUEST: {method} {url}")
# #     if payload:
# #         print(f"    Payload: {json.dumps(payload, indent=4, ensure_ascii=False)}")
# #     if headers and "Authorization" in headers:
# #         print("    Headers: Authorization: Bearer <TOKEN>")
# #
# #
# # def print_response(response):
# #     print(f"<<< RESPONSE: {response.status_code}")
# #     try:
# #         # Пытаемся красиво напечатать JSON
# #         print(json.dumps(response.json(), indent=4, ensure_ascii=False))
# #     except json.JSONDecodeError:
# #         # Если ответ не JSON, печатаем как текст
# #         print(response.text)
# #
# #
# # def check_test_result(title, condition, success_msg="[PASS]", failure_msg="[FAIL]"):
# #     """Проверяет условие и выводит результат теста."""
# #     if condition:
# #         print(f"✅ {success_msg} {title}")
# #     else:
# #         print(f"❌ {failure_msg} {title}")
# #
# #
# # # --- ОСНОВНОЙ СКРИПТ ---
# #
# # def run_api_tests():
# #     session = requests.Session()
# #     access_token = None
# #
# #     # Уникальный идентификатор для этого запуска, чтобы избежать конфликтов
# #     run_id = int(time.time())
# #
# #     # 1. РЕГИСТРАЦИЯ
# #     print_header("1. Регистрация нового пользователя")
# #     user_email = f"testuser_{run_id}@example.com"
# #     user_password = "strong_password_123"
# #     register_payload = {
# #         "email": user_email,
# #         "password": user_password,
# #         "full_name": fake.name()
# #     }
# #     print_request("POST", f"{BASE_URL}/api/auth/register", register_payload)
# #     response = session.post(f"{BASE_URL}/api/auth/register", json=register_payload)
# #     print_response(response)
# #     check_test_result("Регистрация успешна", response.status_code == 201)
# #
# #     # 2. ВХОД В СИСТЕМУ
# #     print_header("2. Вход в систему и получение токена")
# #     login_payload = {
# #         "username": user_email,
# #         "password": user_password
# #     }
# #     print_request("POST", f"{BASE_URL}/api/auth/token", login_payload)
# #     response = session.post(f"{BASE_URL}/api/auth/token", data=login_payload)
# #     print_response(response)
# #     if response.status_code == 200:
# #         access_token = response.json().get("access_token")
# #         check_test_result("Получение токена успешно", access_token is not None)
# #     else:
# #         check_test_result("Получение токена провалено", False)
# #         return  # Выход, если не удалось войти
# #
# #     headers = {"Authorization": f"Bearer {access_token}"}
# #
# #     # 3. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ
# #     print_header("3. Создание тестовых данных")
# #     # Создаем лиды
# #     session.post(f"{BASE_URL}/api/leads/", headers=headers,
# #                  json={"organization_name": "Alpha Project", "lead_status": "New", "rating": 5})
# #     session.post(f"{BASE_URL}/api/leads/", headers=headers,
# #                  json={"organization_name": "Beta Services", "lead_status": "In Progress", "rating": 3})
# #     session.post(f"{BASE_URL}/api/leads/", headers=headers,
# #                  json={"organization_name": "Gamma Inc", "lead_status": "New", "rating": 4})
# #     print("✅ Создано 3 тестовых лида.")
# #
# #     # Создаем юр. лица
# #     session.post(f"{BASE_URL}/api/legal-entities/", headers=headers,
# #                  json={"short_name": "StroyMontazh", "inn": f"7701{run_id % 1000000:06}", "status": "Действующая",
# #                        "revenue": 1000000})
# #     session.post(f"{BASE_URL}/api/legal-entities/", headers=headers,
# #                  json={"short_name": "AgroProm", "inn": f"7702{run_id % 1000000:06}", "status": "Действующая",
# #                        "revenue": 5000000})
# #     session.post(f"{BASE_URL}/api/legal-entities/", headers=headers,
# #                  json={"short_name": "IT Solutions", "inn": f"7703{run_id % 1000000:06}",
# #                        "status": "В процессе ликвидации", "revenue": 250000})
# #     print("✅ Создано 3 тестовых юр. лица.")
# #
# #     # Создаем физ. лиц
# #     session.post(f"{BASE_URL}/api/individuals/", headers=headers,
# #                  json={"full_name": "Иванов Иван Иванович", "email": f"ivanov_{run_id}@test.com"})
# #     session.post(f"{BASE_URL}/api/individuals/", headers=headers,
# #                  json={"full_name": "Петров Петр Петрович", "email": f"petrov_{run_id}@test.com"})
# #     session.post(f"{BASE_URL}/api/individuals/", headers=headers,
# #                  json={"full_name": "Сидоров Сидор Сидорович", "email": f"sidorov_{run_id}@test.com"})
# #     print("✅ Создано 3 тестовых физ. лица.")
# #
# #     # 4. ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ И СОРТИРОВКИ
# #     print_header("4. Тестирование эндпоинтов")
# #
# #     # --- ТЕСТЫ ДЛЯ ЛИДОВ ---
# #     print("\n--- Тестируем /api/leads/ ---")
# #     url = f"{BASE_URL}/api/leads?lead_status=New"
# #     response = session.get(url, headers=headers)
# #     print_request("GET", url)
# #     check_test_result("Фильтрация лидов по статусу 'New'",
# #                       response.status_code == 200 and len(response.json()) == 2)
# #
# #     url = f"{BASE_URL}/api/leads?sort_by=rating&sort_order=desc"
# #     response = session.get(url, headers=headers)
# #     print_request("GET", url)
# #     data = response.json()
# #     ratings = [item['rating'] for item in data]
# #     check_test_result("Сортировка лидов по рейтингу (desc)",
# #                       response.status_code == 200 and ratings == [5, 4, 3])
# #
# #     # --- ТЕСТЫ ДЛЯ ЮР. ЛИЦ ---
# #     print("\n--- Тестируем /api/legal-entities/ ---")
# #     url = f"{BASE_URL}/api/legal-entities?status=Действующая"
# #     response = session.get(url, headers=headers)
# #     print_request("GET", url)
# #     check_test_result("Фильтрация юр. лиц по статусу 'Действующая'",
# #                       response.status_code == 200 and len(response.json()) == 2)
# #
# #     url = f"{BASE_URL}/api/legal-entities?sort_by=revenue&sort_order=asc"
# #     response = session.get(url, headers=headers)
# #     print_request("GET", url)
# #     data = response.json()
# #     revenues = [item['revenue'] for item in data]
# #     check_test_result("Сортировка юр. лиц по выручке (asc)",
# #                       response.status_code == 200 and revenues == [250000, 1000000, 5000000])
# #
# #     # --- ТЕСТЫ ДЛЯ ФИЗ. ЛИЦ ---
# #     print("\n--- Тестируем /api/individuals/ ---")
# #     url = f"{BASE_URL}/api/individuals?full_name=Иван"  # Поиск по части имени
# #     response = session.get(url, headers=headers)
# #     print_request("GET", url)
# #     check_test_result("Фильтрация физ. лиц по части имени 'Иван'",
# #                       response.status_code == 200 and len(response.json()) == 1)
# #
# #     url = f"{BASE_URL}/api/individuals?sort_by=full_name&sort_order=desc"
# #     response = session.get(url, headers=headers)
# #     print_request("GET", url)
# #     data = response.json()
# #     names = [item['full_name'] for item in data]
# #     check_test_result("Сортировка физ. лиц по ФИО (desc)",
# #                       response.status_code == 200 and names == ["Сидоров Сидор Сидорович", "Петров Петр Петрович",
# #                                                                 "Иванов Иван Иванович"])
# #
# #
# # if __name__ == "__main__":
# #     run_api_tests()
#
#
# # test_bulk_delete.py
# import requests
# import json
# import time
#
# # --- НАСТРОЙТЕ ЭТИ ПЕРЕМЕННЫЕ ---
# # BASE_URL = "http://89.111.169.47:8005"  # IP-адрес вашего локального сервера
# BASE_URL = "http://127.0.0.1:8005"
# # Мы будем генерировать уникального пользователя для каждого теста
# UNIQUE_ID = int(time.time())
# USER_EMAIL = f"bulk_delete_tester_{UNIQUE_ID}@example.com"
# USER_PASSWORD = "a_very_secure_password_123!"
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
#
# # ---------------------------------
#
# def print_status(ok, message):
#     """Выводит красивый статус операции."""
#     if ok:
#         print(f"✅ [SUCCESS] {message}")
#     else:
#         print(f"❌ [FAILURE] {message}")
#         # Завершаем скрипт при первой же ошибке
#         exit(1)
#
#
# def run_bulk_delete_test():
#     """
#     Выполняет полный цикл тестирования массового удаления:
#     1. Регистрация и вход.
#     2. Создание 3-х тестовых записей (физ. лиц).
#     3. Вызов эндпоинта для массового удаления 2-х из них.
#     4. Проверка ответа и последствий удаления.
#     """
#     token = None
#     headers = {}
#     individual_ids = []
#
#     try:
#         # --- ШАГ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ ---
#         print("-" * 50)
#         print("1. РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ")
#         # Регистрация
#         register_payload = {"email": USER_EMAIL, "password": USER_PASSWORD, "registration_token": CORRECT_REGISTRATION_TOKEN}
#         register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
#         register_response.raise_for_status()
#         # Вход
#         auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
#         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
#         auth_response.raise_for_status()
#         token = auth_response.json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#         print_status(True, "Успешно зарегистрирован и получен токен.")
#
#         # --- ШАГ 2: СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ---
#         print("-" * 50)
#         print("2. СОЗДАНИЕ 3-Х ФИЗИЧЕСКИХ ЛИЦ")
#         individuals_to_create = [
#             {"full_name": "Иванов Иван (на удаление)"},
#             {"full_name": "Петров Петр (на удаление)"},
#             {"full_name": "Сидоров Сидор (останется)"}
#         ]
#
#         for ind_data in individuals_to_create:
#             response = requests.post(f"{BASE_URL}/api/individuals/", headers=headers, json=ind_data)
#             response.raise_for_status()
#             created_id = response.json()['id']
#             individual_ids.append(created_id)
#             print(f"   -> Создано физ. лицо '{ind_data['full_name']}' с ID: {created_id}")
#
#         print_status(True, f"Успешно создано {len(individual_ids)} записи.")
#
#         # --- ШАГ 3: ВЫПОЛНЕНИЕ МАССОВОГО УДАЛЕНИЯ ---
#         print("-" * 50)
#         print("3. ВЫПОЛНЕНИЕ МАССОВОГО УДАЛЕНИЯ")
#         ids_to_delete = individual_ids[:2]  # Берем первые два ID
#         id_to_keep = individual_ids[2]  # Последний ID оставляем для проверки
#
#         print(f"   -> Отправка запроса на удаление ID: {ids_to_delete}")
#
#         delete_payload = {"ids": ids_to_delete}
#         delete_response = requests.delete(f"{BASE_URL}/api/individuals/bulk-delete", headers=headers,
#                                           json=delete_payload)
#         delete_response.raise_for_status()
#
#         deleted_count = delete_response.json().get("deleted_count")
#
#         print_status(
#             deleted_count == len(ids_to_delete),
#             f"Сервер вернул корректный ответ. Удалено записей: {deleted_count}"
#         )
#
#         # --- ШАГ 4: ПРОВЕРКА ПОСЛЕДСТВИЙ ---
#         print("-" * 50)
#         print("4. ПРОВЕРКА РЕЗУЛЬТАТОВ УДАЛЕНИЯ")
#
#         # 4.1. Проверяем, что удаленные записи действительно не существуют
#         for deleted_id in ids_to_delete:
#             check_response = requests.get(f"{BASE_URL}/api/individuals/{deleted_id}", headers=headers)
#             print_status(
#                 check_response.status_code == 404,
#                 f"Запись с ID {deleted_id} успешно удалена (получен статус 404)."
#             )
#
#         # 4.2. Проверяем, что оставшаяся запись на месте
#         check_response = requests.get(f"{BASE_URL}/api/individuals/{id_to_keep}", headers=headers)
#         check_response.raise_for_status()
#         print_status(
#             check_response.status_code == 200,
#             f"Запись с ID {id_to_keep} не была удалена и доступна."
#         )
#
#         # 4.3. Проверяем общий список
#         list_response = requests.get(f"{BASE_URL}/api/individuals/", headers=headers)
#         list_response.raise_for_status()
#         remaining_count = len(list_response.json())
#         print_status(
#             remaining_count == 1,
#             f"В общем списке осталась {remaining_count} запись, как и ожидалось."
#         )
#
#         print("-" * 50)
#         print("\n🎉 ВСЕ ТЕСТЫ ДЛЯ МАССОВОГО УДАЛЕНИЯ ПРОШЛИ УСПЕШНО! 🎉")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
#         print(f"URL запроса: {e.request.method} {e.request.url}")
#         if e.request.body:
#             # Печатаем тело запроса, если оно есть
#             try:
#                 # Пытаемся декодировать как JSON для читаемости
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
#     run_bulk_delete_test()


import requests
import json
import time
from datetime import datetime, date, timedelta

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"


# -----------------

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

def run_advanced_filter_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
        headers = register_and_login()

        table_name = f"tasks_filter_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Задачи (фильтры)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        attributes = [
            {"name": "due_date", "display_name": "Срок сдачи", "value_type": "date"},
            {"name": "description", "display_name": "Описание", "value_type": "string"},
        ]
        for attr in attributes:
            requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                          json=attr).raise_for_status()

        # --- ШАГ 2: НАПОЛНЕНИЕ ДАННЫМИ ---
        print_header("ШАГ 2: НАПОЛНЕНИЕ ТАБЛИЦЫ РАЗНООБРАЗНЫМИ ДАННЫМИ")

        today = date.today()
        test_data = [
            # 1. Задача со сроком далеко в прошлом (без описания)
            {"due_date": (today - timedelta(days=10)).isoformat()},
            # 2. Задача со сроком "вчера"
            {"due_date": (today - timedelta(days=1)).isoformat(), "description": "Вчерашняя задача"},
            # 3. Задача со сроком "сегодня"
            {"due_date": today.isoformat(), "description": "Сегодняшняя задача"},
            # 4. Задача со сроком "завтра"
            {"due_date": (today + timedelta(days=1)).isoformat(), "description": "Завтрашняя задача"},
            # 5. Задача со сроком далеко в будущем
            {"due_date": (today + timedelta(days=10)).isoformat(), "description": "Задача на будущее"},
        ]
        for item in test_data:
            # Преобразуем date в datetime для отправки
            if 'due_date' in item:
                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                # Используем `datetime.time.min` вместо `time.min`
                item['due_date'] = datetime.combine(date.fromisoformat(item['due_date']), datetime.min.time()).isoformat()
                # ---------------------------
            requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=item).raise_for_status()

        print_status(True, "5 тестовых записей успешно созданы.")
        # --- ШАГ 3: ТЕСТИРОВАНИЕ ФИЛЬТРОВ ---
        print_header("ШАГ 3: ТЕСТЫ РАСШИРЕННОЙ ФИЛЬТРАЦИИ")

        # Тест 1: blank / not_blank
        print("\n -> Тест 1: Поле 'Описание' пустое (ожидается 1)")
        filters1 = [{"field": "description", "op": "blank"}]
        resp1 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters1)}).json()
        print_status(len(resp1) == 1, f"Найдено {len(resp1)} записей.")

        print("\n -> Тест 2: Поле 'Описание' не пустое (ожидается 4)")
        filters2 = [{"field": "description", "op": "not_blank"}]
        resp2 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters2)}).json()
        print_status(len(resp2) == 4, f"Найдено {len(resp2)} записей.")

        # Тест 3: Относительные даты
        print("\n -> Тест 3: Срок сдачи 'является' 'сегодня' (ожидается 1)")
        filters3 = [{"field": "due_date", "op": "is", "value": "today"}]
        resp3 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters3)}).json()
        print_status(len(resp3) == 1, f"Найдено {len(resp3)} записей.")

        # Тест 4: "Количество дней"
        print("\n -> Тест 4: Срок сдачи 'после' 'через 5 дней' (ожидается 1)")
        filters4 = [{"field": "due_date", "op": "is_after", "value": {"type": "number_of_days_from_now", "amount": 5}}]
        resp4 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters4)}).json()
        print_status(len(resp4) == 1, f"Найдено {len(resp4)} записей.")

        # Тест 5: Точная дата
        print("\n -> Тест 5: Срок сдачи 'в или до' точной даты 'завтра' (ожидается 4)")
        tomorrow_iso = (today + timedelta(days=1)).isoformat()
        filters5 = [{"field": "due_date", "op": "is_on_or_before", "value": tomorrow_iso}]
        resp5 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters5)}).json()
        print_status(len(resp5) == 4, f"Найдено {len(resp5)} записей.")

        # Тест 6: Диапазон 'is_within'
        print("\n -> Тест 6: Срок сдачи 'в пределах' от 'вчера' до 'завтра' (ожидается 3)")
        filters6 = [{"field": "due_date", "op": "is_within", "value": ["yesterday", "tomorrow"]}]
        resp6 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                             params={"filters": json.dumps(filters6)}).json()
        print_status(len(resp6) == 3, f"Найдено {len(resp6)} записей.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ РАСШИРЕННОЙ ФИЛЬТРАЦИИ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"Ошибка при выполнении запроса: {e}")
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")


if __name__ == "__main__":
    run_advanced_filter_test()






