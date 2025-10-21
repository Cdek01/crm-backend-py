import requests
import time
import sys
import json

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"


# -----------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        # В случае провала выводим пустую строку для лучшей читаемости и выходим
        print("")
        sys.exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login():
    try:
        auth_payload = {'username': EMAIL, 'password': PASSWORD}
        token_resp = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_resp.raise_for_status()
        return {'Authorization': f'Bearer {token_resp.json()["access_token"]}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}")
        return None


# --- Основная функция демонстрации ---
def run_full_cycle_test():
    headers = login()
    if not headers: return

    ids = {}

    try:
        # --- ШАГ 1: ПОДГОТОВКА СТРУКТУРЫ ---
        print_header("Шаг 1: Создание таблиц 'Проекты' и 'Задачи'")

        # Создаем таблицы
        projects_name = f"projects_full_{int(time.time())}"
        tasks_name = f"tasks_full_{int(time.time())}"
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": projects_name, "display_name": "Проекты (Full Cycle)"})
        resp.raise_for_status();
        ids['projects_table'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": tasks_name, "display_name": "Задачи (Full Cycle)"})
        resp.raise_for_status();
        ids['tasks_table'] = resp.json()

        # Создаем базовые колонки для названий
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes",
                             headers=headers,
                             json={"name": "project_name", "display_name": "Название проекта", "value_type": "string"})
        resp.raise_for_status();
        ids['project_name_attr'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['tasks_table']['id']}/attributes", headers=headers,
                             json={"name": "task_title", "display_name": "Название задачи", "value_type": "string"})
        resp.raise_for_status();
        ids['task_title_attr'] = resp.json()
        print_status(True, "Подготовительный этап завершен.")

        # --- ШАГ 2: СОЗДАНИЕ ДВУСТОРОННЕЙ СВЯЗИ ---
        print_header("Шаг 2: Создание двусторонней связи одним запросом")

        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        payload = {
            "name": "tasks_in_project", "display_name": "Задачи в проекте", "value_type": "relation",

            # Настройки прямой связи (Проект -> Задача)
            "target_entity_type_id": ids['tasks_table']['id'],
            "display_attribute_id": ids['task_title_attr']['id'],  # Показываем "Название задачи"

            "create_back_relation": True,

            # Настройки обратной связи (Задача -> Проект)
            "back_relation_name": "parent_project",
            "back_relation_display_name": "Родительский проект",
            # Явно указываем, что в обратной связи нужно показывать "Название проекта"
            "back_relation_display_attribute_id": ids['project_name_attr']['id']
        }
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---

        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}/attributes",
                             headers=headers, json=payload)
        resp.raise_for_status()
        ids['tasks_in_project_attr'] = resp.json()
        print_status(resp.status_code == 201, "Запрос на создание связи успешно выполнен.")

        # --- ШАГ 3: НАПОЛНЕНИЕ ДАННЫМИ ---
        print_header("Шаг 3: Наполнение таблиц данными")
        resp = requests.post(f"{BASE_URL}/api/data/{projects_name}", headers=headers,
                             json={"project_name": "Проект 'Альфа'"})
        resp.raise_for_status();
        ids['project_a_data'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{tasks_name}", headers=headers,
                             json={"task_title": "Задача №1 для Альфы"})
        resp.raise_for_status();
        ids['task_1_data'] = resp.json()['data'][0]
        print_status(True, "Созданы 'Проект Альфа' и 'Задача №1'.")

        # --- ШАГ 4: УСТАНОВКА СВЯЗИ МЕЖДУ ДАННЫМИ ---
        print_header("Шаг 4: Установка связи между 'Задачей №1' и 'Проектом Альфа'")
        # Обновляем Задачу, указывая в поле 'parent_project' ID 'Проекта Альфа'
        link_payload = {"parent_project": ids['project_a_data']['id']}
        update_url = f"{BASE_URL}/api/data/{tasks_name}/{ids['task_1_data']['id']}"
        resp = requests.put(update_url, headers=headers, json=link_payload)
        resp.raise_for_status()
        print_status(resp.status_code == 200, "Связь успешно установлена (PUT-запрос прошел).")

        # --- ШАГ 5: ФИНАЛЬНАЯ ПРОВЕРКА ОТОБРАЖЕНИЯ ---
        print_header("Шаг 5: Проверка отображения связи с обеих сторон")

        # Проверка 1: Смотрим на Задачу, ожидаем увидеть название Проекта
        resp = requests.get(f"{BASE_URL}/api/data/{tasks_name}/{ids['task_1_data']['id']}", headers=headers)
        task_details = resp.json()
        print(f" -> Данные Задачи: {task_details}")
        displayed_project_name = task_details.get('parent_project')
        expected_project_name = ids['project_a_data']['project_name']
        print_status(
            displayed_project_name == expected_project_name,
            f"В Задаче №1 корректно отображается название проекта: '{displayed_project_name}'"
        )

        # Проверка 2: Смотрим на Проект, ожидаем увидеть название Задачи
        # Важно: текущая реализация 1-ко-многим может показывать только одну запись.
        # Мы проверяем, что хотя бы одна связь отображается.
        resp = requests.get(f"{BASE_URL}/api/data/{projects_name}/{ids['project_a_data']['id']}", headers=headers)
        project_details = resp.json()
        print(f" -> Данные Проекта: {project_details}")
        displayed_task_name = project_details.get('tasks_in_project')
        expected_task_name = ids['task_1_data']['task_title']
        print_status(
            displayed_task_name == expected_task_name,
            f"В Проекте 'Альфа' корректно отображается название задачи: '{displayed_task_name}'"
        )

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    finally:
        # --- ШАГ 6: ОЧИСТКА ---
        print_header("Шаг 6: Очистка (удаление тестовых таблиц)")
        if 'projects_table' in ids:
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['projects_table']['id']}", headers=headers)
            print(f" -> Таблица '{ids['projects_table']['display_name']}' удалена.")
        if 'tasks_table' in ids:
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['tasks_table']['id']}", headers=headers)
            print(f" -> Таблица '{ids['tasks_table']['display_name']}' удалена.")
        print_status(True, "Очистка завершена.")


if __name__ == "__main__":
    run_full_cycle_test()