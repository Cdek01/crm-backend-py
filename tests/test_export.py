import requests
import sys
import json
import time
import pandas as pd
import io
from typing import Dict, Any, Optional
from urllib.parse import quote_plus

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"

# --- ПАРАМЕТРЫ ТЕСТА (ВАЖНО НАСТРОИТЬ!) ---
# Системное имя таблицы, которую будем экспортировать (например, "leads" или "my_custom_table")
TARGET_TABLE_NAME = "deals_ai_test_1730449557"  # <-- ЗАМЕНИТЕ НА ИМЯ ВАШЕЙ ТАБЛИЦЫ
# ID одной из существующих записей в этой таблице для теста фильтрации
KNOWN_ID_IN_TABLE = 1  # <-- ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ID

# -----------------

# --- Глобальные переменные ---
test_failed = False


# --- Вспомогательные функции (без изменений) ---
def print_status(ok: bool, message: str, data: Optional[Any] = None):
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        test_failed = True
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                # Попытка красиво напечатать JSON, если это возможно
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
        print_status(True, f"Успешно получен токен доступа.")
        return {'Authorization': f'Bearer {token}'}
    except Exception as e:
        response_text = getattr(e, 'response', 'N/A')
        if hasattr(response_text, 'text'):
            response_text = response_text.text
        print_status(False, f"Критическая ошибка при авторизации: {e}", response_text)
        return None


# --- Тестовые функции ---

def test_export(headers: Dict[str, str], table_name: str, format: str):
    """
    Универсальная функция для тестирования экспорта.
    """
    print_header(f"Тест: Экспорт таблицы '{table_name}' в формат {format.upper()}")
    try:
        # 1. Выполняем запрос
        url = f"{BASE_URL}/api/data/{table_name}/export?format={format}"
        print(f"-> Запрос на URL: {url}")
        r = requests.get(url, headers=headers)

        # 2. Проверяем статус-код
        if r.status_code != 200:
            print_status(False, f"Ожидался статус-код 200, получен {r.status_code}", r.json())
            return
        print_status(True, f"Сервер вернул статус-код 200 OK.")

        # 3. Проверяем Content-Type
        content_type = r.headers.get("Content-Type", "")
        expected_type = "text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if expected_type not in content_type:
            print_status(False, f"Неверный Content-Type. Ожидался '{expected_type}', получен '{content_type}'")
        else:
            print_status(True, f"Content-Type корректный: '{content_type}'")

        # 4. Проверяем, что файл можно прочитать
        file_content = r.content
        if not file_content:
            print_status(False, "Тело ответа пустое, файл не получен.")
            return

        stream = io.BytesIO(file_content)
        if format == "csv":
            df = pd.read_csv(stream)
        else:  # xlsx
            df = pd.read_excel(stream, engine='openpyxl')

        print_status(True,
                     f"Файл успешно прочитан с помощью pandas. Количество строк: {len(df)}, колонок: {len(df.columns)}.")
        print("-> Превью данных:")
        print(df.head())

    except Exception as e:
        print_status(False, f"Во время теста произошла ошибка: {e}")


def test_export_with_filter(headers: Dict[str, str], table_name: str, known_id: int):
    """
    Тестирует экспорт с применением фильтра.
    """
    print_header(f"Тест: Экспорт с фильтром (ID = {known_id})")
    try:
        # Создаем и кодируем фильтр для URL
        filters_obj = [{"field": "id", "op": "eq", "value": known_id}]
        filters_str = quote_plus(json.dumps(filters_obj))

        url = f"{BASE_URL}/api/data/{table_name}/export?format=csv&filters={filters_str}"
        print(f"-> Запрос на URL: {url}")
        r = requests.get(url, headers=headers)
        r.raise_for_status()

        # Проверяем, что в полученном файле ровно одна строка данных
        df = pd.read_csv(io.BytesIO(r.content))
        if len(df) == 1:
            print_status(True, f"Фильтр сработал корректно. В файле найдена 1 запись с ID={df.iloc[0]['ID']}.")
        else:
            print_status(False, f"Фильтр сработал некорректно. Ожидалась 1 запись, получено {len(df)}.", df.to_dict())

    except Exception as e:
        print_status(False, f"Во время теста с фильтром произошла ошибка: {e}", getattr(e, 'response', 'N/A'))


def test_error_scenarios(headers: Dict[str, str], table_name: str):
    """
    Тестирует сценарии, которые должны возвращать ошибки.
    """
    print_header("Тест: Сценарии с ошибками")

    # Сценарий 1: Несуществующая таблица
    try:
        bad_table = "nonexistent_table_12345"
        url = f"{BASE_URL}/api/data/{bad_table}/export?format=csv"
        r = requests.get(url, headers=headers)
        if r.status_code == 404:
            print_status(True, f"Сервер корректно вернул 404 Not Found для несуществующей таблицы.")
        else:
            print_status(False, f"Ожидался статус 404, но получен {r.status_code}", r.text)
    except Exception as e:
        print_status(False, f"Ошибка при тесте несуществующей таблицы: {e}")

    # Сценарий 2: Неверный формат
    try:
        url = f"{BASE_URL}/api/data/{table_name}/export?format=pdf"
        r = requests.get(url, headers=headers)
        if r.status_code == 422:
            print_status(True, f"Сервер корректно вернул 422 Unprocessable Entity для неверного формата.")
        else:
            print_status(False, f"Ожидался статус 422, но получен {r.status_code}", r.text)
    except Exception as e:
        print_status(False, f"Ошибка при тесте неверного формата: {e}")


def main():
    """Главная функция для запуска всех тестов."""
    auth_headers = login()
    if not auth_headers:
        sys.exit(1)

    # Запуск тестов
    test_export(auth_headers, TARGET_TABLE_NAME, "csv")
    test_export(auth_headers, TARGET_TABLE_NAME, "xlsx")
    test_export_with_filter(auth_headers, TARGET_TABLE_NAME, KNOWN_ID_IN_TABLE)
    test_error_scenarios(auth_headers, TARGET_TABLE_NAME)

    # Итоговый результат
    print_header("Итоги тестирования")
    if not test_failed:
        print("🎉 ✅ Все тесты функции экспорта успешно пройдены!")
    else:
        print("🚨 ❌ Во время тестирования были обнаружены ошибки.")
        sys.exit(1)


if __name__ == "__main__":
    main()