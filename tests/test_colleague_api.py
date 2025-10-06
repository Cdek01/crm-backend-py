import requests
import json
from datetime import datetime

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---

# URL, который предоставил ваш коллега
COLLEAGUE_API_URL = "http://01c43351-8759-468e-ab2f-d02dfc79ebd2.tunnel4.com/change_table"

# --- Данные, которые мы будем отправлять (имитация) ---
# Структура этих данных должна соответствовать тому, что ожидает ваш коллега.
# Я взял за основу вашу структуру из `external_api_client.py`.
# TEST_PAYLOAD = {
#     "event_type": "update",
#     "table_name": "deals",
#     "entity_id": 123,
#     "changed_data": {
#         "status_sdelki": "Переговоры",
#         "summa_dogovora": 50000.0,
#         "responsible_manager_id": 45
#     },
#     "timestamp": datetime.utcnow().isoformat(),  # Добавим время для уникальности
#     "source_system": "MyCRM"
# }
TEST_PAYLOAD = {"change_json":{"dsfsfs": "sfsfsf", "sfsfsf": "sfsfsf"}}

# ----------------------------------------------------

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def send_test_request():
    """
    Отправляет тестовый POST-запрос на API коллеги и выводит результат.
    """
    print_header("ОТПРАВКА ТЕСТОВОГО ЗАПРОСА НА API КОЛЛЕГИ")

    # Устанавливаем заголовок, сообщающий, что мы отправляем JSON
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        print(f" -> URL для отправки: {COLLEAGUE_API_URL}")
        print(f" -> Тело запроса (Payload):")
        # Красиво печатаем JSON, который будем отправлять
        print(json.dumps(TEST_PAYLOAD, indent=4, ensure_ascii=False))

        # Отправляем POST запрос.
        # `json=...` автоматически преобразует словарь в JSON и установит правильный заголовок.

        response = requests.post(
            url=COLLEAGUE_API_URL,
            json=TEST_PAYLOAD,
            headers=headers,
            timeout=10  # Ждем ответа не более 10 секунд
        )

        print("\n" + "-" * 60)
        print("ПОЛУЧЕН ОТВЕТ ОТ СЕРВЕРА")
        print(f" -> Статус-код: {response.status_code}")

        # Проверяем, есть ли контент в ответе, перед тем как парсить JSON
        if response.text:
            try:
                print(" -> Тело ответа (JSON):")
                print(json.dumps(response.json(), indent=4, ensure_ascii=False))
            except json.JSONDecodeError:
                print(" -> Тело ответа (не JSON):")
                print(response.text)
        else:
            print(" -> Тело ответа: Пустое.")
        # ---------------------------

        # Пытаемся вывести тело ответа
        try:
            print(" -> Тело ответа (JSON):")
            print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        except json.JSONDecodeError:
            print(" -> Тело ответа (не JSON):")
            print(response.text)

    except requests.exceptions.Timeout:
        print("\n" + "-" * 60)
        print("❌ [ОШИБКА] Сервер коллеги не ответил за 10 секунд (Timeout).")
        print("   -> Убедитесь, что сервер запущен и туннель (tunnel4.com) активен.")
    except requests.exceptions.RequestException as e:
        print("\n" + "-" * 60)
        print(f"❌ [ОШИБКА ПОДКЛЮЧЕНИЯ] Не удалось отправить запрос.")
        print(f"   -> Детали: {e}")


if __name__ == "__main__":
    send_test_request()