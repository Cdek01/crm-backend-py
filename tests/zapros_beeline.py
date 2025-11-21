import requests
import json
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "https://cloudpbx.beeline.ru/apis/portal"
API_TOKEN = "f0744ced-44e3-4d88-9ec7-f7823d83d634"

# --- ЗАГОЛОВКИ ---
headers = {
    "X-MPBX-API-AUTH-TOKEN": API_TOKEN
}


def print_response(response):
    """Вспомогательная функция для красивого вывода ответа от API."""
    print(f"Статус-код: {response.status_code}")
    try:
        parsed_json = response.json()
        print("Ответ от сервера:")
        print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("Ответ от сервера (не JSON):")
        print(response.text)


def get_abonents():
    """Получает список всех абонентов."""
    print("\n" + "=" * 20 + " 1. ПОЛУЧЕНИЕ СПИСКА АБОНЕНТОВ " + "=" * 20)
    endpoint = "/abonents"
    url = BASE_URL + endpoint

    try:
        print(f"Отправка запроса на: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        print("Запрос выполнен успешно!")
        print_response(response)

    except requests.exceptions.HTTPError as e:
        print(f"!!! Ошибка HTTP: {e.response.status_code} {e.response.reason}")
        print_response(e.response)
    except requests.exceptions.RequestException as e:
        print(f"!!! Критическая ошибка при выполнении запроса: {e}")


def get_records():
    """Получает список записей разговоров."""
    print("\n" + "=" * 20 + " 2. ПОЛУЧЕНИЕ СПИСКА ЗАПИСЕЙ РАЗГОВОРОВ " + "=" * 20)
    endpoint = "/records"
    url = BASE_URL + endpoint

    try:
        print(f"Отправка запроса на: {url}")

        date_to = datetime.now()
        date_from = date_to - timedelta(days=7)

        params = {
            # --- ИЗМЕНЕНИЕ: Формат даты теперь ISO-8601 (гггг-мм-дд) ---
            "dateFrom": date_from.strftime("%Y-%m-%d"),
            "dateTo": date_to.strftime("%Y-%m-%d")
        }
        print(f"Используемые параметры: {params}")

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        print("Запрос выполнен успешно!")
        print_response(response)

    except requests.exceptions.HTTPError as e:
        print(f"!!! Ошибка HTTP: {e.response.status_code} {e.response.reason}")
        print_response(e.response)
    except requests.exceptions.RequestException as e:
        print(f"!!! Критическая ошибка при выполнении запроса: {e}")


def get_statistics():
    """Получает общую статистику."""
    print("\n" + "=" * 20 + " 3. ПОЛУЧЕНИЕ СТАТИСТИКИ " + "=" * 20)
    endpoint = "/v2/statistics"
    url = BASE_URL + endpoint

    try:
        print(f"Отправка запроса на: {url}")

        # --- ИЗМЕНЕНИЕ: Добавляем параметры пагинации ---
        params = {
            "page": 2,  # Номер страницы (начинается с 0)
            "pageSize": 100  # Количество записей на странице
        }
        print(f"Используемые параметры: {params}")

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        print("Запрос выполнен успешно!")
        print_response(response)

    except requests.exceptions.HTTPError as e:
        print(f"!!! Ошибка HTTP: {e.response.status_code} {e.response.reason}")
        print_response(e.response)
    except requests.exceptions.RequestException as e:
        print(f"!!! Критическая ошибка при выполнении запроса: {e}")


if __name__ == "__main__":
    get_abonents()
    get_records()
    get_statistics()
    print("\n" + "=" * 20 + " Проверка API завершена " + "=" * 20)