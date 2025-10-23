import requests
import time
import sys
import json
from typing import Set

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Вспомогательные функции ---
test_failed = False


def print_status(ok, message):
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}\n"); test_failed = True


def print_header(title):
    print("\n" + "=" * 60);
    print(f" {title} ".center(60, "="));
    print("=" * 60)


def login():
    try:
        r = requests.post(f"{BASE_URL}/api/auth/token", data={'username': EMAIL, 'password': PASSWORD})
        r.raise_for_status()
        return {'Authorization': f'Bearer {r.json()["access_token"]}'}
    except Exception as e:
        print(f"Критическая ошибка при авторизации: {e}"); return None


def get_entity_details(headers, table_name, entity_id):
    """Вспомогательная функция для получения деталей одной записи."""
    resp = requests.get(f"{BASE_URL}/api/data/{table_name}/{entity_id}", headers=headers)
    resp.raise_for_status()
    return resp.json()


# --- Основная функция ---
def run_update_test():
    headers = login()
    if not headers: return

    ids = {}
    table_names = {}

    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("Шаг 1: Создание таблиц 'Проекты', 'Пользователи', 'Теги'")

        # Создаем таблицы
        table_names['projects'] = f"projects_upd_{int(time.time())}"
        table_names['users'] = f"users_upd_{int(time.time())}"
        table_names['tags'] = f"tags_upd_{int(time.time())}"

        for key, name in table_names.items():
            resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                                 json={"name": name, "display_name": f"Тест Обновления ({key.capitalize()})"})
            resp.raise_for_status();
            ids[f'{key}_table'] = resp.json()

        # Создаем базовые колонки
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes",
                             headers=headers,
                             json={"name": "project_name", "display_name": "Название проекта", "value_type": "string"});
        resp.raise_for_status();
        ids['project_name_attr'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['users_table']['id']}/attributes", headers=headers,
                             json={"name": "user_name", "display_name": "Имя пользователя", "value_type": "string"});
        resp.raise_for_status();
        ids['user_name_attr'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['tags_table']['id']}/attributes", headers=headers,
                             json={"name": "tag_name", "display_name": "Название тега", "value_type": "string"});
        resp.raise_for_status();
        ids['tag_name_attr'] = resp.json()

        # Создаем связи
        # 1. O2M: Проект <-> Пользователи
        payload_o2m = {"name": "lead_dev", "display_name": "Ведущий разработчик", "value_type": "relation",
                       "relation_type": "one-to-many", "target_entity_type_id": ids['users_table']['id'],
                       "create_back_relation": True}
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes", headers=headers,
                      json=payload_o2m).raise_for_status()
        # 2. M2M: Проект <-> Теги
        payload_m2m = {"name": "project_tags", "display_name": "Теги проекта", "value_type": "relation",
                       "relation_type": "many-to-many", "target_entity_type_id": ids['tags_table']['id'],
                       "create_back_relation": True}
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes", headers=headers,
                      json=payload_m2m).raise_for_status()

        # Создаем данные
        resp = requests.post(f"{BASE_URL}/api/data/{table_names['projects']}", headers=headers,
                             json={"project_name": "Проект 'Феникс'"});
        resp.raise_for_status();
        ids['project_phoenix'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{table_names['users']}", headers=headers,
                             json={"user_name": "Алиса"});
        resp.raise_for_status();
        ids['user_alice'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{table_names['tags']}", headers=headers,
                             json={"tag_name": "Срочно"});
        resp.raise_for_status();
        ids['tag_urgent'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{table_names['tags']}", headers=headers,
                             json={"tag_name": "Внутренний"});
        resp.raise_for_status();
        ids['tag_internal'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{table_names['tags']}", headers=headers,
                             json={"tag_name": "Для клиента"});
        resp.raise_for_status();
        ids['tag_client'] = resp.json()['data'][0]

        print_status(True, "Подготовительный этап завершен.")

        # --- ТЕСТ 1: ОБНОВЛЕНИЕ ПРОСТОГО ПОЛЯ ---
        print_header("Тест 1: Обновление простого текстового поля")
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"project_name": "Проект 'Феникс' (Обновлен)"}).raise_for_status()
        details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        print_status(details.get('project_name') == "Проект 'Феникс' (Обновлен)", "Название проекта успешно обновлено.")

        # --- ТЕСТ 2: УСТАНОВКА СВЯЗИ ONE-TO-MANY ---
        print_header("Тест 2: Установка связи 'Один-ко-многим'")
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"lead_dev": ids['user_alice']['id']}).raise_for_status()
        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        user_details = get_entity_details(headers, table_names['users'], ids['user_alice']['id'])
        print_status(project_details.get('lead_dev') == "Алиса",
                     "Прямая связь (Проект -> Пользователь) отображается корректно.")
        # Имя обратной связи генерируется автоматически
        back_relation_name = f"link_from_{table_names['projects']}"
        print_status(user_details.get(back_relation_name) == "Проект 'Феникс' (Обновлен)",
                     "Обратная связь (Пользователь -> Проект) отображается корректно.")

        # --- ТЕСТ 3: УСТАНОВКА СВЯЗИ MANY-TO-MANY ---
        print_header("Тест 3: Установка связи 'Многие-ко-многим'")
        tags_to_set = [ids['tag_urgent']['id'], ids['tag_internal']['id']]
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"project_tags": tags_to_set}).raise_for_status()
        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        tag_urgent_details = get_entity_details(headers, table_names['tags'], ids['tag_urgent']['id'])
        print_status(set(project_details.get('project_tags', [])) == {"Срочно", "Внутренний"},
                     "Прямая M2M связь (Проект -> Теги) отображается корректно.")
        back_relation_name_m2m = f"link_from_{table_names['projects']}"
        print_status("Проект 'Феникс' (Обновлен)" in tag_urgent_details.get(back_relation_name_m2m, []),
                     "Обратная M2M связь (Тег -> Проект) отображается корректно.")

        # --- ТЕСТ 4: ИЗМЕНЕНИЕ СВЯЗИ MANY-TO-MANY ---
        print_header("Тест 4: Изменение связи 'Многие-ко-многим'")
        new_tags = [ids['tag_internal']['id'], ids['tag_client']['id']]  # Убираем 'Срочно', добавляем 'Для клиента'
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"project_tags": new_tags}).raise_for_status()
        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        tag_urgent_details = get_entity_details(headers, table_names['tags'], ids['tag_urgent']['id'])
        tag_client_details = get_entity_details(headers, table_names['tags'], ids['tag_client']['id'])
        print_status(set(project_details.get('project_tags', [])) == {"Внутренний", "Для клиента"},
                     "Проект корректно обновил список тегов.")
        print_status("Проект 'Феникс' (Обновлен)" not in tag_urgent_details.get(back_relation_name_m2m, []),
                     "Старая обратная связь (с тегом 'Срочно') была удалена.")
        print_status("Проект 'Феникс' (Обновлен)" in tag_client_details.get(back_relation_name_m2m, []),
                     "Новая обратная связь (с тегом 'Для клиента') была создана.")

        # --- ТЕСТ 5: ОЧИСТКА СВЯЗЕЙ ---
        print_header("Тест 5: Очистка (разрыв) связей")
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"lead_dev": None, "project_tags": []}).raise_for_status()
        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        user_details = get_entity_details(headers, table_names['users'], ids['user_alice']['id'])
        tag_internal_details = get_entity_details(headers, table_names['tags'], ids['tag_internal']['id'])
        print_status(project_details.get('lead_dev') is None, "Связь O2M успешно очищена.")
        print_status(project_details.get('project_tags') == [], "Связь M2M успешно очищена.")
        print_status(user_details.get(back_relation_name) is None, "Обратная связь O2M успешно очищена.")
        print_status("Проект 'Феникс' (Обновлен)" not in tag_internal_details.get(back_relation_name_m2m, []),
                     "Обратная связь M2M успешно очищена.")

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    finally:
        # --- ОЧИСТКА ---
        print_header("Очистка (удаление тестовых таблиц)")
        for key, table_info in ids.items():
            if key.endswith('_table'):
                requests.delete(f"{BASE_URL}/api/meta/entity-types/{table_info['id']}", headers=headers)
                print(f" -> Таблица '{table_info['display_name']}' удалена.")

        if not test_failed:
            print("\n" + "🎉" * 20 + "\n Все тесты метода update_entity успешно пройдены! \n" + "🎉" * 20)
        else:
            sys.exit(1)


if __name__ == "__main__":
    run_update_test()