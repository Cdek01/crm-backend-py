# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ ---
# BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005"
# REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
# # --- Данные для создания ---
# OWNER_A_EMAIL = "owner-a@example.com"
# OWNER_A_PASS = "password-a"
# OWNER_A_TABLE_NAME = "reports_a"
# OWNER_A_TABLE_DISPLAY_NAME = "Отчеты Компании А"
#
# USER_B_EMAIL = "user-b@example.com"
# USER_B_PASS = "password-b"
# USER_B_TABLE_NAME = "tasks_b"
# USER_B_TABLE_DISPLAY_NAME = "Задачи Компании Б"
#
#
# # -----------------
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
#
# def register(email, password, full_name):
#     print(f" -> Регистрация пользователя {email}...")
#     payload = {"email": email, "password": password, "full_name": full_name, "registration_token": REGISTRATION_TOKEN}
#     resp = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
#     if resp.status_code == 400 and "уже существует" in resp.text:
#         print(f" -> Пользователь {email} уже существует.")
#         return False  # Не новый
#     resp.raise_for_status()
#     print(f" -> Пользователь {email} успешно создан.")
#     return True  # Новый
#
#
# def login(email, password):
#     payload = {'username': email, 'password': password}
#     resp = requests.post(f"{BASE_URL}/api/auth/token", data=payload)
#     resp.raise_for_status()
#     token = resp.json()['access_token']
#     return {'Authorization': f'Bearer {token}'}
#
#
# def create_table(headers, name, display_name):
#     print(f" -> Создание таблицы '{display_name}' ({name})...")
#     payload = {"name": name, "display_name": display_name}
#     resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=payload)
#     if resp.status_code == 400 and "уже существует" in resp.text:
#         print(f" -> Таблица '{name}' уже существует.")
#         return
#     resp.raise_for_status()
#     table_id = resp.json()['id']
#     # Добавим одну колонку для наглядности
#     attr_payload = {"name": "title", "display_name": "Название", "value_type": "string"}
#     requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
#                   json=attr_payload).raise_for_status()
#     print(f" -> Таблица '{name}' успешно создана/проверена.")
#
#
# def populate_data(headers, table_name, count):
#     print(f" -> Заполнение таблицы '{table_name}' данными...")
#     for i in range(count):
#         data = {"title": f"Тестовая запись #{i + 1} для {table_name}"}
#         requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=data).raise_for_status()
#     print(f" -> Добавлено {count} записей.")
#
#
# def prepare_environment():
#     print_header("ЭТАП 1: ПОДГОТОВКА ТЕСТОВОЙ СРЕДЫ")
#
#     # --- Создаем Владельца А и его окружение ---
#     print("\n--- Создание Владельца А ---")
#     register(OWNER_A_EMAIL, OWNER_A_PASS, "Владелец А")
#     owner_a_headers = login(OWNER_A_EMAIL, OWNER_A_PASS)
#     create_table(owner_a_headers, OWNER_A_TABLE_NAME, OWNER_A_TABLE_DISPLAY_NAME)
#     populate_data(owner_a_headers, OWNER_A_TABLE_NAME, 3)  # Добавим 3 записи
#
#     # --- Создаем Пользователя Б и его окружение ---
#     print("\n--- Создание Пользователя Б ---")
#     register(USER_B_EMAIL, USER_B_PASS, "Пользователь Б")
#     user_b_headers = login(USER_B_EMAIL, USER_B_PASS)
#     create_table(user_b_headers, USER_B_TABLE_NAME, USER_B_TABLE_DISPLAY_NAME)
#     populate_data(user_b_headers, USER_B_TABLE_NAME, 2)  # Добавим 2 записи
#
#     print("\n" + "=" * 60)
#     print("✅ Среда готова. Теперь вы можете настроить права в админ-панели.")
#     print("\nЗАДАЧА:")
#     print(f"1. Зайдите в админку.")
#     print(f"2. Создайте роль для тенанта 'Компания {USER_B_EMAIL}'.")
#     print(
#         f"3. Дайте этой роли право на просмотр таблицы Владельца А. Имя права будет: 'data:view:{OWNER_A_TABLE_NAME}'")
#     print(f"4. Назначьте эту роль пользователю '{USER_B_EMAIL}'.")
#
#
# if __name__ == "__main__":
#     prepare_environment()

import requests
import json

# --- НАСТРОЙКИ (Должны совпадать со скриптом подготовки) ---
BASE_URL = "http://127.0.0.1:8005"

OWNER_A_TABLE_NAME = "reports_a"
USER_B_EMAIL = "user-b@example.com"
USER_B_PASS = "password-b"
USER_B_TABLE_NAME = "tasks_b"


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


def login(email, password):
    payload = {'username': email, 'password': password}
    resp = requests.post(f"{BASE_URL}/api/auth/token", data=payload)
    resp.raise_for_status()
    token = resp.json()['access_token']
    return {'Authorization': f'Bearer {token}'}

def verify_access():
    print_header(f"ЭТАП 3: ПРОВЕРКА ДОСТУПА ДЛЯ {USER_B_EMAIL}")

    try:
        # 1. Авторизация под Пользователем Б
        user_b_headers = login(USER_B_EMAIL, USER_B_PASS)
        print(" -> Авторизация под Пользователем Б успешна.")

        # 2. Проверка видимости структур таблиц
        print("\n--- Проверка списка видимых таблиц ---")
        meta_resp = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=user_b_headers)
        meta_resp.raise_for_status()
        visible_tables = meta_resp.json()
        visible_names = {t['name'] for t in visible_tables}

        print(f" -> Пользователь видит таблицы: {visible_names}")
        print_status(USER_B_TABLE_NAME in visible_names, "Пользователь видит СВОЮ таблицу.")
        print_status(OWNER_A_TABLE_NAME in visible_names, "Пользователь видит ОБЩУЮ таблицу Владельца А.")

        # 3. Проверка доступа к ДАННЫМ
        print("\n--- Проверка доступа к данным в таблицах ---")

        # 3.1 Доступ к своей таблице
        own_data_resp = requests.get(f"{BASE_URL}/api/data/{USER_B_TABLE_NAME}", headers=user_b_headers)
        own_data_resp.raise_for_status()
        print_status(
            len(own_data_resp.json()) == 2,
            f"Пользователь видит свои данные ({len(own_data_resp.json())} из 2 записей)."
        )

        # 3.2 Доступ к общей таблице
        shared_data_resp = requests.get(f"{BASE_URL}/api/data/{OWNER_A_TABLE_NAME}", headers=user_b_headers)
        if shared_data_resp.status_code == 403:
            print_status(False, "Доступ к данным ОБЩЕЙ таблицы запрещен (403). Проверьте права в роли.")
        shared_data_resp.raise_for_status()

        print_status(
            len(shared_data_resp.json()) == 3,
            f"Пользователь видит данные из ОБЩЕЙ таблицы ({len(shared_data_resp.json())} из 3 записей)."
        )

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ ДЕЛЕГИРОВАНИЯ ДОСТУПА ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP.")
    except Exception as e:
        print(f"\n❌ ОШИБКА HTTP.")


# ... (обработка ошибок)

# Вставьте сюда функцию login()
def login(email, password):
    payload = {'username': email, 'password': password}
    resp = requests.post(f"{BASE_URL}/api/auth/token", data=payload)
    resp.raise_for_status()
    token = resp.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


if __name__ == "__main__":
    verify_access()