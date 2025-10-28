import requests
import time
import sys
import json
import os
from typing import Dict, Any, Optional

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# Важно: используйте ИНН реальной, действующей компании
INN_TO_TEST = "7707083893"  # ИНН Сбербанка, для примера
# -----------------

# --- Глобальные переменные ---
test_failed = False
# Уникальное имя для тестовой таблицы
ENRICH_TABLE_NAME = f"enrich_test_{int(time.time())}"


# --- Вспомогательные функции (без изменений) ---
def print_status(ok: bool, message: str, data: Optional[Any] = None):
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                print(f"  └─ Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except (TypeError, json.JSONDecodeError):
                print(f"  └─ Данные: {data}")
        print("")
        test_failed = True


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def login() -> Optional[Dict[str, str]]:
    try:
        url = f"{BASE_URL}/api/auth/token"
        r = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})
        r.raise_for_status()
        print_status(True, "Авторизация прошла успешно")
        return {'Authorization': f'Bearer {r.json()["access_token"]}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}", getattr(e, 'response', 'N/A'))
        return None


# --- Функции для подготовки и очистки ---

def setup_test_environment(headers: Dict[str, str]) -> Optional[int]:
    """Создает кастомную таблицу 'Контрагенты' с полями для обогащения."""
    print_header("Подготовка тестового окружения")
    try:
        # 1. Создаем таблицу
        url_create_table = f"{BASE_URL}/api/meta/entity-types"
        payload = {"name": ENRICH_TABLE_NAME, "display_name": "Тестовые Контрагенты (Обогащение)"}
        r_table = requests.post(url_create_table, headers=headers, json=payload)
        r_table.raise_for_status()
        table_id = r_table.json()['id']
        print_status(True, f"Создана тестовая таблица '{ENRICH_TABLE_NAME}' (ID: {table_id})")

        # 2. Создаем колонки с системными именами, которые ожидает наш сервис
        url_add_attr = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
        columns = [
            # Ключевая колонка-триггер
            {"name": "inn", "display_name": "ИНН", "value_type": "string"},
            # Колонки, которые должны заполниться автоматически
            {"name": "full_name", "display_name": "Полное наименование", "value_type": "string"},
            {"name": "short_name", "display_name": "Краткое наименование", "value_type": "string"},
            {"name": "address", "display_name": "Адрес", "value_type": "string"},
            {"name": "manager_name", "display_name": "Руководитель", "value_type": "string"},
            {"name": "company_status", "display_name": "Статус", "value_type": "string"},
        ]
        for col in columns:
            r_col = requests.post(url_add_attr, headers=headers, json=col)
            r_col.raise_for_status()
        print_status(True, "Созданы колонки для обогащения (ИНН, Название, Адрес и др.)")

        return table_id
    except Exception as e:
        print_status(False, "Ошибка при подготовке окружения",
                     getattr(e, 'response', 'N/A').text if hasattr(e, 'response') else str(e))
        return None


def cleanup(headers: Dict[str, str], table_id: Optional[int]):
    """Удаляет тестовую таблицу."""
    if not table_id: return
    print_header("Очистка тестовых данных")
    try:
        url_delete = f"{BASE_URL}/api/meta/entity-types/{table_id}"
        r = requests.delete(url_delete, headers=headers)
        print_status(r.status_code == 204, f"Тестовая таблица '{ENRICH_TABLE_NAME}' (ID: {table_id}) удалена.")
    except Exception as e:
        print_status(False, "Ошибка на этапе очистки", getattr(e, 'response', 'N/A').text)


# --- Основная функция теста ---

def run_enrichment_test(headers: Dict[str, str]):
    """Запускает процесс создания записи и проверки ее автообогащения."""

    print_header("Сценарий: Автообогащение данных по ИНН")

    try:
        # 1. Создаем запись, заполнив ТОЛЬКО ИНН
        url_data = f"{BASE_URL}/api/data/{ENRICH_TABLE_NAME}"
        payload = {"inn": INN_TO_TEST}
        print(f"-> Создаем запись с одним полем: {payload}")
        r_create = requests.post(url_data, headers=headers, json=payload)
        r_create.raise_for_status()

        # Получаем ID созданной записи из ответа
        # Ответ POST - это список, берем первый элемент
        created_entity_id = r_create.json()['data'][0]['id']
        print_status(True, f"Запись успешно создана. ID: {created_entity_id}")

        # 2. Ждем, пока отработает фоновая задача
        wait_time = 20  # DaData может отвечать с задержкой
        print(f"-> Ждем {wait_time} секунд, пока Celery получит данные от DaData и обновит запись...")
        time.sleep(wait_time)

        # 3. Запрашиваем эту же запись снова, чтобы проверить результат
        url_get = f"{BASE_URL}/api/data/{ENRICH_TABLE_NAME}/{created_entity_id}"
        print(f"-> Запрашиваем обновленную запись: GET {url_get}")
        r_get = requests.get(url_get, headers=headers)
        r_get.raise_for_status()
        enriched_data = r_get.json()
        print(enriched_data = r_get.json())

        # 4. Проводим проверки
        print("-> Проверяем результат обогащения:")

        # Проверка 1: Поле 'full_name' должно было заполниться и не быть пустым
        full_name = enriched_data.get("full_name")
        ok_name = bool(full_name and "сбербанк" in full_name.lower())
        print_status(ok_name, f"Поле 'Полное наименование' заполнено: '{full_name}'")

        # Проверка 2: Поле 'address' должно было заполниться
        address = enriched_data.get("address")
        ok_address = bool(address)
        print_status(ok_address, f"Поле 'Адрес' заполнено: '{address}'")

        # Проверка 3: Поле 'manager_name' должно было заполниться
        manager = enriched_data.get("manager_name")
        ok_manager = bool(manager)
        print_status(ok_manager, f"Поле 'Руководитель' заполнено: '{manager}'")

    except Exception as e:
        print_status(False, f"Ошибка при выполнении теста обогащения: {e}",
                     getattr(e, 'response', 'N/A').text if hasattr(e, 'response') else str(e))


def main():
    """Главная функция для запуска теста."""
    print_header("Авторизация")
    headers = login()
    if not headers:
        sys.exit(1)

    table_id = None
    try:
        table_id = setup_test_environment(headers)
        if table_id:
            run_enrichment_test(headers)
    finally:
        cleanup(headers, table_id)

    print_header("Итоги тестирования")
    if test_failed:
        print("❌ Тестирование автообогащения завершилось с ошибками.")
        sys.exit(1)
    else:
        print("✅ Тест автообогащения прошел успешно.")


if __name__ == "__main__":
    main()