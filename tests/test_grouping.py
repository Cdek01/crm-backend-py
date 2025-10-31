import requests
import time
import sys
import json
from typing import Dict, Any, Optional

# --- НАСТРОЙКИ ---
# Укажите URL вашего API
BASE_URL = "http://89.111.169.47:8005"
# Укажите данные пользователя для входа
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Глобальные переменные для теста ---
test_failed = False
# Генерируем уникальное имя для таблицы, чтобы тесты не мешали друг другу
NEW_TABLE_NAME = f"test_grouping_table_{int(time.time())}"
GROUP_BY_COLUMN_NAME = "status"

# --- РАСШИРЕННЫЙ НАБОР ТЕСТОВЫХ ДАННЫХ ---
# Ключ - значение в колонке, значение - сколько раз его нужно создать.
# None (в Python) соответствует NULL в базе данных.
EXPECTED_DATA = {
    "Новый": 5,
    "В работе": 3,
    "Завершен": 2,
    "archived": 1,  # Проверка на регистр
    "Этап 1": 2,  # Проверка на буквенно-цифровые значения
    "": 1,  # Проверка на пустую строку
    None: 4  # Проверка на NULL значения (записи без статуса)
}


# --- Вспомогательные функции (без изменений) ---

def print_status(ok: bool, message: str, data: Optional[Any] = None):
    """Выводит статус операции в консоль."""
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                print(f"  └─ Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except (TypeError, json.JSONDecodeError):
                print(f"  └─ Ответ сервера: {data}")
        print("")
        test_failed = True


def print_header(title: str):
    """Выводит красивый заголовок для каждого этапа теста."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def login() -> Optional[Dict[str, str]]:
    """Авторизуется и возвращает заголовок для последующих запросов."""
    try:
        url = f"{BASE_URL}/api/auth/token"
        response = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})
        response.raise_for_status()
        print_status(True, "Авторизация прошла успешно")
        return {'Authorization': f'Bearer {response.json()["access_token"]}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}", getattr(e, 'response', 'N/A'))
        return None


def main():
    """Основная функция, запускающая тест."""
    print_header("Расширенный тест группировки данных")

    headers = login()
    if not headers:
        sys.exit(1)

    table_id = None
    try:
        # --- ШАГ 1: Создание инфраструктуры ---
        print_header(f"Шаг 1: Создание таблицы '{NEW_TABLE_NAME}' и колонки '{GROUP_BY_COLUMN_NAME}'")
        # (Код создания таблицы и колонки без изменений)
        url_table = f"{BASE_URL}/api/meta/entity-types"
        payload_table = {"name": NEW_TABLE_NAME, "display_name": f"Тест группировки {int(time.time())}"}
        response_table = requests.post(url_table, headers=headers, json=payload_table)
        if response_table.status_code != 201:
            print_status(False, "Не удалось создать таблицу.", response_table.json());
            sys.exit(1)
        table_id = response_table.json().get("id")
        print_status(True, f"Таблица '{NEW_TABLE_NAME}' (ID: {table_id}) создана.")

        url_attr = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
        payload_attr = {"name": GROUP_BY_COLUMN_NAME, "display_name": "Статус", "value_type": "string"}
        response_attr = requests.post(url_attr, headers=headers, json=payload_attr)
        if response_attr.status_code != 201:
            print_status(False, "Не удалось создать колонку.", response_attr.json());
            sys.exit(1)
        print_status(True, f"Колонка '{GROUP_BY_COLUMN_NAME}' создана.")

        # --- ШАГ 2: Наполнение таблицы разнообразными данными ---
        print_header("Шаг 2: Наполнение таблицы тестовыми данными")
        url_data = f"{BASE_URL}/api/data/{NEW_TABLE_NAME}"
        total_rows_to_create = sum(EXPECTED_DATA.values())
        created_count = 0

        for status_key, count in EXPECTED_DATA.items():
            payload = {}
            # Специальная обработка для NULL-значений
            if status_key is not None:
                payload = {GROUP_BY_COLUMN_NAME: status_key}

            print(f"  -> Создание {count} строк со статусом: '{status_key}'")
            for _ in range(count):
                # Мы не проверяем каждую строку, чтобы не засорять вывод. Проверим общее количество.
                requests.post(url_data, headers=headers, json=payload)
                created_count += 1

        print_status(created_count == total_rows_to_create,
                     f"Создание записей завершено. Ожидалось: {total_rows_to_create}, Создано: {created_count}")
        if created_count != total_rows_to_create: sys.exit(1)

        # --- ШАГ 3: Запрос данных с группировкой ---
        print_header(f"Шаг 3: Выполнение запроса на группировку по колонке '{GROUP_BY_COLUMN_NAME}'")
        url_group = f"{BASE_URL}/api/data/{NEW_TABLE_NAME}/group-by/{GROUP_BY_COLUMN_NAME}"
        response_group = requests.get(url_group, headers=headers)
        if response_group.status_code != 200:
            print_status(False, "Запрос на группировку завершился с ошибкой.", response_group.json());
            sys.exit(1)
        print_status(True, "Запрос на группировку успешно выполнен (код 200).")

        # --- ШАГ 4: Детальная проверка результата ---
        print_header("Шаг 4: Сравнение полученного результата с ожидаемым")
        actual_data_list = response_group.json()
        actual_data_map = {item.get('group_key'): item.get('count') for item in actual_data_list}

        print(f"\n--- Ожидаемый результат ---")
        print(json.dumps(EXPECTED_DATA, indent=2, ensure_ascii=False))
        print(f"\n--- Фактический результат от API ---")
        print(json.dumps(actual_data_map, indent=2, ensure_ascii=False))
        print("\n--- Построчная проверка ---")

        # Проверка 1: все ожидаемые группы есть, и их количество совпадает
        for expected_key, expected_count in EXPECTED_DATA.items():
            if expected_key not in actual_data_map:
                print_status(False, f"ОШИБКА: Ожидаемая группа '{expected_key}' отсутствует в ответе API.")
            elif actual_data_map[expected_key] != expected_count:
                print_status(False,
                             f"РАСХОЖДЕНИЕ: Для группы '{expected_key}' ожидалось {expected_count} записей, а получено {actual_data_map[expected_key]}.")
            else:
                print_status(True, f"Группа '{expected_key}': количество {expected_count} совпадает.")

        # Проверка 2: в ответе нет неожиданных групп
        for actual_key, actual_count in actual_data_map.items():
            if actual_key not in EXPECTED_DATA:
                print_status(False,
                             f"ОШИБКА: В ответе API найдена неожиданная группа '{actual_key}' с количеством {actual_count}.")

    except Exception as e:
        print_status(False, f"Во время теста произошла непредвиденная ошибка: {e}")

    # finally:
    #     # --- ШАГ 5: Очистка (без изменений) ---
    #     if table_id:
    #         print_header("Шаг 5: Очистка (удаление тестовой таблицы)")
    #         url_delete = f"{BASE_URL}/api/meta/entity-types/{table_id}"
    #         requests.delete(url_delete, headers=headers)
    #         # Мы не будем проверять статус удаления, чтобы не завалить тест, если он уже провалился
    #         print(f"Запрос на удаление тестовой таблицы (ID: {table_id}) отправлен.")

    # --- Итог ---
    print_header("Результаты теста")
    if test_failed:
        print("❌ Тест НЕ ПРОЙДЕН. Найдены ошибки.")
        sys.exit(1)
    else:
        print("✅ Тест УСПЕШНО ПРОЙДЕН. Все проверки выполнены.")
        sys.exit(0)


if __name__ == "__main__":
    main()