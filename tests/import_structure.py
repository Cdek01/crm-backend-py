import requests
import json
import sys
import time
import os
import pandas as pd
from typing import Optional

BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
FILE_PATH = r"Структура БД.xlsx"
SHEET_NAME = "Дорожная карта"
NEW_TABLE_NAME = f"roadmap_direct_{int(time.time())}"


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
        print(f"❌ Критическая ошибка: {e}")
        if e.response is not None: print(f"   └─ Ответ: {e.response.text}")
        return None


def direct_import(token: str):
    headers = {"Authorization": f"Bearer {token}"}

    print_header(f"Этап 1: Чтение и очистка листа '{SHEET_NAME}'")
    try:
        df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=1)  # Предполагаем, что заголовки на 2-й строке
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(axis=0, how='all', inplace=True)

        # Принудительно конвертируем все в строки
        df = df.astype(str).replace({'nan': None, 'NaT': None})

        print(f"✅ Файл прочитан. Найдено {len(df)} строк для импорта.")
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return

    print_header(f"Этап 2: Создание таблицы '{NEW_TABLE_NAME}' и ее колонок")
    try:
        # 1. Создаем таблицу
        meta_url = f"{BASE_URL}/api/meta/entity-types"
        meta_payload = {"name": NEW_TABLE_NAME, "display_name": f"Дорожная карта (прямой импорт)"}
        r_meta = requests.post(meta_url, headers=headers, json=meta_payload)
        r_meta.raise_for_status()
        table_info = r_meta.json()
        table_id = table_info["id"]
        print(f"✅ Таблица создана, ID: {table_id}")

        # 2. Создаем колонки (все как string)
        for col_name in df.columns:
            col_payload = {"name": str(col_name).lower().replace(' ', '_'), "display_name": str(col_name),
                           "value_type": "string"}
            r_col = requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                                  json=col_payload)
            r_col.raise_for_status()
        print(f"✅ Создано {len(df.columns)} строковых колонок.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при создании структуры таблицы: {e}")
        if e.response is not None: print(f"   └─ Ответ: {e.response.text}")
        return

    print_header("Этап 3: Построчный импорт данных")
    imported_count = 0
    for index, row in df.iterrows():
        try:
            # Преобразуем строку DataFrame в словарь для JSON
            row_data = {str(col).lower().replace(' ', '_'): val for col, val in row.items() if val is not None}

            if not row_data:
                continue  # Пропускаем пустые строки

            data_url = f"{BASE_URL}/api/data/{NEW_TABLE_NAME}"
            r_data = requests.post(data_url, headers=headers, json=row_data)
            r_data.raise_for_status()

            imported_count += 1
            print(f"  -> Строка {index + 1}/{len(df)} импортирована успешно.")

        except requests.exceptions.RequestException as e:
            print(f"❌ ОШИБКА на строке {index + 1}! Импорт остановлен.")
            print(f"   ├─ Данные строки: {row.to_dict()}")
            if e.response is not None:
                print(f"   └─ Ответ сервера (статус {e.response.status_code}): {e.response.text}")
            # Прерываем цикл после первой ошибки
            break

    print(f"\n✅ Импорт завершен. Всего импортировано: {imported_count} из {len(df)} строк.")


def main():
    auth_token = get_auth_token()
    if not auth_token: sys.exit(1)
    direct_import(auth_token)


if __name__ == "__main__":
    main()