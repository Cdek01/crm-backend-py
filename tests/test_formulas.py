import requests
import json
import time

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8000"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"


# -----------------
def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}"); exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def register_and_login():
    unique_id = int(time.time())
    email = f"select_tester_{unique_id}@example.com"
    password = "password123"
    reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}

def run_formula_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ С ФОРМУЛОЙ")
        headers = register_and_login()

        table_name = f"order_lines_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Строки заказа (формулы)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        attributes = [
            # Колонки с данными
            {"name": "price", "display_name": "Цена", "value_type": "float"},
            {"name": "quantity", "display_name": "Количество", "value_type": "integer"},
            {"name": "discount", "display_name": "Скидка", "value_type": "float"},
            # Колонка-формула
            {
                "name": "total",
                "display_name": "Итого",
                "value_type": "formula",
                "formula_text": "{price} * {quantity} - {discount}"
            },
        ]
        for attr in attributes:
            requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                          json=attr).raise_for_status()

        print_status(True, f"Создана таблица '{table_name}' с колонкой-формулой.")

        # --- ШАГ 2: СОЗДАНИЕ ДАННЫХ ---
        print_header("ШАГ 2: СОЗДАНИЕ ДАННЫХ ДЛЯ ПРОВЕРКИ ВЫЧИСЛЕНИЙ")

        # Запись 1: Все данные есть
        payload1 = {"price": 100.0, "quantity": 2, "discount": 10.0}
        record_1_id = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload1).json()[0]['id']
        print(f" -> Создана запись #{record_1_id} со всеми данными.")

        # Запись 2: Скидка не указана
        payload2 = {"price": 50.0, "quantity": 5}  # `discount` отсутствует
        record_2_id = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload2).json()[0]['id']
        print(f" -> Создана запись #{record_2_id} с неполными данными.")

        # --- ШАГ 3: ТЕСТИРОВАНИЕ ВЫЧИСЛЕНИЙ ---
        print_header("ШАГ 3: ТЕСТИРОВАНИЕ ВЫЧИСЛЕНИЙ ПРИ ЧТЕНИИ")

        # Тест 1: Проверяем первую запись
        print("\n -> Тест 1: Проверка записи с полными данными...")
        record_1_data = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_1_id}", headers=headers).json()
        print(f"    - Полученные данные: {record_1_data}")
        expected_total_1 = 100.0 * 2 - 10.0
        print_status(
            record_1_data.get('total') == expected_total_1,
            f"Формула 'total' вычислена корректно. Ожидалось: {expected_total_1}, получено: {record_1_data.get('total')}"
        )

        # Тест 2: Проверяем вторую запись
        print("\n -> Тест 2: Проверка записи с неполными данными...")
        record_2_data = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_2_id}", headers=headers).json()
        print(f"    - Полученные данные: {record_2_data}")
        print_status(
            record_2_data.get('total') is None,
            "Формула 'total' корректно вернула None, так как не хватает данных для вычисления."
        )

        # --- ШАГ 4: ТЕСТИРОВАНИЕ ПЕРЕСЧЕТА ПРИ ОБНОВЛЕНИИ ---
        print_header("ШАГ 4: ТЕСТИРОВАНИЕ ПЕРЕСЧЕТА 'НА ЛЕТУ' ПОСЛЕ UPDATE")

        print(f"\n -> Обновляем количество в записи #{record_1_id} с 2 на 3...")
        update_payload = {"quantity": 3}
        requests.put(f"{BASE_URL}/api/data/{table_name}/{record_1_id}", headers=headers,
                     json=update_payload).raise_for_status()

        # Запрашиваем запись снова, чтобы увидеть пересчитанное значение
        updated_record_1_data = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_1_id}", headers=headers).json()
        print(f"    - Полученные обновленные данные: {updated_record_1_data}")

        expected_new_total = 100.0 * 3 - 10.0
        print_status(
            updated_record_1_data.get('total') == expected_new_total,
            f"Формула 'total' корректно пересчиталась после обновления. Ожидалось: {expected_new_total}, получено: {updated_record_1_data.get('total')}"
        )

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ ФУНКЦИОНАЛА 'ФОРМУЛЫ' ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


# ... (вставьте сюда `register_and_login`, `print_status`, `print_header`)

if __name__ == "__main__":
    run_formula_test()