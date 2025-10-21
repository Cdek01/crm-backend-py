
import requests
import time
import random
from faker import Faker
from tqdm import tqdm

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
BASE_URL = "http://89.111.169.47:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"

# --- Параметры генерации данных ---
# ВНИМАНИЕ: Большое количество строк ( > 1000) будет выполняться ОЧЕНЬ долго.
NUM_ROWS_TO_CREATE = 10000
NUM_COLUMNS = 30
# -------------------------------------------

# Инициализация генератора фейковых данных
fake = Faker('ru_RU')


# --- Вспомогательные функции (из вашего примера) ---
def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}");
        exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def register_and_login():
    """Регистрирует нового пользователя и возвращает заголовки для авторизации."""
    unique_id = int(time.time())
    email = f"1@example.com"
    password = "string"

    try:

        # Авторизация
        auth_payload = {'username': email, 'password': password}
        token_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_response.raise_for_status()

        token = token_response.json()['access_token']
        print_status(True, f"Успешная авторизация для пользователя {email}")
        return {'Authorization': f'Bearer {token}'}
    except requests.exceptions.HTTPError as e:
        print_status(False, f"Ошибка регистрации/авторизации: {e.response.text}")
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}")


# --- Основная функция ---
def run_data_loading():
    table_id = None
    headers = None

    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header(f"ПОДГОТОВКА: СОЗДАНИЕ ТАБЛИЦЫ С {NUM_COLUMNS} КОЛОНКАМИ")
        headers = register_and_login()

        table_name = f"load_test_{int(time.time())}"
        table_config = {"name": table_name, "display_name": f"Нагрузочный тест ({NUM_ROWS_TO_CREATE} строк)"}

        # Создаем таблицу
        table_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config)
        table_resp.raise_for_status()
        table_id = table_resp.json()['id']

        # Создаем колонки
        created_attributes = []  # Список словарей с name и value_type
        print(f"Создание {NUM_COLUMNS} колонок...")
        for i in tqdm(range(NUM_COLUMNS), desc="Создание колонок"):
            col_type = random.choice(["string", "integer", "float", "boolean", "date"])
            attr_config = {
                "name": f"col_{i + 1}_{col_type}",
                "display_name": f"Колонка {i + 1} ({fake.word()})",
                "value_type": col_type
            }
            url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
            resp = requests.post(url, headers=headers, json=attr_config)
            resp.raise_for_status()
            created_attributes.append({"name": attr_config["name"], "type": col_type})

        print_status(True, f"Успешно создана таблица '{table_name}' с {len(created_attributes)} колонками.")

        # --- ШАГ 2: ЗАГРУЗКА ДАННЫХ ---
        print_header(f"ШАГ 2: ЗАГРУЗКА {NUM_ROWS_TO_CREATE} СТРОК В ТАБЛИЦУ")

        data_url = f"{BASE_URL}/api/data/{table_name}"

        for i in tqdm(range(NUM_ROWS_TO_CREATE), desc="Загрузка данных"):
            row_payload = {}
            # Генерируем данные для каждой колонки
            for attr in created_attributes:
                if attr['type'] == 'string':
                    row_payload[attr['name']] = fake.company()
                elif attr['type'] == 'integer':
                    row_payload[attr['name']] = fake.random_int(min=1, max=10000)
                elif attr['type'] == 'float':
                    row_payload[attr['name']] = fake.pyfloat(left_digits=5, right_digits=2, positive=True)
                elif attr['type'] == 'boolean':
                    row_payload[attr['name']] = random.choice([True, False])
                elif attr['type'] == 'date':
                    row_payload[attr['name']] = fake.date_this_year().isoformat()

            # Отправляем запрос на создание одной строки
            post_resp = requests.post(data_url, headers=headers, json=row_payload)
            # Проверяем только на критические ошибки (5xx), чтобы не прерывать долгий процесс
            if post_resp.status_code >= 500:
                print(f"\nКритическая ошибка сервера на строке {i + 1}: {post_resp.text}")
                break

        print_status(True, f"Процесс загрузки {NUM_ROWS_TO_CREATE} строк завершен.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ЗАГРУЗКА ДАННЫХ УСПЕШНО ЗАВЕРШЕНА! 🎉🎉🎉")
        print(f"Таблица '{table_name}' (ID: {table_id}) наполнена данными.")
        print("Вы можете проверить ее через API или в админ-панели.")


    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    # finally:
    #     # --- ШАГ 3: ОЧИСТКА (Опционально) ---
    #     # Если вы хотите, чтобы таблица осталась для тестов, закомментируйте этот блок
    #     if table_id and headers:
    #         print_header("ШАГ 3: ОЧИСТКА (УДАЛЕНИЕ ТЕСТОВОЙ ТАБЛИЦЫ)")
    #         cleanup_url = f"{BASE_URL}/api/meta/entity-types/{table_id}"
    #         requests.delete(cleanup_url, headers=headers)
    #         print(f"Тестовая таблица с ID {table_id} была удалена.")


if __name__ == "__main__":
    run_data_loading()

















