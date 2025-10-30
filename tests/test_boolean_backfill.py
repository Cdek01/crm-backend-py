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
NEW_TABLE_NAME = f"test_bool_table_{int(time.time())}"
NEW_CHECKBOX_NAME = "is_completed"


# --- Вспомогательные функции ---

def print_status(ok: bool, message: str, data: Optional[Any] = None):
    """Выводит статус операции в консоль."""
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                # Пытаемся красиво напечатать JSON, если это возможно
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
    print_header("Тест создания колонки-чекбокса и заполнения по умолчанию")

    headers = login()
    if not headers:
        sys.exit(1)  # Выход, если авторизация не удалась

    table_id = None
    try:
        # --- ШАГ 1: Создание новой таблицы ---
        print_header("Шаг 1: Создание новой тестовой таблицы")
        url = f"{BASE_URL}/api/meta/entity-types"
        payload = {"name": NEW_TABLE_NAME, "display_name": f"Тест чекбоксов {int(time.time())}"}
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            table_data = response.json()
            table_id = table_data.get("id")
            print_status(True, f"Таблица '{NEW_TABLE_NAME}' (ID: {table_id}) успешно создана.")
        else:
            print_status(False, "Не удалось создать таблицу.", response.json())
            sys.exit(1)

        # --- ШАГ 2: Добавление 2 строк в таблицу ---
        print_header("Шаг 2: Добавление двух строк в таблицу (до создания чекбокса)")
        created_row_ids = []
        for i in range(1, 3):
            url = f"{BASE_URL}/api/data/{NEW_TABLE_NAME}"
            # Данные не важны, главное - создать строки. Они будут содержать только системные поля.
            response = requests.post(url, headers=headers, json={})
            if response.status_code == 201:
                # В ответе приходит весь список, берем первую (самую новую) запись
                new_row_id = response.json()["data"][0]["id"]
                created_row_ids.append(new_row_id)
                print_status(True, f"Создана строка #{i} с ID: {new_row_id}")
            else:
                print_status(False, f"Не удалось создать строку #{i}", response.json())
                # Продолжаем, даже если одна строка не создалась

        if not created_row_ids:
            print_status(False, "Не удалось создать ни одной строки для теста.")
            sys.exit(1)

        # --- ШАГ 3: Создание колонки-чекбокса ---
        print_header(f"Шаг 3: Создание колонки '{NEW_CHECKBOX_NAME}' (тип boolean)")
        url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
        payload = {
            "name": NEW_CHECKBOX_NAME,
            "display_name": "Выполнено?",
            "value_type": "boolean"
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print_status(True, "Колонка-чекбокс успешно создана.")
        else:
            print_status(False, "Не удалось создать колонку-чекбокс.", response.json())
            sys.exit(1)

        # Даем бэкенду немного времени на обработку, на всякий случай
        print("Ожидание 1 секунда для гарантии обработки на бэкенде...")
        time.sleep(1)

        # --- ШАГ 4: Проверка значений по умолчанию ---
        print_header("Шаг 4: Проверка, что у старых строк появилось значение False")
        url = f"{BASE_URL}/api/data/{NEW_TABLE_NAME}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print_status(False, "Не удалось получить данные из таблицы для проверки.", response.json())
            sys.exit(1)

        all_rows = response.json().get("data", [])
        rows_to_check = {row['id']: row for row in all_rows if row['id'] in created_row_ids}

        verification_passed = True
        for row_id in created_row_ids:
            if row_id not in rows_to_check:
                print_status(False, f"Строка с ID {row_id} не найдена в итоговых данных.")
                verification_passed = False
                continue

            row = rows_to_check[row_id]
            if NEW_CHECKBOX_NAME not in row:
                print_status(False, f"У строки ID {row_id} отсутствует поле '{NEW_CHECKBOX_NAME}'.")
                verification_passed = False
            elif row[NEW_CHECKBOX_NAME] is not False:
                print_status(False,
                             f"У строки ID {row_id} значение '{row[NEW_CHECKBOX_NAME]}' вместо ожидаемого False.")
                verification_passed = False
            else:
                print_status(True, f"У строки ID {row_id} значение корректно ({NEW_CHECKBOX_NAME} = False).")

        if not verification_passed:
            # Если проверка провалилась, выводим все данные для анализа
            print("\n--- Полные данные из таблицы для отладки ---")
            print(json.dumps(all_rows, indent=2, ensure_ascii=False))
            print("------------------------------------------\n")

    except Exception as e:
        print_status(False, f"Во время теста произошла непредвиденная ошибка: {e}")

    finally:
        # --- ШАГ 5: Очистка ---
        if table_id:
            print_header("Шаг 5: Очистка (удаление тестовой таблицы)")
            url = f"{BASE_URL}/api/meta/entity-types/{table_id}"
            response = requests.delete(url, headers=headers)
            if response.status_code == 204:
                print_status(True, f"Тестовая таблица (ID: {table_id}) успешно удалена.")
            else:
                print_status(False, "Не удалось удалить тестовую таблицу.", response.text)

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