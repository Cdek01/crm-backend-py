import requests
import sys
import json
import time
from typing import Dict, Any, Optional

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Глобальные переменные ---
test_failed = False
# Уникальное имя для тестовой таблицы, чтобы избежать конфликтов
DEALS_TABLE_NAME = f"deals_ai_test_{int(time.time())}"


# --- Вспомогательные функции (без изменений) ---
def print_status(ok: bool, message: str, data: Optional[Any] = None):
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                print(f"  └─ Ответ сервера/модели: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except (TypeError, json.JSONDecodeError):
                print(f"  └─ Ответ сервера/модели: {data}")
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
    """Создает кастомную таблицу 'Сделки' с нужными полями и данными."""
    print_header("Подготовка тестового окружения")
    try:
        # 1. Создаем таблицу 'Сделки'
        url_create_table = f"{BASE_URL}/api/meta/entity-types"
        payload = {"name": DEALS_TABLE_NAME, "display_name": "Тестовые Сделки (AI)"}
        r_table = requests.post(url_create_table, headers=headers, json=payload)
        r_table.raise_for_status()
        table_id = r_table.json()['id']
        print_status(True, f"Создана тестовая таблица '{DEALS_TABLE_NAME}' (ID: {table_id})")

        # 2. Создаем колонки
        url_add_attr = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
        columns = [
            {"name": "deal_name", "display_name": "Название сделки", "value_type": "string"},
            {"name": "amount", "display_name": "Сумма", "value_type": "float"},
            {"name": "manager", "display_name": "Ответственный", "value_type": "string"},
            {"name": "status", "display_name": "Статус", "value_type": "string"},
        ]
        for col in columns:
            r_col = requests.post(url_add_attr, headers=headers, json=col)
            r_col.raise_for_status()
        print_status(True, "Созданы тестовые колонки: Название, Сумма, Ответственный, Статус")

        # 3. Создаем тестовые данные
        url_add_data = f"{BASE_URL}/api/data/{DEALS_TABLE_NAME}"
        deals_data = [
            {"deal_name": "Сделка с ООО Ромашка", "amount": 15000, "manager": "Иван", "status": "Новая"},
            {"deal_name": "Контракт с ИП Петров", "amount": 5000, "manager": "Анна", "status": "В работе"},
            {"deal_name": "Продажа ЗАО Вектор", "amount": 25000, "manager": "Иван", "status": "Новая"},
        ]
        for deal in deals_data:
            # Используем POST, который возвращает весь список, чтобы не делать лишних запросов
            r_deal = requests.post(url_add_data, headers=headers, json=deal)
            r_deal.raise_for_status()
        print_status(True, "Созданы 3 тестовые сделки")

        return table_id

    except Exception as e:
        print_status(False, "Ошибка при подготовке окружения",
                     getattr(e, 'response', 'N/A').text if hasattr(e, 'response') else str(e))
        return None


def cleanup(headers: Dict[str, str], table_id: Optional[int]):
    """Удаляет тестовую таблицу."""
    if not table_id:
        return
    print_header("Очистка тестовых данных")
    try:
        url_delete = f"{BASE_URL}/api/meta/entity-types/{table_id}"
        r = requests.delete(url_delete, headers=headers)
        print_status(r.status_code == 204, f"Тестовая таблица '{DEALS_TABLE_NAME}' (ID: {table_id}) удалена.")
    except Exception as e:
        print_status(False, "Ошибка на этапе очистки", getattr(e, 'response', 'N/A').text)


# --- Основная функция теста ---

def run_ai_test(headers: Dict[str, str]):
    """Отправляет запросы на AI-парсер и проверяет ответы."""

    print_header("Сценарий: Запрос к созданной таблице")

    query = "покажи все новые сделки ивана на сумму больше 10000"

    payload = {
        "query": query,
        "table_name": DEALS_TABLE_NAME
    }

    print(f"-> Отправляем запрос: '{query}' для таблицы '{DEALS_TABLE_NAME}'")

    try:
        url = f"{BASE_URL}/api/ai/parse-filter"
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        print(data)
        filters = data.get("filters")

        ok_format = isinstance(filters, list) and len(filters) == 3
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Теперь мы всегда будем видеть, что именно вернул AI
        print_status(ok_format, "Получен корректный формат ответа (список из 3 фильтров)", data)
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        if ok_format:
            # Можно добавить более строгие проверки содержимого
            fields = {f['field'] for f in filters}
            ok_fields = {'status', 'manager', 'amount'}.issubset(fields)
            print_status(ok_fields, "Сгенерированы фильтры для правильных полей")

    except Exception as e:
        print_status(False, f"Ошибка при выполнении AI-запроса: {e}",
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
            # Запускаем тест только если окружение было создано успешно
            run_ai_test(headers)
    finally:
       # Удаляем тестовую таблицу в любом случае
        print("должно быть cleanup(headers, table_id)")
        # cleanup(headers, table_id)

    print_header("Итоги тестирования")
    if test_failed:
        print("❌ Тестирование AI-парсера завершилось с ошибками.")
        sys.exit(1)
    else:
        print("✅ Тесты AI-парсера прошли успешно.")


if __name__ == "__main__":
    main()

order_cost = int(input())
if order_cost >= 2000:
    print("Доставка бесплатная")
    print(order_cost)
else:
    print("1. Самовывоз 2. Доставка курьером")
    choice = int(input())

    if choice == 1:
        print("Выбран самовывоз")
        total = order_cost + 100
        print(total)
    elif choice == 2:
        print("Выбрана доставка курьером")
        total = order_cost + 300
print(total)