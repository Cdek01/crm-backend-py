import json

import requests
import time
import sys

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"


# ---------------------------------------------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        # Не выходим из скрипта при ошибке, чтобы выполнился блок finally
        # sys.exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login():
    """Аутентифицируется и возвращает заголовки для авторизации."""
    try:
        auth_payload = {'username': EMAIL, 'password': PASSWORD}
        token_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_response.raise_for_status()
        token = token_response.json()['access_token']
        return {'Authorization': f'Bearer {token}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}")
        return None


# --- Основная функция демонстрации ---
def run_post_response_check():
    headers = login()
    if not headers:
        print_status(False, "Авторизация не удалась. Прерывание скрипта.")
        return

    table_name = f"post_response_test_{int(time.time())}"
    table_id = None

    try:
        # --- ШАГ 1: Подготовка ---
        print_header("Шаг 1: Создание временной таблицы")

        type_resp = requests.post(
            f"{BASE_URL}/api/meta/entity-types", headers=headers,
            json={"name": table_name, "display_name": "Тест ответа POST"}
        )
        type_resp.raise_for_status()
        table_id = type_resp.json()["id"]

        requests.post(
            f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
            json={"name": "name", "display_name": "Название", "value_type": "string"}
        ).raise_for_status()
        print_status(True, f"Временная таблица '{table_name}' успешно создана.")

        # --- ШАГ 2: Основное действие - Создание одной записи ---
        print_header("Шаг 2: Отправка POST-запроса на создание строки")

        payload = {"name": "Моя первая тестовая запись"}
        response = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload)

        print(f" -> Отправлен POST на /api/data/{table_name}")
        print(f" -> Тело запроса: {payload}")

        # --- ШАГ 3: Проверка ответа сервера ---
        print_header("Шаг 3: Анализ ответа от сервера")

        print_status(response.status_code == 201, f"Статус код ответа: {response.status_code} (Ожидалось: 201 Created)")

        # Если статус код неверный, нет смысла продолжать
        if response.status_code != 201:
            print(f"Тело ответа: {response.text}")
            raise Exception("Получен неверный статус код")

        data = response.json()
        print(f"\nПолучено тело ответа:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n")

        print("--- Начинаем проверку структуры ---")
        print_status(isinstance(data, dict), "1. Тело ответа является объектом (словарем).")
        print_status('total' in data, "2. В ответе присутствует ключ 'total'.")
        print_status(isinstance(data.get('total'), int), "3. Значение ключа 'total' является числом.")
        print_status('data' in data, "4. В ответе присутствует ключ 'data'.")
        print_status(isinstance(data.get('data'), list), "5. Значение ключа 'data' является массивом (списком).")

        # Проверяем содержимое массива data
        if isinstance(data.get('data'), list):
            data_array = data['data']
            print_status(len(data_array) > 0, "6. Массив 'data' не пустой.")

            if len(data_array) > 0:
                created_row = data_array[0]
                print_status(isinstance(created_row, dict), "7. Элемент внутри 'data' является объектом.")
                print_status('id' in created_row and isinstance(created_row['id'], int),
                             "8. У созданной записи есть числовой 'id' от сервера.")
                print_status(created_row.get('name') == payload['name'],
                             "9. Данные в созданной записи совпадают с отправленными.")

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    finally:
        # --- ШАГ 4: Очистка ---
        if table_id:
            print_header("Шаг 4: Очистка (удаление временной таблицы)")
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers)
            print(f" -> Временная таблица '{table_name}' удалена.")
            print_status(True, "Очистка завершена.")


if __name__ == "__main__":
    run_post_response_check()
