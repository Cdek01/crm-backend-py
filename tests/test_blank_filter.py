import requests
import sys
import json
import time
from typing import Dict, Any, Optional

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"  # Укажите правильный URL вашего сервера
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Глобальные переменные ---
test_failed = False
UNIQUE_TABLE_NAME = f"blank_filter_test_{int(time.time())}"
test_table_info = {}


# --- Вспомогательные функции ---
def print_status(ok: bool, message: str, data: Optional[Any] = None):
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        test_failed = True
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                print(f"  └─ Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except (TypeError, json.JSONDecodeError):
                print(f"  └─ Ответ сервера: {data}")
        print("")


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def login() -> Optional[Dict[str, str]]:
    print_header("Этап 0: Авторизация")
    try:
        url = f"{BASE_URL}/api/auth/token"
        r = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})
        r.raise_for_status()
        token = r.json()["access_token"]
        print_status(True, "Успешно получен токен доступа.")
        return {'Authorization': f'Bearer {token}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}", getattr(e, 'response', 'N/A'))
        return None


# --- Функции для подготовки и очистки ---
def create_test_table(headers: Dict[str, str]) -> Optional[str]:
    global test_table_info
    print_header(f"Этап 1: Создание тестовой таблицы '{UNIQUE_TABLE_NAME}'")
    try:
        url = f"{BASE_URL}/api/meta/entity-types"
        payload = {"name": UNIQUE_TABLE_NAME, "display_name": f"Тест blank фильтра {time.time()}"}
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        table_id = r.json()["id"]
        test_table_info = {"id": table_id, "name": UNIQUE_TABLE_NAME}
        print_status(True, f"Таблица создана, ID: {table_id}")

        columns = [{"name": "description", "display_name": "Описание", "value_type": "string"}]
        for col in columns:
            url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
            r = requests.post(url, headers=headers, json=col)
            r.raise_for_status()
            print_status(True, f"Колонка '{col['display_name']}' добавлена.")
        return UNIQUE_TABLE_NAME
    except Exception as e:
        print_status(False, "Не удалось создать тестовую таблицу", getattr(e, 'response', 'N/A').text)
        return None


def populate_test_data(headers: Dict[str, str], table_name: str):
    print_header(f"Этап 2: Наполнение таблицы '{table_name}' данными для теста")
    try:
        # Сценарий 1: Запись с НЕПУСТЫМ значением
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                      json={"description": "Есть значение"}).raise_for_status()
        print_status(True, "Добавлена запись 1: с непустым значением.")

        # Сценарий 2: Запись с ПУСТОЙ СТРОКОЙ
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={"description": ""}).raise_for_status()
        print_status(True, "Добавлена запись 2: со значением пустой строки ''.")

        # Сценарий 3: Запись, где поле НЕ УКАЗАНО (значение физически отсутствует в БД)
        # Для этого создаем запись, не передавая поле 'description'
        r = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={})
        r.raise_for_status()
        created_id = r.json()['data'][0]['id']
        print_status(True, f"Добавлена запись 3 (ID: {created_id}): поле 'description' не передавалось.")

        # Сценарий 4: Запись, где значение было, а потом его стерли (стало пустой строкой)
        r = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                          json={"description": "Временное значение"})
        r.raise_for_status()
        id_to_update = r.json()['data'][0]['id']
        requests.put(f"{BASE_URL}/api/data/{table_name}/{id_to_update}", headers=headers,
                     json={"description": ""}).raise_for_status()
        print_status(True, f"Добавлена запись 4 (ID: {id_to_update}): значение было, но его очистили до ''.")

        return True
    except Exception as e:
        print_status(False, "Не удалось наполнить таблицу данными", getattr(e, 'response', 'N/A').text)
        return False


def delete_test_table(headers: Dict[str, str]):
    if not test_table_info: return
    print_header(f"Этап 4: Очистка (удаление таблицы '{test_table_info['name']}')")
    try:
        url = f"{BASE_URL}/api/meta/entity-types/{test_table_info['id']}"
        r = requests.delete(url, headers=headers)
        if r.status_code == 204:
            print_status(True, f"Тестовая таблица ID {test_table_info['id']} успешно удалена.")
        else:
            print_status(False, f"Не удалось удалить тестовую таблицу. Статус: {r.status_code}", r.text)
    except Exception as e:
        print_status(False, "Произошла ошибка при удалении тестовой таблицы", getattr(e, 'response', 'N/A'))


# --- Тестовая функция ---
def run_tests(headers: Dict[str, str], table_name: str):
    print_header("Этап 3: Тестирование фильтров")

    # --- Тест 1: Проверка фильтра "blank" (пусто) ---
    print("\n--- Тест 1: Проверка фильтра 'blank' ---")
    try:
        filters = [{"field": "description", "op": "blank"}]
        params = {"filters": json.dumps(filters), "limit": 100}

        r = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)
        r.raise_for_status()

        result = r.json()
        count = result.get("total", 0)

        if count == 3:
            print_status(True, f"Фильтр 'blank' работает корректно. Найдено {count} записи (ожидалось 3).")
        else:
            print_status(False, f"Фильтр 'blank' работает НЕКОРРЕКТНО. Найдено {count} записей, но ожидалось 3.",
                         result.get('data'))

    except Exception as e:
        print_status(False, f"Произошла ошибка при тесте фильтра 'blank'", getattr(e, 'response', 'N/A'))

    # --- Тест 2: Проверка фильтра "not_blank" (не пусто) ---
    print("\n--- Тест 2: Проверка фильтра 'not_blank' ---")
    try:
        filters = [{"field": "description", "op": "not_blank"}]
        params = {"filters": json.dumps(filters), "limit": 100}

        r = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)
        r.raise_for_status()

        result = r.json()
        count = result.get("total", 0)
        data = result.get('data', [])

        if count == 1 and data[0]['description'] == "Есть значение":
            print_status(True, f"Фильтр 'not_blank' работает корректно. Найдена {count} запись (ожидалась 1).")
        else:
            print_status(False, f"Фильтр 'not_blank' работает НЕКОРРЕКТНО. Найдено {count} записей, но ожидалась 1.",
                         data)

    except Exception as e:
        print_status(False, f"Произошла ошибка при тесте фильтра 'not_blank'", getattr(e, 'response', 'N/A'))


# --- Главная функция ---
def main():
    auth_headers = login()
    if not auth_headers: sys.exit(1)

    try:
        table_name = create_test_table(auth_headers)
        if not table_name: sys.exit(1)

        if not populate_test_data(auth_headers, table_name):
            sys.exit(1)

        run_tests(auth_headers, table_name)

    finally:
        # Пауза, чтобы убедиться, что все операции завершены, перед удалением
        time.sleep(1)
        delete_test_table(auth_headers)

    print_header("Итоги тестирования")
    if not test_failed:
        print("🎉 ✅ Все тесты фильтров 'blank' / 'not_blank' успешно пройдены!")
    else:
        print("🚨 ❌ Во время тестирования были обнаружены ошибки.")
        sys.exit(1)


if __name__ == "__main__":
    main()