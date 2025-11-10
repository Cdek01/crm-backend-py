import requests
import json
import sys
import time
import os
import pandas as pd
import io
import numpy as np
from typing import Optional

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
CSV_FILE_PATH = r"Структура БД - Дорожная карта.csv"
NEW_TABLE_NAME = f"roadmap_{int(time.time())}"


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def get_auth_token() -> Optional[str]:
    print_header("Этап 0: Авторизация")
    try:
        url = f"{BASE_URL}/api/auth/token"
        response = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})
        response.raise_for_status()
        token = response.json().get("access_token")
        print("✅ Успешно получен токен доступа.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"❌ Критическая ошибка при авторизации: {e}")
        if e.response is not None: print(f"   └─ Ответ сервера: {e.response.text}")
        return None


def test_simple_import(token: str):
    """Тестовый импорт с минимальными данными"""
    headers = {"Authorization": f"Bearer {token}"}

    print_header("ТЕСТ: Создание простой таблицы")

    # Создаем простой DataFrame с 3 строками
    test_data = {
        'Название': ['Тест 1', 'Тест 2', 'Тест 3'],
        'Описание': ['Описание 1', 'Описание 2', 'Описание 3'],
        'Статус': [1, 2, 3]
    }
    df_test = pd.DataFrame(test_data)

    print("📊 Тестовые данные:")
    print(df_test)

    try:
        # Создаем Excel файл
        output_stream = io.BytesIO()
        df_test.to_excel(output_stream, index=False, engine='openpyxl')
        output_stream.seek(0)

        # Загружаем на сервер
        upload_url = f"{BASE_URL}/api/imports/upload"
        files = {
            'file': ('test_simple.xlsx', output_stream,
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }

        print("📤 Загрузка тестового файла...")
        response_upload = requests.post(upload_url, headers=headers, files=files, timeout=60)
        response_upload.raise_for_status()

        upload_data = response_upload.json()
        file_id = upload_data.get("file_id")
        headers_from_server = upload_data.get("headers", [])

        print(f"✅ Файл загружен. file_id: {file_id}")

        # Запускаем импорт
        column_mappings = []
        for h in headers_from_server:
            column_mappings.append({
                "original_header": h["original_header"],
                "display_name": h["original_header"],
                "value_type": h["suggested_type"],
                "do_import": True
            })

        test_table_name = f"test_simple_{int(time.time())}"
        config_payload = {
            "new_table_name": test_table_name,
            "new_table_display_name": f"Тестовая таблица",
            "columns": column_mappings,
            "import_all_rows": True
        }

        process_url = f"{BASE_URL}/api/imports/process/{file_id}"
        print("🚀 Запуск тестового импорта...")

        response_process = requests.post(process_url, headers=headers, json=config_payload, timeout=60)
        response_process.raise_for_status()

        process_response = response_process.json()
        task_id = process_response.get("task_id")

        print(f"✅ Тестовый импорт запущен!")
        print(f"   ID задачи: {task_id}")
        print(f"   Таблица: {test_table_name}")

        return True

    except Exception as e:
        print(f"❌ Тестовый импорт не удался: {e}")
        return False


def debug_csv_data():
    """Диагностика CSV данных"""
    print_header("ДИАГНОСТИКА CSV ДАННЫХ")

    try:
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8')
        print(f"📊 Исходные данные: {len(df)} строк, {len(df.columns)} колонок")

        # Анализ колонок
        print("\n🔍 Анализ колонок:")
        for i, col in enumerate(df.columns):
            non_empty = df[col].notna().sum()
            dtype = df[col].dtype
            sample = df[col].iloc[0] if not df[col].empty else "EMPTY"
            print(f"   {i:2d}. '{col}' - {dtype}, непустых: {non_empty}/{len(df)}, пример: {str(sample)[:30]}...")

        # Покажем первые 3 строки
        print("\n📄 Первые 3 строки данных:")
        print(df.head(3).to_string())

        # Проверим проблемные символы
        print("\n🔍 Поиск проблемных символов:")
        for col in df.columns:
            if df[col].dtype == object:
                for i, val in enumerate(df[col].head(5)):
                    if pd.notna(val):
                        try:
                            str(val).encode('utf-8')
                        except UnicodeEncodeError as e:
                            print(f"   ❌ Проблема в колонке '{col}', строка {i}: {e}")

        return df

    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
        return None


def create_minimal_roadmap(token: str, df: pd.DataFrame):
    """Создание минимальной версии дорожной карты"""
    headers = {"Authorization": f"Bearer {token}"}

    print_header("Создание минимальной таблицы")

    try:
        # Берем только основные колонки и первые 10 строк
        essential_cols = []
        for col in df.columns:
            if not col.startswith('Unnamed') and df[col].notna().sum() > 0:
                essential_cols.append(col)
            if len(essential_cols) >= 5:  # Ограничимся 5 колонками
                break

        df_minimal = df[essential_cols].head(10).copy()

        # Очищаем данные
        for col in df_minimal.columns:
            if df_minimal[col].dtype == object:
                df_minimal[col] = df_minimal[col].fillna('').astype(str)
            else:
                df_minimal[col] = df_minimal[col].fillna(0)

        print(f"📊 Минимальные данные: {len(df_minimal)} строк, {len(df_minimal.columns)} колонок")
        print(f"   Колонки: {list(df_minimal.columns)}")
        print("\nПервые 3 строки:")
        print(df_minimal.head(3).to_string())

        # Создаем Excel файл
        output_stream = io.BytesIO()
        df_minimal.to_excel(output_stream, index=False, engine='openpyxl')
        output_stream.seek(0)

        # Загружаем на сервер
        upload_url = f"{BASE_URL}/api/imports/upload"
        files = {
            'file': ('minimal_roadmap.xlsx', output_stream,
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }

        print("📤 Загрузка минимального файла...")
        response_upload = requests.post(upload_url, headers=headers, files=files, timeout=60)
        response_upload.raise_for_status()

        upload_data = response_upload.json()
        file_id = upload_data.get("file_id")
        headers_from_server = upload_data.get("headers", [])

        print(f"✅ Файл загружен. file_id: {file_id}")

        # Запускаем импорт
        column_mappings = []
        for h in headers_from_server:
            column_mappings.append({
                "original_header": h["original_header"],
                "display_name": h["original_header"],
                "value_type": h["suggested_type"],
                "do_import": True
            })

        minimal_table_name = f"minimal_roadmap_{int(time.time())}"
        config_payload = {
            "new_table_name": minimal_table_name,
            "new_table_display_name": f"Минимальная дорожная карта",
            "columns": column_mappings,
            "import_all_rows": True
        }

        process_url = f"{BASE_URL}/api/imports/process/{file_id}"
        print("🚀 Запуск импорта минимальной таблицы...")

        response_process = requests.post(process_url, headers=headers, json=config_payload, timeout=60)
        response_process.raise_for_status()

        process_response = response_process.json()
        task_id = process_response.get("task_id")

        print(f"✅ Импорт запущен!")
        print(f"   ID задачи: {task_id}")
        print(f"   Таблица: {minimal_table_name}")

        # Ждем
        print("⏳ Ожидание 20 секунд...")
        time.sleep(20)

        print("✅ Минимальная таблица должна быть создана")
        return True

    except Exception as e:
        print(f"❌ Ошибка создания минимальной таблицы: {e}")
        import traceback
        print(f"Детали: {traceback.format_exc()}")
        return False


def main():
    auth_token = get_auth_token()
    if not auth_token:
        sys.exit(1)

    # 1. Сначала диагностируем данные
    df = debug_csv_data()
    if df is None:
        print("❌ Не удалось прочитать CSV файл")
        return

    # 2. Пробуем тестовый импорт с простыми данными
    test_success = test_simple_import(auth_token)
    if not test_success:
        print("❌ Тестовый импорт не удался - проблема с сервером")
        return

    print("⏳ Ожидание 10 секунд перед следующим шагом...")
    time.sleep(10)

    # 3. Пробуем создать минимальную версию дорожной карты
    create_minimal_roadmap(auth_token, df)

    print_header("ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("Проверьте в интерфейсе CRM:")
    print("1. Создалась ли тестовая таблица (test_simple_...)")
    print("2. Создалась ли минимальная дорожная карта (minimal_roadmap_...)")
    print("3. Если нет - проблема на стороне сервера")


if __name__ == "__main__":
    main()