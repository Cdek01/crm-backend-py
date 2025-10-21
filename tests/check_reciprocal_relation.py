import requests
import time
import sys

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
BASE_URL = "http://89.111.169.47:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
EMAIL = "1@example.com"
PASSWORD = "string"


# ---------------------------------------------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        sys.exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login():
    """Аутентифицируется и возвращает заголовки для авторизации."""
    try:
        auth_payload = {'username': EMAIL, 'password': PASSWORD}
        token_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_response.raise_for_status()
        token = token_response.json()['access_token']
        return {'Authorization': f'Bearer {token}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}")
        return None


# --- Основная функция демонстрации ---
def run_reciprocal_relation_demo():
    headers = login()
    if not headers: return

    # Словарь для хранения всех созданных ID
    ids = {}

    try:
        # --- ШАГ 1: Подготовка - Создание двух таблиц и базовых колонок ---
        print_header("Шаг 1: Создание таблиц 'Проекты' и 'Задачи'")

        # Создаем таблицу "Проекты"
        projects_table_name = f"projects_demo_{int(time.time())}"
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": projects_table_name, "display_name": "Демо Проекты"})
        resp.raise_for_status();
        ids['projects_table'] = resp.json()

        # Создаем таблицу "Задачи"
        tasks_table_name = f"tasks_demo_{int(time.time())}"
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": tasks_table_name, "display_name": "Демо Задачи"})
        resp.raise_for_status();
        ids['tasks_table'] = resp.json()

        # Добавляем колонку "Название проекта" в "Проекты"
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes",
                             headers=headers,
                             json={"name": "project_name", "display_name": "Название проекта", "value_type": "string"})
        resp.raise_for_status();
        ids['project_name_attr'] = resp.json()

        # Добавляем колонку "Название задачи" в "Задачи"
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['tasks_table']['id']}/attributes", headers=headers,
                             json={"name": "task_title", "display_name": "Название задачи", "value_type": "string"})
        resp.raise_for_status();
        ids['task_title_attr'] = resp.json()

        print_status(True, "Таблицы и базовые колонки успешно созданы.")

        # --- ШАГ 2: Основное действие - Создание двусторонней связи ---
        print_header("Шаг 2: Отправка запроса на создание двусторонней связи")

        # Мы "находимся" в таблице "Проекты" и создаем колонку "Задачи",
        # которая будет ссылаться на таблицу "Задачи"
        payload = {
            "name": "tasks_in_project",
            "display_name": "Задачи в проекте",
            "value_type": "relation",

            "target_entity_type_id": ids['tasks_table']['id'],
            "display_attribute_id": ids['task_title_attr']['id'],

            "create_back_relation": True,

            "back_relation_name": "parent_project",
            "back_relation_display_name": "Родительский проект"
        }

        print(" -> Отправляем POST-запрос с флагом 'create_back_relation: true'...")
        create_relation_url = f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes"
        resp = requests.post(create_relation_url, headers=headers, json=payload)
        resp.raise_for_status()

        print_status(resp.status_code == 201, "Запрос на создание связи успешно выполнен.")

        # --- ШАГ 3: Проверка результата ---
        print_header("Шаг 3: Проверка созданных колонок в обеих таблицах")

        # Проверка 1: колонка в исходной таблице "Проекты"
        resp = requests.get(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}", headers=headers)
        projects_details = resp.json()

        main_relation_attr = next(
            (attr for attr in projects_details['attributes'] if attr['name'] == 'tasks_in_project'), None)
        print_status(main_relation_attr is not None, "В таблице 'Проекты' найдена новая колонка 'Задачи в проекте'.")
        print_status(
            main_relation_attr['target_entity_type_id'] == ids['tasks_table']['id'],
            " -> Колонка 'Задачи в проекте' правильно ссылается на таблицу 'Задачи'."
        )

        # Проверка 2: АВТОМАТИЧЕСКИ созданная колонка в целевой таблице "Задачи"
        resp = requests.get(f"{BASE_URL}/api/meta/entity-types/{ids['tasks_table']['id']}", headers=headers)
        tasks_details = resp.json()

        back_relation_attr = next((attr for attr in tasks_details['attributes'] if attr['name'] == 'parent_project'),
                                  None)
        print_status(back_relation_attr is not None,
                     "В таблице 'Задачи' АВТОМАТИЧЕСКИ создана обратная колонка 'Родительский проект'.")
        print_status(
            back_relation_attr['target_entity_type_id'] == ids['projects_table']['id'],
            " -> Обратная колонка правильно ссылается обратно на таблицу 'Проекты'."
        )

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    # finally:
    #     # --- ШАГ 4: Очистка ---
    #     print_header("Шаг 4: Очистка (удаление тестовых таблиц)")
    #     if 'projects_table' in ids:
    #         requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}", headers=headers)
    #         print(f" -> Таблица '{ids['projects_table']['display_name']}' удалена.")
    #     if 'tasks_table' in ids:
    #         requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['tasks_table']['id']}", headers=headers)
    #         print(f" -> Таблица '{ids['tasks_table']['display_name']}' удалена.")
    #     print_status(True, "Очистка завершена.")


if __name__ == "__main__":
    run_reciprocal_relation_demo()