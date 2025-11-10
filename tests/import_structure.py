import requests
import json
import sys
import time
import os
import io
from typing import Optional

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
FILE_PATH = r"Структура БД.xlsx"
SHEET_NAME = "Дорожная карта"

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


def import_roadmap_sheet(token: str):
    headers = {"Authorization": f"Bearer {token}"}

    print_header(f"Этап 1: Подготовка и отправка файла")

    if not os.path.exists(FILE_PATH):
        print(f"❌ ОШИБКА: Файл не найден по пути: {FILE_PATH}")
        return

    try:
        # Отправляем оригинальный файл как есть
        with open(FILE_PATH, 'rb') as f:
            files = {'file': (os.path.basename(FILE_PATH), f)}
            print(f"-> Отправка файла '{os.path.basename(FILE_PATH)}' на анализ...")

            upload_url = f"{BASE_URL}/api/imports/upload"
            response_upload = requests.post(upload_url, headers=headers, files=files)
            response_upload.raise_for_status()

            upload_data = response_upload.json()
            file_id = upload_data.get("file_id")
            headers_from_server = upload_data.get("headers", [])

            print(f"✅ Сервер проанализировал файл. Получен file_id: {file_id}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка на этапе загрузки файла: {e}")
        if e.response is not None: print(f"   └─ Ответ сервера: {e.response.text}")
        return

    print_header("Этап 2: Запуск фонового импорта (все колонки как 'string')")

    try:
        # Принудительно задаем тип 'string' для всех колонок,
        # игнорируя то, что предложил сервер.
        column_mappings = [{
            "original_header": h["original_header"],
            "display_name": h["original_header"],
            "value_type": "string",
            "do_import": True
        } for h in headers_from_server]

        config_payload = {
            "new_table_name": NEW_TABLE_NAME,
            "new_table_display_name": f"Дорожная карта (импорт от {time.strftime('%Y-%m-%d')})",
            "columns": column_mappings
        }

        process_url = f"{BASE_URL}/api/imports/process/{file_id}"
        print("-> Отправка финальной конфигурации...")

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


if __name__ == "__main__":
    main()