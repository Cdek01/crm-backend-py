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
    email = f"AntonShlips12@example.com"
    password = "AntonShlips12(1985)"
    reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def create_table_with_attrs(headers, config):
    """Создает таблицу и ее атрибуты, возвращает ID таблицы и словарь атрибутов."""
    table_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                               json={"name": config['name'], "display_name": config['display_name']}).json()
    table_id = table_resp['id']

    attrs_map = {}
    for attr_payload in config['attributes']:
        url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
        attr_resp = requests.post(url, headers=headers, json=attr_payload).json()
        attrs_map[attr_resp['name']] = attr_resp

    return table_id, attrs_map


# --- ОСНОВНОЙ ТЕСТ ---
def run_lookup_test():
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦ")
        headers = register_and_login()

        # 1.1 Создаем таблицу-ИСТОЧНИК "Справочник компаний"
        companies_config = {
            "name": f"companies_{int(time.time())}",
            "display_name": "Справочник компаний",
            "attributes": [
                {"name": "inn", "display_name": "ИНН", "value_type": "string"},
                {"name": "legal_name", "display_name": "Юридическое название", "value_type": "string"},
            ]
        }
        companies_table_id, companies_attrs = create_table_with_attrs(headers, companies_config)
        print(f" -> Создана таблица-источник '{companies_config['name']}' (ID: {companies_table_id})")

        # 1.2 Наполняем ее данными
        requests.post(f"{BASE_URL}/api/data/{companies_config['name']}", headers=headers,
                      json={"inn": "7707083893", "legal_name": "СБЕРБАНК"}).raise_for_status()
        requests.post(f"{BASE_URL}/api/data/{companies_config['name']}", headers=headers,
                      json={"inn": "7728168971", "legal_name": "ГАЗПРОМ"}).raise_for_status()
        print(" -> Таблица-источник наполнена данными.")

        # 1.3 Создаем таблицу-ПРИЕМНИК "Сделки" со связанной колонкой
        deals_config = {
            "name": f"deals_{int(time.time())}",
            "display_name": "Сделки",
            "attributes": [
                {"name": "deal_title", "display_name": "Название сделки", "value_type": "string"},
                {"name": "client_inn", "display_name": "ИНН клиента", "value_type": "string"},
                {
                    "name": "client_name_lookup",
                    # --- ДОБАВЬТЕ ЭТУ СТРОКУ ---
                    "display_name": "Название клиента (из справочника)",
                    # ---------------------------
                    "value_type": "relation",
                    "target_entity_type_id": companies_table_id,
                    "source_attribute_id": None, # Это нормально, мы обновим его позже
                    "target_attribute_id": companies_attrs['inn']['id'],
                    "display_attribute_id": companies_attrs['legal_name']['id'],
                }
            ]
        }
        deals_table_id, deals_attrs = create_table_with_attrs(headers, deals_config)

        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Теперь, когда у нас есть ID всех колонок, мы ОБНОВЛЯЕМ связанную колонку,
        # чтобы установить ей правильный `source_attribute_id`.
        lookup_attr_id = deals_attrs['client_name_lookup']['id']
        source_attr_id = deals_attrs['client_inn']['id']

        update_payload = {"source_attribute_id": source_attr_id}
        update_url = f"{BASE_URL}/api/meta/entity-types/{deals_table_id}/attributes/{lookup_attr_id}"
        requests.put(update_url, headers=headers, json=update_payload).raise_for_status()
        # ---------------------------

        print(f" -> Создана и настроена таблица-приемник '{deals_config['name']}'.")

        # --- ШАГ 2: СОЗДАНИЕ ДАННЫХ В ПРИЕМНИКЕ ---
        print_header("ШАГ 2: СОЗДАНИЕ СДЕЛКИ С УКАЗАНИЕМ ИНН")

        deal_payload = {"deal_title": "Продажа ПО", "client_inn": "7707083893"}
        # `client_name_lookup` не передаем, он должен вычислиться сам
        requests.post(f"{BASE_URL}/api/data/{deals_config['name']}", headers=headers,
                      json=deal_payload).raise_for_status()
        print_status(True, "Тестовая сделка для 'СБЕРБАНК' создана.")

        # --- ШАГ 3: ФИНАЛЬНАЯ ПРОВЕРКА ---
        print_header("ШАГ 3: ПРОВЕРКА, ЧТО СВЯЗАННОЕ ПОЛЕ ЗАПОЛНИЛОСЬ")

        # Запрашиваем список всех сделок
        all_deals = requests.get(f"{BASE_URL}/api/data/{deals_config['name']}", headers=headers).json()

        print_status(len(all_deals) > 0, "Получен непустой список сделок.")

        created_deal = all_deals[0]
        print(f" -> Полученные данные для сделки: {json.dumps(created_deal, indent=2, ensure_ascii=False)}")

        # Проверяем, что исходное поле на месте
        print_status(created_deal.get('client_inn') == "7707083893", "Исходный ключ 'client_inn' на месте.")

        # Главная проверка
        print_status(
            created_deal.get('client_name_lookup') == "СБЕРБАНК",
            f"Связанное поле 'client_name_lookup' корректно заполнено значением 'СБЕРБАНК'."
        )

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ТЕСТ СВЯЗАННЫХ ПОЛЕЙ (LOOK UP) ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


# ... (вставьте сюда `register_and_login`, `print_status`, `print_header`)

if __name__ == "__main__":
    run_lookup_test()