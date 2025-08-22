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
# # --- ДАННЫЕ ДЛЯ ОТПРАВКИ РЕАЛЬНОГО SMS ---
#
# # ВАЖНО: Укажите ваш РЕАЛЬНЫЙ номер телефона в международном формате (начиная с 7)
# REAL_PHONE_NUMBER = "79952116323"
#
# # Текст сообщения, который будет отправлен
# MESSAGE_TO_SEND = f"Проверка API {time.strftime('%H:%M:%S')}. Если вы получили это сообщение, все работает."
#
# # Системное имя для таблицы, где будут храниться логи отправки
# SMS_LOG_TABLE_NAME = "sms_sending_log"
#
# # ----------------------------------------------------
#
# def print_status(ok, message):
#     if ok: print(f"✅ [SUCCESS] {message}")
#     else: print(f"❌ [FAILURE] {message}"); exit(1)
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
# # --- Основная функция ---
#
# def send_real_sms():
#     try:
#         # --- ШАГ 1: АВТОРИЗАЦИЯ И ПОДГОТОВКА СРЕДЫ ---
#         print_header("ШАГ 1: ПОДГОТОВКА")
#
#         # 1.1. Регистрация или вход
#         unique_id = int(time.time())
#         email = f"real_sms_sender_{unique_id}@example.com"
#         password = "password123"
#         reg_payload = {"email": email, "password": password, "full_name": "Real SMS Sender", "registration_token": CORRECT_REGISTRATION_TOKEN}
#         requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#         auth_payload = {'username': email, 'password': password}
#         token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#         print(f" -> Авторизация прошла успешно.")
#
#         # 1.2. Проверка и создание таблицы для логов
#         meta_response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
#         existing_tables = {t['name'] for t in meta_response.json()}
#         if SMS_LOG_TABLE_NAME not in existing_tables:
#             print(f" -> Таблица '{SMS_LOG_TABLE_NAME}' не найдена, создаем...")
#             table_config = {"name": SMS_LOG_TABLE_NAME, "display_name": "Логи отправки SMS"}
#             requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).raise_for_status()
#             print(f" -> Таблица успешно создана.")
#         else:
#             print(f" -> Таблица '{SMS_LOG_TABLE_NAME}' уже существует.")
#
#         # --- ШАГ 2: СОЗДАНИЕ ЗАПИСИ ДЛЯ ОТПРАВКИ ---
#         print_header("ШАГ 2: СОЗДАНИЕ ЗАПИСИ И ЗАПУСК ОТПРАВКИ")
#
#         payload = {
#             "phone_number": REAL_PHONE_NUMBER,
#             "message_text": MESSAGE_TO_SEND,
#         }
#         create_response = requests.post(f"{BASE_URL}/api/data/{SMS_LOG_TABLE_NAME}", headers=headers, json=payload)
#         create_response.raise_for_status()
#         entity_id = create_response.json()['id']
#         print(f" -> Создана запись для отправки с ID: {entity_id}")
#
#         # --- ШАГ 3: ЗАПУСК ТРИГГЕРА ---
#         update_url = f"{BASE_URL}/api/data/{SMS_LOG_TABLE_NAME}/{entity_id}"
#         trigger_response = requests.put(update_url, headers=headers, json={"send_sms_trigger": True})
#         trigger_response.raise_for_status()
#
#         initial_status = trigger_response.json().get('sms_status')
#         print_status(
#             initial_status == 'pending',
#             f" -> Триггер успешно запущен. Статус записи: '{initial_status}'."
#         )
#
#         # --- ШАГ 4: МОНИТОРИНГ СТАТУСА ---
#         print_header("ШАГ 4: МОНИТОРИНГ")
#
#         for i in range(30): # Проверяем 10 раз с интервалом 3 секунды (всего 30 секунд)
#             print(f" -> Попытка {i+1}/10: Проверяем статус...")
#             time.sleep(3)
#
#             status_response = requests.get(update_url, headers=headers)
#             current_status = status_response.json().get('sms_status')
#
#             if current_status != 'pending':
#                 print(f" -> Статус изменился на '{current_status}'!")
#
#                 if current_status == 'sent':
#                     print_status(True, "Бэкенд сообщает, что SMS успешно отправлен.")
#                 elif current_status == 'error':
#                     last_error = status_response.json().get('sms_last_error')
#                     print_status(False, f"Бэкенд сообщает об ошибке отправки: {last_error}")
#                 else:
#                     print_status(False, f"Неизвестный финальный статус: {current_status}")
#
#                 return # Завершаем скрипт
#
#         print_status(False, "Статус не изменился с 'pending' за 30 секунд. Проверьте логи Celery воркера.")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP.")
#         print(f"URL: {e.request.method} {e.request.url}")
#         print(f"Статус: {e.response.status_code}")
#         print(f"Ответ: {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
#
# if __name__ == "__main__":
#     send_real_sms()


import requests
import json
import time
from datetime import datetime, timedelta
from faker import Faker

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"  # ИЛИ "http://89.111.169.47:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"

# --- Данные пользователя для теста ---
USER_EMAIL = "user@example.com"
USER_PASSWORD = "string"

# -----------------
fake = Faker('ru_RU')


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


def login(email, password):
    """
    Авторизуется под существующим пользователем.
    В случае ошибки выбрасывает исключение.
    Возвращает словарь с заголовком Authorization для последующих запросов.
    """
    print(f" -> Попытка входа под пользователем: {email}...")

    # Формируем тело запроса (form-data)
    auth_payload = {
        'username': email,
        'password': password
    }

    # Отправляем POST запрос
    auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)

    # Проверяем, что запрос прошел успешно. Если нет (например, 401 Unauthorized),
    # requests выбросит исключение HTTPError, которое будет поймано в основном блоке try...except.
    auth_response.raise_for_status()

    # Извлекаем токен из успешного ответа
    token = auth_response.json()['access_token']

    # Формируем и возвращаем заголовок
    return {'Authorization': f'Bearer {token}'}

def run_filtering_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
        headers = login(USER_EMAIL, USER_PASSWORD)
        print(" -> Авторизация успешна.")

        table_name = f"employees_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Сотрудники"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        attributes = [
            {"name": "full_name", "display_name": "ФИО", "value_type": "string"},
            {"name": "department", "display_name": "Отдел", "value_type": "string"},
            {"name": "salary", "display_name": "Зарплата", "value_type": "integer"},
            {"name": "hire_date", "display_name": "Дата найма", "value_type": "date"},
            {"name": "is_active", "display_name": "Активен", "value_type": "boolean"},
        ]
        for attr in attributes:
            requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                          json=attr).raise_for_status()

        # --- ШАГ 2: НАПОЛНЕНИЕ ДАННЫМИ ---
        print_header("ШАГ 2: НАПОЛНЕНИЕ ТАБЛИЦЫ РАЗНООБРАЗНЫМИ ДАННЫМИ")

        test_data = [
            {"full_name": "Иванов Иван", "department": "Продажи", "salary": 75000, "hire_date": "2023-05-10T10:00:00",
             "is_active": True},
            {"full_name": "Петрова Анна", "department": "Маркетинг", "salary": 90000,
             "hire_date": "2022-11-20T10:00:00", "is_active": True},
            {"full_name": "Сидоров Петр", "department": "Продажи", "salary": 85000, "hire_date": "2024-01-15T10:00:00",
             "is_active": True},
            {"full_name": "Кузнецова Ольга", "department": "Разработка", "salary": 120000,
             "hire_date": "2021-03-01T10:00:00", "is_active": False},
            {"full_name": "Васильев Иван", "department": "Разработка", "salary": 150000,
             "hire_date": "2024-02-20T10:00:00", "is_active": True},
        ]
        for item in test_data:
            requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=item).raise_for_status()

        print_status(True, "5 тестовых записей успешно созданы.")

        # --- ШАГ 3: ТЕСТИРОВАНИЕ ФИЛЬТРОВ ---
        print_header("ШАГ 3: ТЕСТЫ ФИЛЬТРАЦИИ")

        # Тест 1: Точное совпадение строки
        print("\n -> Тест 1: Найти всех из отдела 'Продажи' (ожидается 2)")
        filters1 = [{"field": "department", "op": "eq", "value": "Продажи"}]
        params1 = {"filters": json.dumps(filters1)}
        resp1 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params1).json()
        print_status(len(resp1) == 2, f"Найдено {len(resp1)} записей.")

        # Тест 2: Число больше чем
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        print("\n -> Тест 2: Найти всех с зарплатой > 80000 (ожидается 4)")
        filters2 = [{"field": "salary", "op": "gt", "value": 80000}]
        params2 = {"filters": json.dumps(filters2)}
        resp2 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params2).json()
        print_status(len(resp2) == 4, f"Найдено {len(resp2)} записей.")
        # ---------------------------

        # Тест 3: Булево значение
        print("\n -> Тест 3: Найти всех неактивных (is_active = false, ожидается 1)")
        filters3 = [{"field": "is_active", "op": "eq", "value": False}]
        params3 = {"filters": json.dumps(filters3)}
        resp3 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params3).json()
        print_status(len(resp3) == 1 and resp3[0]['full_name'] == "Кузнецова Ольга", f"Найдено {len(resp3)} записей.")

        # Тест 4: Дата больше чем
        print("\n -> Тест 4: Найти всех, кто нанят после 01.01.2024 (ожидается 2)")
        filters4 = [{"field": "hire_date", "op": "gte", "value": "2024-01-01T00:00:00"}]
        params4 = {"filters": json.dumps(filters4)}
        resp4 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params4).json()
        print_status(len(resp4) == 2, f"Найдено {len(resp4)} записей.")

        # Тест 5: Частичное совпадение строки
        print("\n -> Тест 5: Найти всех, у кого в имени есть 'Иван' (ожидается 2)")
        filters5 = [{"field": "full_name", "op": "contains", "value": "Иван"}]
        params5 = {"filters": json.dumps(filters5)}
        resp5 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params5).json()
        print_status(len(resp5) == 2, f"Найдено {len(resp5)} записей.")

        # Тест 6: Комбинированный фильтр
        print("\n -> Тест 6: Найти активных из отдела 'Продажи' с ЗП > 80000 (ожидается 1)")
        filters6 = [
            {"field": "is_active", "value": True},
            {"field": "department", "value": "Продажи"},
            {"field": "salary", "op": "gt", "value": 80000},
        ]
        params6 = {"filters": json.dumps(filters6)}
        resp6 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params6).json()
        print_status(len(resp6) == 1 and resp6[0]['full_name'] == "Сидоров Петр", f"Найдено {len(resp6)} записей.")
        print(resp6)
        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ ФИЛЬТРАЦИИ ДАННЫХ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e.response.status_code} {e.response.reason}")
    except Exception as e:
        print(f"Ошибка HTTP: {e.response.status_code} {e.response.reason}")




# Вставьте сюда вашу рабочую функцию login
def login(email, password):
    auth_payload = {'username': email, 'password': password}
    auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
    auth_response.raise_for_status()
    token = auth_response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


if __name__ == "__main__":
    run_filtering_test()