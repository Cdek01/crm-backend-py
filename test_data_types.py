import requests
import json
import time
from datetime import datetime, timedelta

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---

BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера

# --- Данные СУЩЕСТВУЮЩЕГО пользователя ---
USER_EMAIL = "user-b@example.com"
USER_PASSWORD = "password-b"



# ----------------------------------------------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}"); exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login(email, password):
    """
    Авторизуется под существующим пользователем.
    Возвращает словарь с заголовками для аутентификации.
    """
    auth_payload = {'username': email, 'password': password}
    auth_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
    auth_response.raise_for_status()  # Выбросит исключение, если авторизация не удалась
    token = auth_response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


# --- ОСНОВНОЙ ТЕСТ ---
def run_data_types_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ШАГ 1: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТИПИЗИРОВАННОЙ ТАБЛИЦЫ")

        # Используем простую функцию входа
        headers = login(USER_EMAIL, USER_PASSWORD)
        print(f" -> Успешная авторизация под пользователем: {USER_EMAIL}")

        table_name = f"typed_assets_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Типизированные Активы"}
        table_id_response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config)
        table_id_response.raise_for_status()
        table_id = table_id_response.json()['id']

        attributes = [
            {"name": "asset_name", "display_name": "Название", "value_type": "string"},
            {"name": "inventory_number", "display_name": "Инв. номер", "value_type": "integer"},
            {"name": "cost", "display_name": "Стоимость", "value_type": "float"},
            {"name": "purchase_date", "display_name": "Дата покупки", "value_type": "date"},
            {"name": "is_active", "display_name": "Активен", "value_type": "boolean"},
        ]
        for attr in attributes:
            requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                          json=attr).raise_for_status()

        print_status(True, f"Создана таблица '{table_name}' со всеми типами колонок.")

        # --- ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ЗАПИСИ ---
        print_header("ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ТИПИЗИРОВАННОЙ ЗАПИСИ")

        date_value = datetime.now()
        record_payload = {
            "asset_name": "Ноутбук",
            "inventory_number": 10512,
            "cost": 1500.99,
            "purchase_date": date_value.isoformat(),
            "is_active": True
        }
        create_resp = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=record_payload)
        create_resp.raise_for_status()
        created_record = create_resp.json()[0]
        record_id = created_record['id']

        print(f" -> Создана запись с ID: {record_id}")

        # Проверяем типы и значения
        print_status(created_record.get('asset_name') == "Ноутбук", "Тип 'string' сохранился корректно.")
        print_status(created_record.get('inventory_number') == 10512, "Тип 'integer' сохранился корректно.")
        print_status(created_record.get('cost') == 1500.99, "Тип 'float' сохранился корректно.")
        print_status(created_record.get('is_active') is True, "Тип 'boolean' сохранился корректно.")
        print_status(
            created_record.get('purchase_date', '').startswith(date_value.isoformat()[:19]),
            "Тип 'date' сохранился корректно."
        )

        # --- ШАГ 3: ПРОВЕРКА СОРТИРОВКИ ПО РАЗНЫМ ТИПАМ ---
        print_header("ШАГ 3: ПРОВЕРКА СОРТИРОВКИ ПО ТИПИЗИРОВАННЫМ ПОЛЯМ")

        # Добавим еще две записи для сортировки
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={
            "asset_name": "Стол", "inventory_number": 500, "cost": 350.0,
            "purchase_date": (datetime.now() - timedelta(days=10)).isoformat(), "is_active": True
        })
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={
            "asset_name": "Кресло", "inventory_number": 20000, "cost": 500.50,
            "purchase_date": (datetime.now() + timedelta(days=5)).isoformat(), "is_active": False
        })

        # Проверяем сортировку по float
        params = {"sort_by": "cost", "sort_order": "desc"}
        resp = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)
        resp.raise_for_status()
        sorted_by_cost = [item.get('cost') for item in resp.json()]
        print(f" -> Сортировка по стоимости (desc): {sorted_by_cost}")
        print_status(sorted_by_cost == [1500.99, 500.50, 350.0], "Сортировка по 'float' работает.")

        # Проверяем сортировку по boolean
        params = {"sort_by": "is_active", "sort_order": "desc"}
        resp = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)
        resp.raise_for_status()
        sorted_by_active = [item.get('is_active') for item in resp.json()]
        print(f" -> Сортировка по активности (desc): {sorted_by_active}")
        print_status(sorted_by_active == [True, True, False], "Сортировка по 'boolean' работает.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ ТИПОВ ДАННЫХ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP.")
        print(f"   URL: {e.request.method} {e.request.url}")
        print(f"   Статус: {e.response.status_code}")
        print(f"   Ответ: {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


if __name__ == "__main__":
    run_data_types_test()