import requests
import time
import sys
import json
from typing import Set, List, Dict, Any, Optional

# --- НАСТРОЙКИ ---
# Замените на ваш URL, email и пароль
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Глобальные переменные для теста ---
test_failed = False
# Уникальные имена для тестовых таблиц, чтобы избежать конфликтов
PROJECT_TABLE_NAME = f"projects_test_{int(time.time())}"
TASK_TABLE_NAME = f"tasks_test_{int(time.time())}"


# --- Вспомогательные функции ---

def pretty_print_request(method: str, url: str, headers: Optional[Dict] = None, payload: Optional[Any] = None):
    """Красиво выводит в консоль информацию об исходящем запросе."""
    print("-" * 30)
    print(f"REQUEST -> {method} {url}")
    if headers:
        # Не выводим полный токен, чтобы не засорять лог
        print(f"  Headers: {{'Authorization': 'Bearer ...'}}")
    if payload:
        try:
            print(f"  Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        except (TypeError, json.JSONDecodeError):
            print(f"  Payload: {payload}")
    print("-" * 30)


def pretty_print_response(response: requests.Response):
    """Красиво выводит в консоль информацию о полученном ответе."""
    print(f"RESPONSE <- {response.status_code} {response.reason}")
    try:
        if response.text:  # Проверяем, есть ли тело у ответа
            print(f"  Body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except (TypeError, json.JSONDecodeError):
        print(f"  Body (raw): {response.text[:500]}...")  # Обрезаем на случай большого ответа
    print("-" * 30)


def print_status(ok: bool, message: str, data: Optional[Any] = None):
    """Выводит статус теста и устанавливает флаг ошибки."""
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                print(f"  └─ Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except (TypeError, json.JSONDecodeError):
                print(f"  └─ Ответ сервера: {data}")
        print("")
        test_failed = True


def print_header(title: str):
    """Выводит красивый заголовок для каждого тестового блока."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def login() -> Optional[Dict[str, str]]:
    """Аутентифицируется и возвращает заголовки для последующих запросов."""
    try:
        url = f"{BASE_URL}/api/auth/token"
        payload = {'username': EMAIL, 'password': PASSWORD}
        pretty_print_request("POST", url, payload=payload)
        r = requests.post(url, data=payload)
        pretty_print_response(r)
        r.raise_for_status()
        print_status(True, "Авторизация прошла успешно")
        return {'Authorization': f'Bearer {r.json()["access_token"]}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}", getattr(e, 'response', 'N/A'))
        return None


# --- Основные функции теста ---

def create_tables(headers: Dict[str, str]) -> Optional[Dict[str, int]]:
    """Создает тестовые таблицы 'Проекты' и 'Задачи' и колонку-связь между ними."""
    table_ids = {}
    try:
        # 1. Создание таблицы "Проекты"
        url_create_table = f"{BASE_URL}/api/meta/entity-types"
        project_payload = {"name": PROJECT_TABLE_NAME, "display_name": "Тестовые Проекты"}
        pretty_print_request("POST", url_create_table, headers, project_payload)
        r_project = requests.post(url_create_table, headers=headers, json=project_payload)
        pretty_print_response(r_project)
        r_project.raise_for_status()
        project_data = r_project.json()
        table_ids["project_id"] = project_data["id"]
        print_status(True, f"Таблица '{PROJECT_TABLE_NAME}' создана, ID: {table_ids['project_id']}")

        # <-- ИЗМЕНЕНИЕ 1: Создаем в "Проектах" колонку 'name'
        url_add_attr = f"{BASE_URL}/api/meta/entity-types/{table_ids['project_id']}/attributes"
        project_name_payload = {"name": "name", "display_name": "Название проекта", "value_type": "string"}
        pretty_print_request("POST", url_add_attr, headers, project_name_payload)
        r_proj_attr = requests.post(url_add_attr, headers=headers, json=project_name_payload)
        pretty_print_response(r_proj_attr)
        r_proj_attr.raise_for_status()
        print_status(True, "Колонка 'name' добавлена в таблицу 'Проекты'")

        # 2. Создание таблицы "Задачи"
        task_payload = {"name": TASK_TABLE_NAME, "display_name": "Тестовые Задачи"}
        pretty_print_request("POST", url_create_table, headers, task_payload)
        r_task = requests.post(url_create_table, headers=headers, json=task_payload)
        pretty_print_response(r_task)
        r_task.raise_for_status()
        task_data = r_task.json()
        table_ids["task_id"] = task_data["id"]
        print_status(True, f"Таблица '{TASK_TABLE_NAME}' создана, ID: {table_ids['task_id']}")

        # <-- ИЗМЕНЕНИЕ 2: Создаем в "Задачах" колонку 'name'
        url_add_attr = f"{BASE_URL}/api/meta/entity-types/{table_ids['task_id']}/attributes"
        task_name_payload = {"name": "name", "display_name": "Название задачи", "value_type": "string"}
        pretty_print_request("POST", url_add_attr, headers, task_name_payload)
        r_task_attr = requests.post(url_add_attr, headers=headers, json=task_name_payload)
        pretty_print_response(r_task_attr)
        r_task_attr.raise_for_status()
        print_status(True, "Колонка 'name' добавлена в таблицу 'Задачи'")

        # 3. Создание колонки-связи
        url_link = f"{BASE_URL}/api/meta/entity-types/{table_ids['task_id']}/attributes"
        link_payload = {
            "name": "linked_projects", "display_name": "Связанные проекты", "value_type": "relation",
            "allow_multiple_selection": True, "target_entity_type_id": table_ids["project_id"],
            "create_back_relation": True, "back_relation_name": "linked_tasks",
            "back_relation_display_name": "Связанные задачи"
        }
        pretty_print_request("POST", url_link, headers, link_payload)
        r_link = requests.post(url_link, headers=headers, json=link_payload)
        pretty_print_response(r_link)
        r_link.raise_for_status()
        print_status(True, "Колонка-связь 'многие-ко-многим' успешно создана")
        # --- НОВЫЙ БЛОК ПРОВЕРКИ ---
        print("\n-> Проверяем метаданные обратной связи...")
        time.sleep(1)  # Небольшая пауза, чтобы сервер успел все обработать
        url_get_project_table = f"{BASE_URL}/api/meta/entity-types/{table_ids['project_id']}"
        r_check = requests.get(url_get_project_table, headers=headers)
        project_meta = r_check.json()

        back_relation_attr = next((attr for attr in project_meta['attributes'] if attr['name'] == 'linked_tasks'), None)

        if back_relation_attr:
            display_attr_id = back_relation_attr.get('display_attribute_id')
            # Находим, какой колонке соответствует этот ID в таблице Задач
            url_get_task_table = f"{BASE_URL}/api/meta/entity-types/{table_ids['task_id']}"
            r_task_meta = requests.get(url_get_task_table, headers=headers)
            task_meta = r_task_meta.json()
            display_attr = next((attr for attr in task_meta['attributes'] if attr['id'] == display_attr_id), None)

            if display_attr:
                print_status(True,
                             f"Обратная связь 'linked_tasks' будет использовать колонку '{display_attr['name']}' для отображения.")
            else:
                print_status(False, f"Не удалось найти отображаемую колонку для ID: {display_attr_id}")
        else:
            print_status(False, "Не удалось найти метаданные обратной колонки 'linked_tasks'")
        # --- КОНЕЦ НОВОГО БЛОКА ПРОВЕРКИ ---
        return table_ids
    except Exception as e:
        print_status(False, "Ошибка на этапе создания таблиц", getattr(e, 'response', 'N/A').text)
        return None

def create_initial_data(headers: Dict[str, str]) -> Optional[Dict[str, List[int]]]:
    """Наполняет таблицы начальными данными."""
    ids = {"project_ids": [], "task_ids": []}
    try:
        # 1. Создаем 3 проекта
        for i in range(1, 4):
            url = f"{BASE_URL}/api/data/{PROJECT_TABLE_NAME}"
            payload = {"name": f"Проект {i}"}
            pretty_print_request("POST", url, headers, payload)
            r = requests.post(url, headers=headers, json=payload)
            pretty_print_response(r)
            r.raise_for_status()
            ids["project_ids"].append(r.json()["data"][0]["id"])
        print_status(True, f"Созданы проекты с ID: {ids['project_ids']}")

        # 2. Создаем 3 задачи
        url = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}"
        # Задача 1
        payload1 = {"name": "Задача без проекта"}
        pretty_print_request("POST", url, headers, payload1)
        r1 = requests.post(url, headers=headers, json=payload1)
        pretty_print_response(r1)
        r1.raise_for_status()
        ids["task_ids"].append(r1.json()["data"][0]["id"])
        # Задача 2
        payload2 = {"name": "Задача с одним проектом", "linked_projects": [ids["project_ids"][0]]}
        pretty_print_request("POST", url, headers, payload2)
        r2 = requests.post(url, headers=headers, json=payload2)
        pretty_print_response(r2)
        r2.raise_for_status()
        ids["task_ids"].append(r2.json()["data"][0]["id"])
        # Задача 3
        payload3 = {"name": "Задача с двумя проектами",
                    "linked_projects": [ids["project_ids"][0], ids["project_ids"][1]]}
        pretty_print_request("POST", url, headers, payload3)
        r3 = requests.post(url, headers=headers, json=payload3)
        pretty_print_response(r3)
        r3.raise_for_status()
        ids["task_ids"].append(r3.json()["data"][0]["id"])

        print_status(True, f"Созданы задачи с ID: {ids['task_ids']}")
        return ids
    except Exception as e:
        print_status(False, "Ошибка на этапе создания данных", getattr(e, 'response', 'N/A').text)
        return None


# ОБНОВЛЕННАЯ ФУНКЦИЯ ТЕСТОВ (только для полноты, т.к. она уже была исправлена в прошлый раз)
def test_link_updates(headers: Dict[str, str], ids: Dict[str, List[int]]):
    """Основная функция, тестирующая все сценарии обновления связей."""
    project_ids = ids["project_ids"]
    task_ids = ids["task_ids"]

    # --- Тест 1: Добавить одну связь к задаче без связей ---
    print("\n--- Тест 1: Добавление первой связи ---")
    payload = {"linked_projects": [project_ids[0]]}
    try:
        url_put = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[0]}"
        pretty_print_request("PUT", url_put, headers, payload)
        r_upd = requests.put(url_put, headers=headers, json=payload)
        pretty_print_response(r_upd)
        r_upd.raise_for_status()

        # Проверка задачи
        url_get_task = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[0]}"
        pretty_print_request("GET", url_get_task, headers)
        r_get_task = requests.get(url_get_task, headers=headers)
        pretty_print_response(r_get_task)
        task_data = r_get_task.json()

        links = task_data.get("linked_projects", [])
        ok = len(links) == 1 and links[0]['id'] == project_ids[0]
        project_name = f"'{links[0]['value']}'" if ok and links[0]['value'] != 'N/A' else "ИМЯ НЕ НАЙДЕНО"
        print_status(ok, f"Задача {task_ids[0]} теперь ссылается на проект {project_name} (ID: {project_ids[0]})")
        if project_name == "ИМЯ НЕ НАЙДЕНО": test_failed = True  # Добавляем проверку имени

        # Проверка обратной связи в проекте
        url_get_proj = f"{BASE_URL}/api/data/{PROJECT_TABLE_NAME}/{project_ids[0]}"
        pretty_print_request("GET", url_get_proj, headers)
        r_get_proj = requests.get(url_get_proj, headers=headers)
        pretty_print_response(r_get_proj)
        proj_data = r_get_proj.json()

        back_links = proj_data.get("linked_tasks", [])
        ok_back = any(link['id'] == task_ids[0] for link in back_links)
        task_name = next((link['value'] for link in back_links if link['id'] == task_ids[0]), 'ИМЯ НЕ НАЙДЕНО')
        print_status(ok_back, f"Проект {project_ids[0]} теперь имеет обратную ссылку на задачу '{task_name}'")
        if task_name == "ИМЯ НЕ НАЙДЕНО": test_failed = True  # Добавляем проверку имени

    except Exception as e:
        print_status(False, "Ошибка при добавлении первой связи", getattr(e, 'response', 'N/A').text)

    # --- Тест 2: Добавить вторую связь к задаче с одной связью ---
    print("\n--- Тест 2: Добавление второй связи (старая + новая) ---")
    payload = {"linked_projects": [project_ids[0], project_ids[1]]}
    try:
        url_put = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[1]}"
        pretty_print_request("PUT", url_put, headers, payload)
        r_upd = requests.put(url_put, headers=headers, json=payload)
        pretty_print_response(r_upd)
        r_upd.raise_for_status()

        url_get_task = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[1]}"
        pretty_print_request("GET", url_get_task, headers)
        r_get_task = requests.get(url_get_task, headers=headers)
        pretty_print_response(r_get_task)
        task_data = r_get_task.json()

        links = task_data.get("linked_projects", [])
        link_ids = {link['id'] for link in links}
        ok = len(links) == 2 and link_ids == {project_ids[0], project_ids[1]}
        # <-- ИЗМЕНЕНИЕ: Собираем все имена проектов
        project_names = [f"'{link['value']}'" for link in links]
        print_status(ok, f"Задача {task_ids[1]} теперь ссылается на 2 проекта: {', '.join(project_names)}")

        # Проверка обратной связи во втором проекте
        url_get_proj = f"{BASE_URL}/api/data/{PROJECT_TABLE_NAME}/{project_ids[1]}"
        pretty_print_request("GET", url_get_proj, headers)
        r_get_proj = requests.get(url_get_proj, headers=headers)
        pretty_print_response(r_get_proj)
        proj_data = r_get_proj.json()

        back_links = proj_data.get("linked_tasks", [])
        ok_back = any(link['id'] == task_ids[1] for link in back_links)
        task_name = next((link['value'] for link in back_links if link['id'] == task_ids[1]), 'ИМЯ НЕ НАЙДЕНО')
        print_status(ok_back, f"Проект {project_ids[1]} теперь имеет обратную ссылку на задачу '{task_name}'")

    except Exception as e:
        print_status(False, "Ошибка при добавлении второй связи", getattr(e, 'response', 'N/A').text)

    # --- Тест 3: Удаление одной связи из двух ---
    print("\n--- Тест 3: Удаление одной связи из двух ---")
    payload = {"linked_projects": [project_ids[1]]}
    try:
        url_put = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[2]}"
        pretty_print_request("PUT", url_put, headers, payload)
        r_upd = requests.put(url_put, headers=headers, json=payload)
        pretty_print_response(r_upd)
        r_upd.raise_for_status()

        url_get_task = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[2]}"
        pretty_print_request("GET", url_get_task, headers)
        r_get_task = requests.get(url_get_task, headers=headers)
        pretty_print_response(r_get_task)
        task_data = r_get_task.json()

        links = task_data.get("linked_projects", [])
        ok = len(links) == 1 and links[0]['id'] == project_ids[1]
        # <-- ИЗМЕНЕНИЕ: Показываем имя оставшегося проекта
        project_name = f"'{links[0]['value']}'" if ok else "ИМЯ НЕ НАЙДЕНО"
        print_status(ok, f"В задаче {task_ids[2]} осталась 1 связь с проектом {project_name}")

        # Проверяем, что из проекта 0 обратная связь удалилась
        url_get_proj = f"{BASE_URL}/api/data/{PROJECT_TABLE_NAME}/{project_ids[0]}"
        pretty_print_request("GET", url_get_proj, headers)
        r_get_proj = requests.get(url_get_proj, headers=headers)
        pretty_print_response(r_get_proj)
        proj_data = r_get_proj.json()

        back_links = proj_data.get("linked_tasks", [])
        ok_back_removed = not any(link['id'] == task_ids[2] for link in back_links)
        print_status(ok_back_removed, f"Из проекта {project_ids[0]} удалена обратная ссылка на задачу {task_ids[2]}")

    except Exception as e:
        print_status(False, "Ошибка при удалении одной связи", getattr(e, 'response', 'N/A').text)

    # --- Тест 4: Полная очистка связей ---
    print("\n--- Тест 4: Полная очистка связей ---")
    payload = {"linked_projects": []}
    try:
        url_put = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[1]}"
        pretty_print_request("PUT", url_put, headers, payload)
        r_upd = requests.put(url_put, headers=headers, json=payload)
        pretty_print_response(r_upd)
        r_upd.raise_for_status()

        url_get_task = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[1]}"
        pretty_print_request("GET", url_get_task, headers)
        r_get_task = requests.get(url_get_task, headers=headers)
        pretty_print_response(r_get_task)
        task_data = r_get_task.json()

        links = task_data.get("linked_projects", [])
        ok = not links
        print_status(ok, f"У задачи {task_ids[1]} удалены все связи")

    except Exception as e:
        print_status(False, "Ошибка при полной очистке связей", getattr(e, 'response', 'N/A').text)


    # ... (аналогичные print'ы добавлены для всех остальных тестов) ...

    # --- Тест 2: Добавить вторую связь к задаче с одной связью ---
    print("\n--- Тест 2: Добавление второй связи (старая + новая) ---")
    try:
        url = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[1]}"
        payload = {"linked_projects": [project_ids[0], project_ids[1]]}
        pretty_print_request("PUT", url, headers, payload)
        r_upd = requests.put(url, headers=headers, json=payload)
        pretty_print_response(r_upd)
        r_upd.raise_for_status()

        # ... (логика проверок) ...

    except Exception as e:
        print_status(False, "Ошибка при добавлении второй связи", getattr(e, 'response', 'N/A').text)

    # --- Тест 3: Удаление одной связи из двух ---
    print("\n--- Тест 3: Удаление одной связи из двух ---")
    try:
        url = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[2]}"
        payload = {"linked_projects": [project_ids[1]]}
        pretty_print_request("PUT", url, headers, payload)
        r_upd = requests.put(url, headers=headers, json=payload)
        pretty_print_response(r_upd)
        r_upd.raise_for_status()

        # ... (логика проверок) ...

    except Exception as e:
        print_status(False, "Ошибка при удалении одной связи", getattr(e, 'response', 'N/A').text)

    # --- Тест 4: Полная очистка связей ---
    print("\n--- Тест 4: Полная очистка связей ---")
    try:
        url = f"{BASE_URL}/api/data/{TASK_TABLE_NAME}/{task_ids[1]}"
        payload = {"linked_projects": []}
        pretty_print_request("PUT", url, headers, payload)
        r_upd = requests.put(url, headers=headers, json=payload)
        pretty_print_response(r_upd)
        r_upd.raise_for_status()

        # ... (логика проверок) ...

    except Exception as e:
        print_status(False, "Ошибка при полной очистке связей", getattr(e, 'response', 'N/A').text)


def cleanup(headers: Dict[str, str], table_ids: Optional[Dict[str, int]]):
    """Удаляет тестовые таблицы."""
    if not table_ids:
        print("-> Пропуск очистки: таблицы не были созданы.")
        return
    try:
        if "task_id" in table_ids:
            url = f"{BASE_URL}/api/meta/entity-types/{table_ids['task_id']}"
            pretty_print_request("DELETE", url, headers)
            r = requests.delete(url, headers=headers)
            pretty_print_response(r)
            print_status(r.status_code == 204, f"Таблица '{TASK_TABLE_NAME}' (ID: {table_ids['task_id']}) удалена")
        if "project_id" in table_ids:
            url = f"{BASE_URL}/api/meta/entity-types/{table_ids['project_id']}"
            pretty_print_request("DELETE", url, headers)
            r = requests.delete(url, headers=headers)
            pretty_print_response(r)
            print_status(r.status_code == 204,
                         f"Таблица '{PROJECT_TABLE_NAME}' (ID: {table_ids['project_id']}) удалена")
    except Exception as e:
        print_status(False, "Ошибка на этапе очистки", getattr(e, 'response', 'N/A').text)


def main():
    """Главная функция для запуска всех тестов."""
    print_header("Авторизация")
    headers = login()
    if not headers:
        sys.exit(1)

    table_ids = None
    try:
        print_header("Шаг 1: Создание тестовых таблиц и связей")
        table_ids = create_tables(headers)
        if not table_ids:
            sys.exit(1)

        print_header("Шаг 2: Создание начальных данных")
        initial_ids = create_initial_data(headers)
        if not initial_ids:
            sys.exit(1)

        print_header("Шаг 3: Тестирование обновлений связей 'многие-ко-многим'")
        test_link_updates(headers, initial_ids)

    finally:
        print_header("Шаг 4: Очистка тестовых данных")
        # cleanup(headers, table_ids)

        print_header("Итоги тестирования")
        if test_failed:
            print("❌ Тестирование завершилось с ошибками.")
            sys.exit(1)
        else:
            print("✅ Все тесты прошли успешно!")


if __name__ == "__main__":
    main()