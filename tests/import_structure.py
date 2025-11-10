import requests
import json
import sys
import time
import os
import pandas as pd
import io
from typing import Optional

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
FILE_PATH = r"Структура БД.xlsx"
SHEET_NAME = "Дорожная карта"

NEW_TABLE_NAME = f"roadmap_{int(time.time())}"


# ... (вспомогательные функции print_header, get_auth_token) ...
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


def import_roadmap_sheet(token: str):
    headers = {"Authorization": f"Bearer {token}"}

    print_header(f"Этап 1: Чтение и очистка листа '{SHEET_NAME}'")

    if not os.path.exists(FILE_PATH):
        print(f"❌ ОШИБКА: Файл не найден по пути: {FILE_PATH}")
        return

    try:
        df_raw = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=None)

        first_valid_index = df_raw.dropna(how='all').index.min()
        headers_series = df_raw.iloc[first_valid_index]

        df_data = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=first_valid_index + 1)

        df_data.dropna(axis=1, how='all', inplace=True)
        df_data.dropna(axis=0, how='all', inplace=True)

        valid_headers = {i: h for i, h in headers_series.dropna().items()}
        df_data = df_data.iloc[:, list(valid_headers.keys())]
        df_data.columns = list(valid_headers.values())

        # --- ГЛАВНОЕ ИЗМЕНЕНИЕ: Заменяем все NaN на строку 'NaN' ---
        df_data.fillna('NaN', inplace=True)
        # -----------------------------------------------------------

        print(f"✅ Лист '{SHEET_NAME}' успешно прочитан и очищен.")
        print(f"   - Найдено строк для импорта: {len(df_data)}")
        print(f"   - Распознаны и назначены колонки: {list(df_data.columns)}")

        if df_data.empty:
            print("\n❌ ОШИБКА: DataFrame пустой. Импорт остановлен.")
            return

        print("\n-> Превью очищенных данных (первые 3 строки):")
        print(df_data.head(3).to_string())

        print("\n-> Создание временного Excel файла в памяти...")
        output_stream = io.BytesIO()
        # Сохраняем уже обработанный DataFrame
        df_data.to_excel(output_stream, index=False, engine='openpyxl')
        output_stream.seek(0)

    except Exception as e:
        print(f"❌ Ошибка при чтении Excel файла: {e}")
        return

    # ... (Этапы 2 и 3 остаются без изменений) ...
    print_header("Этап 2: Загрузка и анализ подготовленного файла на сервере")
    try:
        upload_url = f"{BASE_URL}/api/imports/upload"
        files = {'file': (f"{NEW_TABLE_NAME}.xlsx", output_stream,
                          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response_upload = requests.post(upload_url, headers=headers, files=files)
        response_upload.raise_for_status()
        upload_data = response_upload.json()
        file_id = upload_data.get("file_id")
        headers_from_server = upload_data.get("headers", [])
        if not file_id or not headers_from_server:
            print("❌ Ошибка: Сервер не вернул file_id или информацию о колонках.")
            return
        print(f"✅ Файл успешно проанализирован. Получен file_id: {file_id}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка на этапе загрузки файла: {e}")
        if e.response is not None: print(f"   └─ Ответ сервера: {e.response.text}")
        return

    try:
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Мы больше не доверяем "suggested_type".
        # Мы принудительно говорим серверу, что ВСЕ колонки - это строки.
        column_mappings = []
        for h in headers_from_server:
            column_mappings.append({
                "original_header": h["original_header"],
                "display_name": h["original_header"],
                "value_type": "string",  # <--- ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ ТИП "СТРОКА"
                "do_import": True
            })

        config_payload = {
            "new_table_name": NEW_TABLE_NAME,
            "new_table_display_name": f"Дорожная карта (импорт от {time.strftime('%Y-%m-%d')})",
            "columns": column_mappings
        }

        process_url = f"{BASE_URL}/api/imports/process/{file_id}"
        response_process = requests.post(process_url, headers=headers, json=config_payload)
        response_process.raise_for_status()
        task_id = response_process.json().get("task_id")

        print("\n🎉 ✅ УСПЕХ! Фоновая задача по импорту успешно запущена.")
        print(f"   ├─ ID задачи: {task_id}")
        print(f"   └─ Новая таблица появится в CRM с системным именем: '{NEW_TABLE_NAME}'")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка на этапе запуска импорта: {e}")
        if e.response is not None: print(f"   └─ Ответ сервера: {e.response.text}")


def main():
    auth_token = get_auth_token()
    if not auth_token:
        sys.exit(1)
    import_roadmap_sheet(auth_token)
    print_header("Завершение")
    print("Процесс запущен на сервере. Через несколько минут проверьте интерфейс вашей CRM.")


if __name__ == "__main__":
    main()