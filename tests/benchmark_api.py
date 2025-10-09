import requests
import time
import random
from faker import Faker

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"

# --- Параметры бенчмарка ---
NUM_RECORDS_TO_CREATE = 100  # Сколько записей создать
NUM_RECORDS_TO_UPDATE = 20  # Сколько записей обновить для теста
NUM_RECORDS_TO_READ = 20  # Сколько записей прочитать по ID для теста
# -----------------

fake = Faker('ru_RU')


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
    email = f"a1@example.com"
    password = "aaaaaaaaaa"
    reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}

def run_benchmark():
    results = {}

    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА СРЕДЫ ДЛЯ БЕНЧМАРКА")
        headers = register_and_login()

        table_name = f"products_bench_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Продукты (бенчмарк)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']

        attributes = [
            {"name": "product_name", "display_name": "Название", "value_type": "string"},
            {"name": "price", "display_name": "Цена", "value_type": "float"},
            {"name": "stock_quantity", "display_name": "Кол-во на складе", "value_type": "integer"},
        ]
        for attr in attributes:
            requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                          json=attr).raise_for_status()

        print(f" -> Тестовая таблица '{table_name}' создана.")

        # --- ШАГ 2: БЕНЧМАРК СОЗДАНИЯ (CREATE) ---
        # --- ШАГ 2: БЕНЧМАРК СОЗДАНИЯ (CREATE) ---
        print_header(f"ШАГ 2: СОЗДАНИЕ {NUM_RECORDS_TO_CREATE} ЗАПИСЕЙ")
        created_ids = []
        start_time = time.perf_counter()
        for i in range(NUM_RECORDS_TO_CREATE):
            payload = {
                "product_name": f"Товар {i}",
                "price": round(random.uniform(10.0, 1000.0), 2),
                "stock_quantity": random.randint(0, 100)
            }

            # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
            # Ответ теперь - это список. Новая запись - первая в списке.
            response_list = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload).json()

            # Проверяем, что ответ не пустой
            if not response_list:
                print(f"❌ ОШИБКА: POST-запрос вернул пустой список!")
                exit(1)

            new_entity_id = response_list[0]['id']
            created_ids.append(new_entity_id)
            # ---------------------------

        end_time = time.perf_counter()
        total_time = end_time - start_time
        results["CREATE (single)"] = (total_time / NUM_RECORDS_TO_CREATE) * 1000
        print(f" -> Готово. Среднее время на создание одной записи: {results['CREATE (single)']:.2f} мс")

        # --- ШАГ 3: БЕНЧМАРК ЧТЕНИЯ СПИСКА (READ LIST) ---
        print_header(f"ШАГ 3: ЧТЕНИЕ СПИСКА ИЗ {NUM_RECORDS_TO_CREATE} ЗАПИСЕЙ")
        start_time = time.perf_counter()
        requests.get(f"{BASE_URL}/api/data/{table_name}?limit={NUM_RECORDS_TO_CREATE}",
                     headers=headers).raise_for_status()
        end_time = time.perf_counter()
        results["READ (list)"] = (end_time - start_time) * 1000
        print(f" -> Готово. Время на получение списка: {results['READ (list)']:.2f} мс")

        # --- ШАГ 4: БЕНЧМАРК ОБНОВЛЕНИЯ (UPDATE) ---
        print_header(f"ШАГ 4: ОБНОВЛЕНИЕ {NUM_RECORDS_TO_UPDATE} СЛУЧАЙНЫХ ЗАПИСЕЙ")
        ids_to_update = random.sample(created_ids, NUM_RECORDS_TO_UPDATE)
        start_time = time.perf_counter()
        for entity_id in ids_to_update:
            payload = {"price": round(random.uniform(5.0, 50.0), 2)}
            requests.put(f"{BASE_URL}/api/data/{table_name}/{entity_id}", headers=headers,
                         json=payload).raise_for_status()
        end_time = time.perf_counter()
        total_time = end_time - start_time
        results["UPDATE (single)"] = (total_time / NUM_RECORDS_TO_UPDATE) * 1000
        print(f" -> Готово. Среднее время на обновление одной записи: {results['UPDATE (single)']:.2f} мс")

        # --- ШАГ 5: БЕНЧМАРК ЧТЕНИЯ ОДНОЙ ЗАПИСИ (READ SINGLE) ---
        print_header(f"ШАГ 5: ЧТЕНИЕ {NUM_RECORDS_TO_READ} СЛУЧАЙНЫХ ЗАПИСЕЙ ПО ID")
        ids_to_read = random.sample(created_ids, NUM_RECORDS_TO_READ)
        start_time = time.perf_counter()
        for entity_id in ids_to_read:
            requests.get(f"{BASE_URL}/api/data/{table_name}/{entity_id}", headers=headers).raise_for_status()
        end_time = time.perf_counter()
        total_time = end_time - start_time
        results["READ (single)"] = (total_time / NUM_RECORDS_TO_READ) * 1000
        print(f" -> Готово. Среднее время на чтение одной записи: {results['READ (single)']:.2f} мс")

        # --- ШАГ 6: БЕНЧМАРК УДАЛЕНИЯ (DELETE) ---
        # (Пропускаем, чтобы не замедлять тест еще больше, можно раскомментировать при необходимости)
        # ...

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
    finally:
        # --- ВЫВОД РЕЗУЛЬТАТОВ ---
        print_header("РЕЗУЛЬТАТЫ БЕНЧМАРКА")
        if results:
            print(f"{'Операция':<20} | {'Среднее время (мс)':<20}")
            print("-" * 43)
            for op, timing in results.items():
                print(f"{op:<20} | {timing:<20.2f}")
        else:
            print("Бенчмарк не был завершен из-за ошибки.")




if __name__ == "__main__":
    run_benchmark()