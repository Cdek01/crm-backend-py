# import requests
# import json
# from faker import Faker
# import time
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
#
# # BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# BASE_URL = "http://89.111.169.47:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
#
# # --- Данные нового пользователя ---
# # NEW_USER_EMAIL = "new.user@example.com"
# # NEW_USER_PASSWORD = "Password123!"
# # NEW_USER_FULL_NAME = "Иван Иванов"
# # --- Данные пользователя, чьи права мы проверяем ---
# USER_EMAIL = "new.user@example.com"
# USER_PASSWORD = "Password123!"
#
# # --- Список системных имен таблиц для проверки ---
# TABLES_TO_TEST = [
#     "leads_custom",
#     "archived_leads",
#     "monitoring",
#     "deals",
#     "contracts",
#     "founders_directors",
# ]
#
# # ----------------------------------------------------------------------
# fake = Faker('ru_RU')
#
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
#
# def run_permission_test():
#     print_header(f"ПРОВЕРКА ПРАВ ДОСТУПА ДЛЯ ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")
#
#     try:
#         # --- ШАГ 1: АВТОРИЗАЦИЯ И ПОЛУЧЕНИЕ ПРАВ ---
#         print("\n--- Шаг 1: Авторизация и получение списка реальных прав ---")
#         auth_payload = {'username': USER_EMAIL, 'password': USER_PASSWORD}
#         auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
#
#         if auth_response.status_code != 200:
#             print(
#                 f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться. Проверьте email и пароль. Ответ: {auth_response.text}")
#             return
#
#         token = auth_response.json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#
#         me_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
#         user_permissions = set(me_response.json().get("permissions", []))
#
#         print(f"✅ Пользователь успешно авторизован.")
#         print(f"✅ Сервер сообщает, что у пользователя {len(user_permissions)} прав:")
#         for perm in sorted(list(user_permissions)):
#             print(f"   - {perm}")
#
#         # --- ШАГ 2: ЦИКЛ ПРОВЕРКИ ТАБЛИЦ ---
#         for table_name in TABLES_TO_TEST:
#             print_header(f"ПРОВЕРКА ТАБЛИЦЫ: '{table_name}'")
#
#             # --- 2.1 Проверка на ПРОСМОТР (GET) ---
#             print(f"\n -> 1. Попытка просмотра (GET /api/data/{table_name})")
#             view_permission_needed = f"data:view:{table_name}"
#
#             get_response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
#
#             if get_response.status_code == 200:
#                 print(f"   ✅ [УСПЕХ] Доступ на просмотр есть (статус 200).")
#                 if view_permission_needed not in user_permissions:
#                     print(f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ есть, но права '{view_permission_needed}' нет в списке!")
#             elif get_response.status_code == 403:
#                 print(f"   ✅ [КОРРЕКТНО ЗАБЛОКИРОВАНО] Доступ на просмотр запрещен (статус 403).")
#                 if view_permission_needed in user_permissions:
#                     print(
#                         f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ запрещен, хотя право '{view_permission_needed}' есть в списке!")
#             else:
#                 print(f"   ❌ [ОШИБКА] Неожиданный статус ответа: {get_response.status_code} - {get_response.text}")
#
#             # --- 2.2 Проверка на СОЗДАНИЕ (POST) ---
#             print(f"\n -> 2. Попытка создания (POST /api/data/{table_name})")
#             create_permission_needed = f"data:create:{table_name}"
#             # Отправляем минимально необходимые данные
#             post_payload = {"test_field": f"test_value_{int(time.time())}"}
#
#             post_response = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=post_payload)
#
#             # Для создания успешный статус - 201
#             if post_response.status_code == 201:
#                 print(f"   ✅ [УСПЕХ] Доступ на создание есть (статус 201).")
#                 if create_permission_needed not in user_permissions:
#                     print(f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ есть, но права '{create_permission_needed}' нет в списке!")
#             elif post_response.status_code == 403:
#                 print(f"   ✅ [КОРРЕКТНО ЗАБЛОКИРОВАНО] Доступ на создание запрещен (статус 403).")
#                 if create_permission_needed in user_permissions:
#                     print(
#                         f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Доступ запрещен, хотя право '{create_permission_needed}' есть в списке!")
#             else:
#                 print(f"   ❌ [ОШИБКА] Неожиданный статус ответа: {post_response.status_code} - {post_response.text}")
#
#         print("\n" + "=" * 60)
#         print("ПРОВЕРКА ПРАВ ЗАВЕРШЕНА.")
#
#     except Exception as e:
#         print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА В СКРИПТЕ: {e}")
#
#
# if __name__ == "__main__":
#     run_permission_test()


import requests
import json
import time
from faker import Faker

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "new.user@example.com"
USER_PASSWORD = "Password123!"

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
    print_header(f"ПРОВЕРКА ПРАВ ДОСТУПА И ВЫВОД ДАННЫХ ДЛЯ: {USER_EMAIL}")

    try:
        # --- ШАГ 1: АВТОРИЗАЦИЯ ---
        print("\n--- Шаг 1: Авторизация ---")
        auth_payload = {'username': USER_EMAIL, 'password': USER_PASSWORD}
        auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        auth_response.raise_for_status()
        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print(f"✅ Пользователь успешно авторизован.")

        # --- ШАГ 2: ЦИКЛ ПРОВЕРКИ И ВЫВОДА ДАННЫХ ---
        for table_name in TABLES_TO_TEST:
            print_header(f"ТАБЛИЦА: '{table_name}'")

            print(f"\n -> Попытка просмотра (GET /api/data/{table_name})...")
            get_response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)

            # --- ИЗМЕНЕНИЕ ЗДЕСЬ: ДОБАВЛЯЕМ ЛОГИКУ ВЫВОДА ДАННЫХ ---
            if get_response.status_code == 200:
                print(f"   ✅ [УСПЕХ] Доступ на просмотр есть (статус 200).")

                table_data = get_response.json()

                if not table_data:
                    print("   -> Таблица пуста.")
                else:
                    print(f"   -> Получено {len(table_data)} записей. Содержимое:")
                    # Красиво выводим каждую запись
                    for i, record in enumerate(table_data, 1):
                        print(f"\n   --- Запись #{i} ---")
                        # Используем json.dumps для красивого форматирования
                        print(json.dumps(record, indent=4, ensure_ascii=False))
            # -------------------------------------------------------

            elif get_response.status_code == 403:
                print(f"   ℹ️  [ДОСТУП ЗАПРЕЩЕН] Пользователь не имеет права 'data:view:{table_name}' (статус 403).")
            elif get_response.status_code == 404:
                print(
                    f"   ⚠️  [ТАБЛИЦА НЕ НАЙДЕНА] Таблицы с именем '{table_name}' не существует для этого пользователя (статус 404).")
            else:
                print(f"   ❌ [ОШИБКА] Неожиданный статус ответа: {get_response.status_code} - {get_response.text}")

        print("\n" + "=" * 60)
        print("ПРОВЕРКА ЗАВЕРШЕНА.")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА HTTP: Не удалось авторизоваться или произошел сбой.")
        print(f"   Статус: {e.response.status_code}, Ответ: {e.response.text}")
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА В СКРИПТЕ: {e}")


if __name__ == "__main__":
    run_permission_test()