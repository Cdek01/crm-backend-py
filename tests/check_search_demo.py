import requests
import time
import sys
import json

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"


# -----------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}\n")
        # Устанавливаем флаг, что тест провален
        global test_failed
        test_failed = True


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login():
    try:
        auth_payload = {'username': EMAIL, 'password': PASSWORD}
        token_resp = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_resp.raise_for_status()
        return {'Authorization': f'Bearer {token_resp.json()["access_token"]}'}
    except Exception as e:
        print(f"Критическая ошибка при авторизации: {e}")
        return None


# --- Основная функция демонстрации ---
def run_search_demo():
    global test_failed
    test_failed = False

    headers = login()
    if not headers: return

    ids = {}
    table_name = f"search_demo_{int(time.time())}"

    try:
        # --- ШАГ 1: Подготовка ---
        print_header("Шаг 1: Создание и наполнение тестовой таблицы")

        # Создаем таблицу и колонки
        type_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                                  json={"name": table_name, "display_name": "Демо универсального поиска"})
        type_resp.raise_for_status();
        ids['table_id'] = type_resp.json()["id"]

        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}/attributes", headers=headers,
                      json={"name": "company_name", "display_name": "Название",
                            "value_type": "string"}).raise_for_status()
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}/attributes", headers=headers,
                      json={"name": "phone", "display_name": "Телефон", "value_type": "string"}).raise_for_status()
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}/attributes", headers=headers,
                      json={"name": "city", "display_name": "Город", "value_type": "string"}).raise_for_status()
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}/attributes", headers=headers,
                      json={"name": "order_id", "display_name": "ID Заказа",
                            "value_type": "integer"}).raise_for_status()

        # Наполняем данными
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                      json={"company_name": "ООО Ромашка", "phone": "79001112233", "city": "Москва",
                            "order_id": 101}).raise_for_status()
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                      json={"company_name": "ИП Васильков", "phone": "79114445566", "city": "СПб",
                            "order_id": 102}).raise_for_status()
        requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers,
                      json={"company_name": "ООО Строй-Траст", "phone": "79227778899", "city": "Москва",
                            "order_id": 103}).raise_for_status()
        print_status(True, "Тестовые данные успешно загружены.")

        # --- ШАГ 2: Демонстрация поисковых запросов ---
        print_header("Шаг 2: Демонстрация поисковых запросов")

        test_queries = [
            {"description": "Поиск по части строки ('ООО')", "q": "ООО", "expected_count": 2},
            {"description": "Регистронезависимый поиск ('ромашка')", "q": "ромашка", "expected_count": 1},
            {"description": "Поиск по номеру телефона ('79114445566')", "q": "79114445566", "expected_count": 1},
            {"description": "Поиск по числовому ID заказа ('103')", "q": "103", "expected_count": 1},
            {"description": "Поиск несуществующих данных ('Абракадабра')", "q": "Абракадабра", "expected_count": 0},
            {"description": "Комбинированный поиск ('ООО' + фильтр по городу 'Москва')", "q": "ООО",
             "filters": json.dumps([{"field": "city", "op": "eq", "value": "Москва"}]), "expected_count": 2}
        ]

        for test in test_queries:
            print(f"\n--- Тестируем: {test['description']} ---")

            params = {"q": test["q"]}
            if "filters" in test:
                params["filters"] = test["filters"]

            response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                found_count = data.get('total', 0)
                print(f" -> Запрос: {response.url}")
                print(f" -> Найдено записей: {found_count} (Ожидалось: {test['expected_count']})")
                if found_count > 0:
                    print(" -> Результаты:")
                    for item in data.get('data', []):
                        print(
                            f"    - ID: {item.get('id')}, Название: {item.get('company_name', 'N/A')}, Город: {item.get('city', 'N/A')}")
                print_status(found_count == test['expected_count'],
                             "Количество найденных записей соответствует ожиданиям.")
            else:
                print_status(False, f"Запрос завершился с ошибкой {response.status_code}: {response.text}")

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    finally:
        # --- ШАГ 3: Очистка ---
        if 'table_id' in ids:
            print_header("Шаг 3: Очистка (удаление тестовой таблицы)")
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['table_id']}", headers=headers)
            print(f" -> Временная таблица '{table_name}' удалена.")

        if not test_failed:
            print("\n" + "🎉" * 20 + "\n Все тесты универсального поиска успешно пройдены! \n" + "🎉" * 20)
        else:
            sys.exit(1)


if __name__ == "__main__":
    run_search_demo()