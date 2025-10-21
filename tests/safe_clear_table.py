# import requests
# import time
# from tqdm import tqdm
# import sys
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
# BASE_URL = "http://89.111.169.47:8005"
# EMAIL = "1@example.com"
# PASSWORD = "string"
#
# # Размер порции, которую мы получаем и удаляем за один цикл.
# # Не делайте это значение слишком большим, чтобы не нагружать GET-запрос.
# BATCH_SIZE = 100
# # Небольшая задержка между DELETE-запросами (в секундах), чтобы не перегрузить сервер.
# # 0.05 = 50 миллисекунд. Установите 0, если уверены в мощности сервера.
# DELAY_BETWEEN_DELETES = 0
# # ---------------------------------------------------
#
# # --- Вспомогательные функции ---
# def print_status(ok, message):
#     if ok:
#         print(f"✅ [INFO] {message}")
#     else:
#         print(f"❌ [FAIL] {message}")
#         sys.exit(1)
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
# def login():
#     """Аутентифицируется и возвращает заголовки для авторизации."""
#     print_header("Шаг 1: Авторизация")
#     try:
#         auth_payload = {'username': EMAIL, 'password': PASSWORD}
#         token_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
#         token_response.raise_for_status()
#         token = token_response.json()['access_token']
#         print_status(True, f"Успешная авторизация для пользователя {EMAIL}")
#         return {'Authorization': f'Bearer {token}'}
#     except Exception as e:
#         print_status(False, f"Критическая ошибка при авторизации: {e}")
#
#
# # --- Основная функция ---
# def clear_table_safely():
#     total_deleted_count = 0
#     headers = login()
#
#     # --- НОВЫЙ БЛОК: Получение и выбор таблицы ---
#     print_header("Шаг 2: Получение списка доступных таблиц")
#     try:
#         get_types_url = f"{BASE_URL}/api/meta/entity-types"
#         types_response = requests.get(get_types_url, headers=headers)
#         types_response.raise_for_status()
#
#         available_tables = types_response.json()
#         if not available_tables:
#             print_status(False, "Для данного пользователя не найдено ни одной таблицы.")
#
#         print("Найдены следующие таблицы:")
#         for i, table in enumerate(available_tables):
#             print(f"  {i + 1}. {table['display_name']} (системное имя: {table['name']})")
#
#     except requests.exceptions.HTTPError as e:
#         print_status(False, f"Не удалось получить список таблиц: {e.response.status_code} - {e.response.text}")
#
#     # --- НОВЫЙ БЛОК: Выбор таблицы пользователем ---
#     chosen_table = None
#     while not chosen_table:
#         try:
#             choice = input(f"\nВведите номер таблицы для очистки (от 1 до {len(available_tables)}): ")
#             choice_index = int(choice) - 1
#             if 0 <= choice_index < len(available_tables):
#                 chosen_table = available_tables[choice_index]
#             else:
#                 print("Ошибка: номер вне диапазона. Попробуйте еще раз.")
#         except ValueError:
#             print("Ошибка: введите число.")
#
#     table_name = chosen_table['name']
#     print_status(True, f"Выбрана таблица: '{chosen_table['display_name']}'")
#
#     # --- Существующая логика удаления ---
#     print_header(f"Шаг 3: Начало процесса удаления из таблицы '{table_name}'")
#
#     while True:
#         try:
#             print(f"\nЗапрашиваем следующую порцию из {BATCH_SIZE} записей...")
#             get_url = f"{BASE_URL}/api/data/{table_name}?limit={BATCH_SIZE}"
#             get_response = requests.get(get_url, headers=headers)
#             get_response.raise_for_status()
#
#             json_data = get_response.json()
#             records = json_data.get('data', json_data) if isinstance(json_data, dict) else json_data
#
#             if not records:
#                 print_status(True, "В таблице больше не осталось записей.")
#                 break
#
#             entity_ids = [entity['id'] for entity in records]
#             print(f"Получено {len(entity_ids)} ID для удаления.")
#
#             for entity_id in tqdm(entity_ids, desc=f"Удаление порции (всего удалено {total_deleted_count})"):
#                 delete_url = f"{BASE_URL}/api/data/{table_name}/{entity_id}"
#                 requests.delete(delete_url, headers=headers)  # Ошибки удаления отдельных строк не прерывают процесс
#                 total_deleted_count += 1
#                 time.sleep(DELAY_BETWEEN_DELETES)
#
#         except requests.exceptions.HTTPError as e:
#             print_status(False,
#                          f"Критическая ошибка HTTP при получении данных: {e.response.status_code} - {e.response.text}")
#         except Exception as e:
#             print_status(False, f"Произошла непредвиденная ошибка: {e}")
#
#     print("\n" + "=" * 60)
#     print("🎉🎉🎉 ПРОЦЕСС ОЧИСТКИ УСПЕШНО ЗАВЕРШЕН! 🎉🎉🎉")
#     print(f"Всего удалено записей: {total_deleted_count}")
#
#
# if __name__ == "__main__":
#     clear_table_safely()


import requests
import time
from tqdm import tqdm
import sys

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"

# Размер порции, которую мы получаем и удаляем за один цикл.
# Теперь это и размер GET-запроса, и размер одного BULK-DELETE запроса.
BATCH_SIZE = 500
# Небольшая задержка между пакетными удалениями, чтобы дать серверу "передышку".
DELAY_BETWEEN_BATCHES = 0.5  # полсекунды


# ---------------------------------------------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [INFO] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        sys.exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login():
    """Аутентифицируется и возвращает заголовки для авторизации."""
    print_header("Шаг 1: Авторизация")
    try:
        auth_payload = {'username': EMAIL, 'password': PASSWORD}
        token_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_response.raise_for_status()
        token = token_response.json()['access_token']
        print_status(True, f"Успешная авторизация для пользователя {EMAIL}")
        return {'Authorization': f'Bearer {token}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}")


# --- Основная функция ---
def clear_table_by_batches():
    total_deleted_count = 0
    headers = login()

    # --- Получение и выбор таблицы (логика без изменений) ---
    print_header("Шаг 2: Получение списка доступных таблиц")
    try:
        get_types_url = f"{BASE_URL}/api/meta/entity-types"
        types_response = requests.get(get_types_url, headers=headers)
        types_response.raise_for_status()
        available_tables = types_response.json()
        if not available_tables:
            print_status(False, "Для данного пользователя не найдено ни одной таблицы.")

        print("Найдены следующие таблицы:")
        for i, table in enumerate(available_tables):
            print(f"  {i + 1}. {table['display_name']} (системное имя: {table['name']})")
    except requests.exceptions.HTTPError as e:
        print_status(False, f"Не удалось получить список таблиц: {e.response.status_code} - {e.response.text}")

    chosen_table = None
    while not chosen_table:
        try:
            choice = input(f"\nВведите номер таблицы для очистки (от 1 до {len(available_tables)}): ")
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(available_tables):
                chosen_table = available_tables[choice_index]
            else:
                print("Ошибка: номер вне диапазона. Попробуйте еще раз.")
        except ValueError:
            print("Ошибка: введите число.")

    table_name = chosen_table['name']
    print_status(True, f"Выбрана таблица: '{chosen_table['display_name']}'")

    # --- ИЗМЕНЕННАЯ ЛОГИКА УДАЛЕНИЯ ---
    print_header(f"Шаг 3: Начало процесса удаления из '{table_name}' пакетами по {BATCH_SIZE}")

    # Обернем цикл в tqdm для общего прогресс-бара
    with tqdm(total=None, desc="Всего удалено", unit=" записей") as pbar:
        while True:
            try:
                # 1. Получаем следующую порцию ID для удаления
                get_url = f"{BASE_URL}/api/data/{table_name}?limit={BATCH_SIZE}"
                get_response = requests.get(get_url, headers=headers)
                get_response.raise_for_status()

                json_data = get_response.json()
                records = json_data.get('data', json_data) if isinstance(json_data, dict) else json_data

                if not records:
                    print_status(True, "\nВ таблице больше не осталось записей.")
                    break

                entity_ids = [entity['id'] for entity in records]

                # --- 2. Удаляем всю порцию ОДНИМ запросом ---
                delete_url = f"{BASE_URL}/api/data/{table_name}/bulk-delete"
                delete_payload = {"ids": entity_ids}

                delete_resp = requests.post(delete_url, headers=headers, json=delete_payload)

                if delete_resp.status_code == 200:
                    deleted_count = delete_resp.json().get('deleted_count', len(entity_ids))
                    total_deleted_count += deleted_count
                    pbar.update(deleted_count)  # Обновляем прогресс-бар
                else:
                    print(
                        f"\n⚠️ Предупреждение: не удалось удалить пакет. Статус: {delete_resp.status_code}, Ответ: {delete_resp.text}")

                time.sleep(DELAY_BETWEEN_BATCHES)

            except requests.exceptions.HTTPError as e:
                print_status(False,
                             f"Критическая ошибка HTTP при получении данных: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print_status(False, f"Произошла непредвиденная ошибка: {e}")

    print("\n" + "=" * 60)
    print("🎉🎉🎉 ПРОЦЕСС ОЧИСТКИ УСПЕШНО ЗАВЕРШЕН! 🎉🎉🎉")
    print(f"Всего удалено записей: {total_deleted_count}")


if __name__ == "__main__":
    clear_table_by_batches()