import requests
import time
import sys
import json
from typing import Set, Optional
import requests
import time
import sys
import json
from typing import Set, List, Dict, Any
# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Вспомогательные функции ---
test_failed = False


def print_status(ok: bool, message: str):
    """Выводит статус теста и устанавливает флаг ошибки."""
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}\n")
        test_failed = True


def print_header(title: str):
    """Выводит красивый заголовок для каждого тестового блока."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login() -> Optional[Dict[str, str]]:
    """Аутентифицируется и возвращает заголовки для последующих запросов."""
    try:
        url = f"{BASE_URL}/api/auth/token"
        print(f"-> Попытка авторизации: POST {url}")
        r = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})
        r.raise_for_status()
        return {'Authorization': f'Bearer {r.json()["access_token"]}'}
    except Exception as e:
        print(f"Критическая ошибка при авторизации: {e}")
        return None


def get_entity_details(headers: Dict, table_name: str, entity_id: int) -> Dict[str, Any]:
    """Вспомогательная функция для получения деталей одной записи."""
    resp = requests.get(f"{BASE_URL}/api/data/{table_name}/{entity_id}", headers=headers)
    resp.raise_for_status()
    return resp.json()


def get_entity_type_schema(headers: Dict, table_id: int) -> Dict[str, Any]:
    """Получает актуальную схему таблицы со всеми атрибутами."""
    resp = requests.get(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers)
    resp.raise_for_status()
    return resp.json()


# --- Основная функция ---
def run_update_test():
    global test_failed
    headers = login()
    if not headers:
        sys.exit(1)

    ids = {}
    table_names = {}

    # Используем уникальные имена таблиц, чтобы тесты можно было запускать многократно
    timestamp = int(time.time())
    table_names['projects'] = f"projects_upd_{timestamp}"
    table_names['users'] = f"users_upd_{timestamp}"
    table_names['tags'] = f"tags_upd_{timestamp}"

    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("Шаг 1: Создание таблиц, атрибутов и связей")

        # Создание таблиц
        for key, name in table_names.items():
            resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                                 json={"name": name, "display_name": f"Тест Обновления ({key.capitalize()})"})
            resp.raise_for_status()
            ids[f'{key}_table'] = resp.json()

        # Создание базовых атрибутов (колонок 'name')
        for key in table_names:
            resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids[f'{key}_table']['id']}/attributes",
                                 headers=headers,
                                 json={"name": f"{key}_name", "display_name": f"Название ({key})",
                                       "value_type": "string"})
            resp.raise_for_status()
            ids[f'{key}_name_attr'] = resp.json()

        # --- ИСПРАВЛЕНИЕ: Создаем связи с правильными параметрами ---
        print("\nСоздание связей...")
        # Связь Проект -> Пользователь (Один-к-Одному, симметричная)
        payload_1_to_1 = {
            "name": "lead_dev", "display_name": "Ведущий разработчик", "value_type": "relation",
            "target_entity_type_id": ids['users_table']['id'],
            "display_attribute_id": ids['users_name_attr']['id'],
            "allow_multiple": False,  # <-- Один-к-Одному
            "is_symmetrical": True,
            "back_relation_name": "user_project",  # <-- Задаем имя обратной связи
            "back_relation_display_name": "Проект пользователя",
            "back_relation_display_attribute_id": ids['projects_name_attr']['id'],
            "back_relation_allow_multiple": False
        }
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes", headers=headers,
                      json=payload_1_to_1).raise_for_status()

        # Связь Проект -> Теги (Многие-ко-Многим, симметричная)
        payload_m_to_m = {
            "name": "project_tags", "display_name": "Теги проекта", "value_type": "relation",
            "target_entity_type_id": ids['tags_table']['id'],
            "display_attribute_id": ids['tags_name_attr']['id'],
            "allow_multiple": True,  # <-- Многие-ко-Многим
            "is_symmetrical": True,
            "back_relation_name": "tag_projects",  # <-- Задаем имя обратной связи
            "back_relation_display_name": "Проекты с тегом",
            "back_relation_display_attribute_id": ids['projects_name_attr']['id'],
            "back_relation_allow_multiple": True
        }
        requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes", headers=headers,
                      json=payload_m_to_m).raise_for_status()

        # Создаем данные
        print("\nСоздание тестовых записей...")
        ids['project_phoenix'] = requests.post(f"{BASE_URL}/api/data/{table_names['projects']}", headers=headers,
                                               json={"projects_name": "Проект 'Феникс'"}).json()['data'][0]
        ids['user_alice'] = requests.post(f"{BASE_URL}/api/data/{table_names['users']}", headers=headers,
                                          json={"users_name": "Алиса"}).json()['data'][0]
        ids['tag_urgent'] = requests.post(f"{BASE_URL}/api/data/{table_names['tags']}", headers=headers,
                                          json={"tags_name": "Срочно"}).json()['data'][0]
        ids['tag_internal'] = requests.post(f"{BASE_URL}/api/data/{table_names['tags']}", headers=headers,
                                            json={"tags_name": "Внутренний"}).json()['data'][0]
        ids['tag_client'] = requests.post(f"{BASE_URL}/api/data/{table_names['tags']}", headers=headers,
                                          json={"tags_name": "Для клиента"}).json()['data'][0]
        print_status(True, "Подготовительный этап завершен.")

        # --- ТЕСТ 1: ОБНОВЛЕНИЕ ПРОСТОГО ПОЛЯ ---
        print_header("Тест 1: Обновление простого текстового поля")
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"projects_name": "Проект 'Феникс' (Обновлен)"}).raise_for_status()
        details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        print_status(details.get('projects_name') == "Проект 'Феникс' (Обновлен)",
                     "Название проекта успешно обновлено.")

        # --- ТЕСТ 2: УСТАНОВКА СВЯЗИ ОДИН-К-ОДНОМУ ---
        print_header("Тест 2: Установка связи 'Один-к-Одному'")
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"lead_dev": ids['user_alice']['id']}).raise_for_status()

        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        user_details = get_entity_details(headers, table_names['users'], ids['user_alice']['id'])

        # ИСПРАВЛЕНИЕ: Проверяем формат [{id, display_value}]
        lead_dev_data = project_details.get('lead_dev', [])
        is_direct_link_ok = len(lead_dev_data) == 1 and lead_dev_data[0]['id'] == ids['user_alice']['id'] and \
                            lead_dev_data[0]['display_value'] == "Алиса"
        print_status(is_direct_link_ok, "Прямая связь (Проект -> Пользователь) установлена корректно.")

        user_project_data = user_details.get('user_project', [])
        is_back_link_ok = len(user_project_data) == 1 and user_project_data[0]['id'] == ids['project_phoenix']['id'] and \
                          user_project_data[0]['display_value'] == "Проект 'Феникс' (Обновлен)"
        print_status(is_back_link_ok, "Обратная связь (Пользователь -> Проект) создана автоматически.")

        # --- ТЕСТ 3: УСТАНОВКА СВЯЗИ MANY-TO-MANY ---
        print_header("Тест 3: Установка связи 'Многие-ко-многим'")
        tags_to_set = [ids['tag_urgent']['id'], ids['tag_internal']['id']]
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"project_tags": tags_to_set}).raise_for_status()

        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        tag_urgent_details = get_entity_details(headers, table_names['tags'], ids['tag_urgent']['id'])

        # ИСПРАВЛЕНИЕ: Проверяем формат [{id, display_value}]
        project_tags_data = project_details.get('project_tags', [])
        project_tags_values = {tag['display_value'] for tag in project_tags_data}
        print_status(project_tags_values == {"Срочно", "Внутренний"},
                     "Прямая M2M связь (Проект -> Теги) установлена корректно.")

        tag_projects_data = tag_urgent_details.get('tag_projects', [])
        tag_projects_values = {p['display_value'] for p in tag_projects_data}
        print_status("Проект 'Феникс' (Обновлен)" in tag_projects_values,
                     "Обратная M2M связь (Тег -> Проект) создана автоматически.")

        # --- ТЕСТ 4: ИЗМЕНЕНИЕ СВЯЗИ MANY-TO-MANY ---
        print_header("Тест 4: Изменение связи 'Многие-ко-многим'")
        new_tags = [ids['tag_internal']['id'], ids['tag_client']['id']]
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"project_tags": new_tags}).raise_for_status()

        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        tag_urgent_details_after = get_entity_details(headers, table_names['tags'], ids['tag_urgent']['id'])
        tag_client_details = get_entity_details(headers, table_names['tags'], ids['tag_client']['id'])

        project_tags_values = {tag['display_value'] for tag in project_details.get('project_tags', [])}
        print_status(project_tags_values == {"Внутренний", "Для клиента"}, "Проект корректно обновил список тегов.")

        urgent_projects_values = {p['display_value'] for p in tag_urgent_details_after.get('tag_projects', [])}
        print_status("Проект 'Феникс' (Обновлен)" not in urgent_projects_values,
                     "Старая обратная связь (с тегом 'Срочно') была удалена.")

        client_projects_values = {p['display_value'] for p in tag_client_details.get('tag_projects', [])}
        print_status("Проект 'Феникс' (Обновлен)" in client_projects_values,
                     "Новая обратная связь (с тегом 'Для клиента') была создана.")

        # --- ТЕСТ 5: ОЧИСТКА СВЯЗЕЙ ---
        print_header("Тест 5: Очистка (разрыв) связей")
        requests.put(f"{BASE_URL}/api/data/{table_names['projects']}/{ids['project_phoenix']['id']}", headers=headers,
                     json={"lead_dev": None, "project_tags": []}).raise_for_status()

        project_details = get_entity_details(headers, table_names['projects'], ids['project_phoenix']['id'])
        user_details = get_entity_details(headers, table_names['users'], ids['user_alice']['id'])
        tag_internal_details = get_entity_details(headers, table_names['tags'], ids['tag_internal']['id'])

        print_status(project_details.get('lead_dev') == [], "Связь 1-к-1 успешно очищена (результат: пустой массив).")
        print_status(project_details.get('project_tags') == [], "Связь M2M успешно очищена (результат: пустой массив).")
        print_status(user_details.get('user_project') == [], "Обратная связь 1-к-1 успешно очищена.")
        internal_projects_values = {p['display_value'] for p in tag_internal_details.get('tag_projects', [])}
        print_status("Проект 'Феникс' (Обновлен)" not in internal_projects_values,
                     "Обратная связь M2M успешно очищена.")

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        import traceback
        print_status(False, f"Произошла непредвиденная ошибка: {e}\n{traceback.format_exc()}")
    finally:
        # --- ОЧИСТКА ---
        print_header("Очистка (удаление тестовых таблиц)")
        for key, table_info in ids.items():
            if key.endswith('_table'):
                # Проверяем, что table_info - это словарь с ключом 'id'
                if isinstance(table_info, dict) and 'id' in table_info:
                    requests.delete(f"{BASE_URL}/api/meta/entity-types/{table_info['id']}", headers=headers)
                    print(f" -> Таблица '{table_info.get('display_name', 'N/A')}' удалена.")

        if not test_failed:
            print("\n" + "🎉" * 20 + "\n Все тесты успешно пройдены! \n" + "🎉" * 20)
        else:
            print("\n" + "❗️" * 20 + "\n Некоторые тесты провалились. \n" + "❗️" * 20)
            sys.exit(1)


if __name__ == "__main__":
    run_update_test()