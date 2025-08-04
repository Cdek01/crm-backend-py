# import requests
# import json
# import random
# from faker import Faker
# import time
#
# # --- НАСТРОЙКИ ---
# BASE_URL = "http://127.0.0.1:8005"  # Укажите адрес вашего запущенного сервера
# # BASE_URL = "http://89.111.169.47:8005" # Пример для удаленного сервера
#
# # Инициализируем Faker для генерации случайных данных
# fake = Faker("ru_RU")
#
#
# # --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КРАСИВОГО ВЫВОДА ---
#
# def print_header(title):
#     print("\n" + "=" * 80)
#     print(f" {title.upper()} ".center(80, "="))
#     print("=" * 80)
#
#
# def print_request(method, url, payload=None, headers=None):
#     print(f">>> REQUEST: {method} {url}")
#     if payload:
#         print(f"    Payload: {json.dumps(payload, indent=4, ensure_ascii=False)}")
#     if headers and "Authorization" in headers:
#         print("    Headers: Authorization: Bearer <TOKEN>")
#
#
# def print_response(response):
#     print(f"<<< RESPONSE: {response.status_code}")
#     try:
#         # Пытаемся красиво напечатать JSON
#         print(json.dumps(response.json(), indent=4, ensure_ascii=False))
#     except json.JSONDecodeError:
#         # Если ответ не JSON, печатаем как текст
#         print(response.text)
#
#
# def check_test_result(title, condition, success_msg="[PASS]", failure_msg="[FAIL]"):
#     """Проверяет условие и выводит результат теста."""
#     if condition:
#         print(f"✅ {success_msg} {title}")
#     else:
#         print(f"❌ {failure_msg} {title}")
#
#
# # --- ОСНОВНОЙ СКРИПТ ---
#
# def run_api_tests():
#     session = requests.Session()
#     access_token = None
#
#     # Уникальный идентификатор для этого запуска, чтобы избежать конфликтов
#     run_id = int(time.time())
#
#     # 1. РЕГИСТРАЦИЯ
#     print_header("1. Регистрация нового пользователя")
#     user_email = f"testuser_{run_id}@example.com"
#     user_password = "strong_password_123"
#     register_payload = {
#         "email": user_email,
#         "password": user_password,
#         "full_name": fake.name()
#     }
#     print_request("POST", f"{BASE_URL}/api/auth/register", register_payload)
#     response = session.post(f"{BASE_URL}/api/auth/register", json=register_payload)
#     print_response(response)
#     check_test_result("Регистрация успешна", response.status_code == 201)
#
#     # 2. ВХОД В СИСТЕМУ
#     print_header("2. Вход в систему и получение токена")
#     login_payload = {
#         "username": user_email,
#         "password": user_password
#     }
#     print_request("POST", f"{BASE_URL}/api/auth/token", login_payload)
#     response = session.post(f"{BASE_URL}/api/auth/token", data=login_payload)
#     print_response(response)
#     if response.status_code == 200:
#         access_token = response.json().get("access_token")
#         check_test_result("Получение токена успешно", access_token is not None)
#     else:
#         check_test_result("Получение токена провалено", False)
#         return  # Выход, если не удалось войти
#
#     headers = {"Authorization": f"Bearer {access_token}"}
#
#     # 3. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ
#     print_header("3. Создание тестовых данных")
#     # Создаем лиды
#     session.post(f"{BASE_URL}/api/leads/", headers=headers,
#                  json={"organization_name": "Alpha Project", "lead_status": "New", "rating": 5})
#     session.post(f"{BASE_URL}/api/leads/", headers=headers,
#                  json={"organization_name": "Beta Services", "lead_status": "In Progress", "rating": 3})
#     session.post(f"{BASE_URL}/api/leads/", headers=headers,
#                  json={"organization_name": "Gamma Inc", "lead_status": "New", "rating": 4})
#     print("✅ Создано 3 тестовых лида.")
#
#     # Создаем юр. лица
#     session.post(f"{BASE_URL}/api/legal-entities/", headers=headers,
#                  json={"short_name": "StroyMontazh", "inn": f"7701{run_id % 1000000:06}", "status": "Действующая",
#                        "revenue": 1000000})
#     session.post(f"{BASE_URL}/api/legal-entities/", headers=headers,
#                  json={"short_name": "AgroProm", "inn": f"7702{run_id % 1000000:06}", "status": "Действующая",
#                        "revenue": 5000000})
#     session.post(f"{BASE_URL}/api/legal-entities/", headers=headers,
#                  json={"short_name": "IT Solutions", "inn": f"7703{run_id % 1000000:06}",
#                        "status": "В процессе ликвидации", "revenue": 250000})
#     print("✅ Создано 3 тестовых юр. лица.")
#
#     # Создаем физ. лиц
#     session.post(f"{BASE_URL}/api/individuals/", headers=headers,
#                  json={"full_name": "Иванов Иван Иванович", "email": f"ivanov_{run_id}@test.com"})
#     session.post(f"{BASE_URL}/api/individuals/", headers=headers,
#                  json={"full_name": "Петров Петр Петрович", "email": f"petrov_{run_id}@test.com"})
#     session.post(f"{BASE_URL}/api/individuals/", headers=headers,
#                  json={"full_name": "Сидоров Сидор Сидорович", "email": f"sidorov_{run_id}@test.com"})
#     print("✅ Создано 3 тестовых физ. лица.")
#
#     # 4. ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ И СОРТИРОВКИ
#     print_header("4. Тестирование эндпоинтов")
#
#     # --- ТЕСТЫ ДЛЯ ЛИДОВ ---
#     print("\n--- Тестируем /api/leads/ ---")
#     url = f"{BASE_URL}/api/leads?lead_status=New"
#     response = session.get(url, headers=headers)
#     print_request("GET", url)
#     check_test_result("Фильтрация лидов по статусу 'New'",
#                       response.status_code == 200 and len(response.json()) == 2)
#
#     url = f"{BASE_URL}/api/leads?sort_by=rating&sort_order=desc"
#     response = session.get(url, headers=headers)
#     print_request("GET", url)
#     data = response.json()
#     ratings = [item['rating'] for item in data]
#     check_test_result("Сортировка лидов по рейтингу (desc)",
#                       response.status_code == 200 and ratings == [5, 4, 3])
#
#     # --- ТЕСТЫ ДЛЯ ЮР. ЛИЦ ---
#     print("\n--- Тестируем /api/legal-entities/ ---")
#     url = f"{BASE_URL}/api/legal-entities?status=Действующая"
#     response = session.get(url, headers=headers)
#     print_request("GET", url)
#     check_test_result("Фильтрация юр. лиц по статусу 'Действующая'",
#                       response.status_code == 200 and len(response.json()) == 2)
#
#     url = f"{BASE_URL}/api/legal-entities?sort_by=revenue&sort_order=asc"
#     response = session.get(url, headers=headers)
#     print_request("GET", url)
#     data = response.json()
#     revenues = [item['revenue'] for item in data]
#     check_test_result("Сортировка юр. лиц по выручке (asc)",
#                       response.status_code == 200 and revenues == [250000, 1000000, 5000000])
#
#     # --- ТЕСТЫ ДЛЯ ФИЗ. ЛИЦ ---
#     print("\n--- Тестируем /api/individuals/ ---")
#     url = f"{BASE_URL}/api/individuals?full_name=Иван"  # Поиск по части имени
#     response = session.get(url, headers=headers)
#     print_request("GET", url)
#     check_test_result("Фильтрация физ. лиц по части имени 'Иван'",
#                       response.status_code == 200 and len(response.json()) == 1)
#
#     url = f"{BASE_URL}/api/individuals?sort_by=full_name&sort_order=desc"
#     response = session.get(url, headers=headers)
#     print_request("GET", url)
#     data = response.json()
#     names = [item['full_name'] for item in data]
#     check_test_result("Сортировка физ. лиц по ФИО (desc)",
#                       response.status_code == 200 and names == ["Сидоров Сидор Сидорович", "Петров Петр Петрович",
#                                                                 "Иванов Иван Иванович"])
#
#
# if __name__ == "__main__":
#     run_api_tests()


# test_bulk_delete.py
import requests
import json
import time

# --- НАСТРОЙТЕ ЭТИ ПЕРЕМЕННЫЕ ---
BASE_URL = "http://127.0.0.1:8005"  # IP-адрес вашего локального сервера

# Мы будем генерировать уникального пользователя для каждого теста
UNIQUE_ID = int(time.time())
USER_EMAIL = f"bulk_delete_tester_{UNIQUE_ID}@example.com"
USER_PASSWORD = "a_very_secure_password_123!"


# ---------------------------------

def print_status(ok, message):
    """Выводит красивый статус операции."""
    if ok:
        print(f"✅ [SUCCESS] {message}")
    else:
        print(f"❌ [FAILURE] {message}")
        # Завершаем скрипт при первой же ошибке
        exit(1)


def run_bulk_delete_test():
    """
    Выполняет полный цикл тестирования массового удаления:
    1. Регистрация и вход.
    2. Создание 3-х тестовых записей (физ. лиц).
    3. Вызов эндпоинта для массового удаления 2-х из них.
    4. Проверка ответа и последствий удаления.
    """
    token = None
    headers = {}
    individual_ids = []

    try:
        # --- ШАГ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ ---
        print("-" * 50)
        print("1. РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ")
        # Регистрация
        register_payload = {"email": USER_EMAIL, "password": USER_PASSWORD, "full_name": "Bulk Tester"}
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
        register_response.raise_for_status()
        # Вход
        auth_payload_form = {'username': USER_EMAIL, 'password': USER_PASSWORD}
        auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload_form)
        auth_response.raise_for_status()
        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print_status(True, "Успешно зарегистрирован и получен токен.")

        # --- ШАГ 2: СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ---
        print("-" * 50)
        print("2. СОЗДАНИЕ 3-Х ФИЗИЧЕСКИХ ЛИЦ")
        individuals_to_create = [
            {"full_name": "Иванов Иван (на удаление)"},
            {"full_name": "Петров Петр (на удаление)"},
            {"full_name": "Сидоров Сидор (останется)"}
        ]

        for ind_data in individuals_to_create:
            response = requests.post(f"{BASE_URL}/api/individuals/", headers=headers, json=ind_data)
            response.raise_for_status()
            created_id = response.json()['id']
            individual_ids.append(created_id)
            print(f"   -> Создано физ. лицо '{ind_data['full_name']}' с ID: {created_id}")

        print_status(True, f"Успешно создано {len(individual_ids)} записи.")

        # --- ШАГ 3: ВЫПОЛНЕНИЕ МАССОВОГО УДАЛЕНИЯ ---
        print("-" * 50)
        print("3. ВЫПОЛНЕНИЕ МАССОВОГО УДАЛЕНИЯ")
        ids_to_delete = individual_ids[:2]  # Берем первые два ID
        id_to_keep = individual_ids[2]  # Последний ID оставляем для проверки

        print(f"   -> Отправка запроса на удаление ID: {ids_to_delete}")

        delete_payload = {"ids": ids_to_delete}
        delete_response = requests.delete(f"{BASE_URL}/api/individuals/bulk-delete", headers=headers,
                                          json=delete_payload)
        delete_response.raise_for_status()

        deleted_count = delete_response.json().get("deleted_count")

        print_status(
            deleted_count == len(ids_to_delete),
            f"Сервер вернул корректный ответ. Удалено записей: {deleted_count}"
        )

        # --- ШАГ 4: ПРОВЕРКА ПОСЛЕДСТВИЙ ---
        print("-" * 50)
        print("4. ПРОВЕРКА РЕЗУЛЬТАТОВ УДАЛЕНИЯ")

        # 4.1. Проверяем, что удаленные записи действительно не существуют
        for deleted_id in ids_to_delete:
            check_response = requests.get(f"{BASE_URL}/api/individuals/{deleted_id}", headers=headers)
            print_status(
                check_response.status_code == 404,
                f"Запись с ID {deleted_id} успешно удалена (получен статус 404)."
            )

        # 4.2. Проверяем, что оставшаяся запись на месте
        check_response = requests.get(f"{BASE_URL}/api/individuals/{id_to_keep}", headers=headers)
        check_response.raise_for_status()
        print_status(
            check_response.status_code == 200,
            f"Запись с ID {id_to_keep} не была удалена и доступна."
        )

        # 4.3. Проверяем общий список
        list_response = requests.get(f"{BASE_URL}/api/individuals/", headers=headers)
        list_response.raise_for_status()
        remaining_count = len(list_response.json())
        print_status(
            remaining_count == 1,
            f"В общем списке осталась {remaining_count} запись, как и ожидалось."
        )

        print("-" * 50)
        print("\n🎉 ВСЕ ТЕСТЫ ДЛЯ МАССОВОГО УДАЛЕНИЯ ПРОШЛИ УСПЕШНО! 🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP на шаге, который выполнялся последним.")
        print(f"URL запроса: {e.request.method} {e.request.url}")
        if e.request.body:
            # Печатаем тело запроса, если оно есть
            try:
                # Пытаемся декодировать как JSON для читаемости
                body = json.loads(e.request.body)
                print(f"Тело запроса: {json.dumps(body, indent=2, ensure_ascii=False)}")
            except:
                print(f"Тело запроса: {e.request.body}")
        print(f"Статус код: {e.response.status_code}")
        print(f"Ответ сервера: {e.response.text}")
    except Exception as e:
        print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА")
        print(f"Ошибка: {e}")


# Запускаем наш тест
if __name__ == "__main__":
    run_bulk_delete_test()