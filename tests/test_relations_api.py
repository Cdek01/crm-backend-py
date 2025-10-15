import requests
from typing import Dict, List

# --- ГЛАВНЫЕ НАСТРОЙКИ ---
# Замените на URL вашего API
API_BASE_URL = "http://89.111.169.47:8005"

# Ваш статический токен доступа
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYW5pa2JlbGF2aW4yMDA2QGdtYWlsLmNvbSIsImV4cCI6MjA3NTcwNTExNH0.JXxPMrye8Vigv684SmBMF6uqt6fxd9WHajwM3j8Jj8c"
# -------------------------

# Глобальные заголовки для всех запросов
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


# --- Вспомогательные функции ---

def cleanup_test_tables(table_names: List[str]):
    """Удаляет тестовые таблицы, чтобы каждый запуск был чистым."""
    print("\n--- Шаг 0: Очистка старых тестовых таблиц ---")
    try:
        response = requests.get(f"{API_BASE_URL}/api/meta/entity-types", headers=HEADERS)
        response.raise_for_status()  # Проверяем на ошибки HTTP

        existing_types = response.json()
        for et in existing_types:
            if et['name'] in table_names:
                print(f"Очистка: удаление старой таблицы '{et['name']}' (ID: {et['id']})")
                del_resp = requests.delete(f"{API_BASE_URL}/api/meta/entity-types/{et['id']}", headers=HEADERS)
                if del_resp.status_code == 204:
                    print(f"Таблица '{et['name']}' успешно удалена.")
                else:
                    print(f"Предупреждение: не удалось удалить таблицу '{et['name']}'. Статус: {del_resp.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка во время очистки: {e}")


def run_relation_test():
    """Основная функция, выполняющая все шаги теста."""

    company_table_name = "test_companies_relation"
    deal_table_name = "test_deals_relation"

    # Словарь для хранения ID всех созданных сущностей (таблиц, колонок)
    ids = {}

    # Очищаем таблицы перед началом и после завершения (даже если была ошибка)
    cleanup_test_tables([company_table_name, deal_table_name])

    try:
        # --- Шаг 1: Создание метаданных (таблиц и колонок) ---
        print("\n--- Шаг 1: Создание метаданных ---")

        # Создание таблицы "Компании"
        comp_resp = requests.post(
            f"{API_BASE_URL}/api/meta/entity-types", headers=HEADERS,
            json={"name": company_table_name, "display_name": "Тестовые Компании (Связи)"}
        )
        comp_resp.raise_for_status()
        ids["company_type_id"] = comp_resp.json()["id"]

        # Создание таблицы "Сделки"
        deal_resp = requests.post(
            f"{API_BASE_URL}/api/meta/entity-types", headers=HEADERS,
            json={"name": deal_table_name, "display_name": "Тестовые Сделки (Связи)"}
        )
        deal_resp.raise_for_status()
        ids["deal_type_id"] = deal_resp.json()["id"]

        # Создание колонок для Компаний
        attr_resp = requests.post(f"{API_BASE_URL}/api/meta/entity-types/{ids['company_type_id']}/attributes",
                                  headers=HEADERS,
                                  json={"name": "company_inn", "display_name": "ИНН", "value_type": "string"})
        attr_resp.raise_for_status();
        ids["company_inn_attr_id"] = attr_resp.json()["id"]

        attr_resp = requests.post(f"{API_BASE_URL}/api/meta/entity-types/{ids['company_type_id']}/attributes",
                                  headers=HEADERS,
                                  json={"name": "company_name", "display_name": "Название", "value_type": "string"})
        attr_resp.raise_for_status();
        ids["company_name_attr_id"] = attr_resp.json()["id"]

        # Создание колонок для Сделок
        attr_resp = requests.post(f"{API_BASE_URL}/api/meta/entity-types/{ids['deal_type_id']}/attributes",
                                  headers=HEADERS, json={"name": "client_inn_key", "display_name": "ИНН Клиента",
                                                         "value_type": "string"})
        attr_resp.raise_for_status();
        ids["client_inn_key_attr_id"] = attr_resp.json()["id"]

        attr_resp = requests.post(f"{API_BASE_URL}/api/meta/entity-types/{ids['deal_type_id']}/attributes",
                                  headers=HEADERS,
                                  json={"name": "client_name_lookup", "display_name": "Название Клиента",
                                        "value_type": "relation"})
        attr_resp.raise_for_status();
        ids["client_lookup_attr_id"] = attr_resp.json()["id"]

        print("✅ Метаданные успешно созданы.")

        # --- Шаг 2: Наполнение таблиц данными ---
        print("\n--- Шаг 2: Наполнение данными ---")
        requests.post(f"{API_BASE_URL}/api/data/{company_table_name}", headers=HEADERS,
                      json={"company_inn": "7707083893", "company_name": "ПАО СБЕРБАНК"}).raise_for_status()
        requests.post(f"{API_BASE_URL}/api/data/{company_table_name}", headers=HEADERS,
                      json={"company_inn": "7736207543", "company_name": "ООО Яндекс"}).raise_for_status()
        requests.post(f"{API_BASE_URL}/api/data/{deal_table_name}", headers=HEADERS,
                      json={"client_inn_key": "7707083893"}).raise_for_status()  # Сделка со Сбером
        requests.post(f"{API_BASE_URL}/api/data/{deal_table_name}", headers=HEADERS,
                      json={"client_inn_key": "9999999999"}).raise_for_status()  # Сделка с несуществующей компанией
        requests.post(f"{API_BASE_URL}/api/data/{deal_table_name}", headers=HEADERS,
                      json={"client_inn_key": "7736207543"}).raise_for_status()  # Сделка с Яндексом
        print("✅ Данные успешно загружены.")

        # --- Шаг 3: Настройка связи ---
        print("\n--- Шаг 3: Настройка связи ---")
        relation_payload = {
            "target_entity_type_id": ids["company_type_id"],  # Смотреть в таблицу "Компании"
            "source_attribute_id": ids["client_inn_key_attr_id"],  # Брать ключ из "ИНН Клиента" в Сделках
            "target_attribute_id": ids["company_inn_attr_id"],  # Искать совпадение в "ИНН" в Компаниях
            "display_attribute_id": ids["company_name_attr_id"]  # Отображать "Название" из Компаний
        }
        update_resp = requests.put(
            f"{API_BASE_URL}/api/meta/entity-types/{ids['deal_type_id']}/attributes/{ids['client_lookup_attr_id']}",
            headers=HEADERS, json=relation_payload
        )
        update_resp.raise_for_status()
        print("✅ Связь успешно настроена.")

        # --- Шаг 4: Проверка результата ---
        print("\n--- Шаг 4: Проверка результата ---")
        get_deals_resp = requests.get(f"{API_BASE_URL}/api/data/{deal_table_name}", headers=HEADERS)
        get_deals_resp.raise_for_status()

        deals_data = get_deals_resp.json()
        assert len(deals_data) == 3, "Ожидалось 3 сделки"

        deals_by_inn = {d["client_inn_key"]: d for d in deals_data}

        # Проверка 1: Сделка со Сбером
        sber_deal = deals_by_inn.get("7707083893")
        assert sber_deal is not None, "Сделка с ИНН Сбербанка не найдена!"
        assert sber_deal["client_name_lookup"] == "ПАО СБЕРБАНК", "Название Сбербанка не подтянулось"
        print("✓ Проверка 1 (Сбербанк): OK")

        # Проверка 2: Сделка с Яндексом
        yandex_deal = deals_by_inn.get("7736207543")
        assert yandex_deal is not None, "Сделка с ИНН Яндекса не найдена!"
        assert yandex_deal["client_name_lookup"] == "ООО Яндекс", "Название Яндекса не подтянулось"
        print("✓ Проверка 2 (Яндекс): OK")

        # Проверка 3: Сделка с несуществующим ИНН
        fake_deal = deals_by_inn.get("9999999999")
        assert fake_deal is not None, "Сделка с несуществующим ИНН не найдена!"
        assert fake_deal.get("client_name_lookup") is None, "Для несуществующего ИНН поле должно быть пустым (None)"
        print("✓ Проверка 3 (Несуществующий ИНН): OK")

        print("\n🎉🎉🎉 Тест функциональности связей успешно пройден! 🎉🎉🎉")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ ОШИБКА НА ШАГЕ: {e}")
        if e.response is not None:
            print(f"Статус ответа: {e.response.status_code}")
            print(f"Тело ответа: {e.response.text}")
    except AssertionError as e:
        print(f"\n❌ ПРОВЕРКА НЕ ПРОЙДЕНА: {e}")
    finally:
        # Вне зависимости от результата, пытаемся почистить за собой
        cleanup_test_tables([company_table_name, deal_table_name])


if __name__ == "__main__":
    run_relation_test()