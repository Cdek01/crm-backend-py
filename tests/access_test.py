import requests
import time
import json

# --- КОНФИГУРАЦИЯ ---
# Замените на URL вашего API
BASE_URL = "http://89.111.169.47:8005"

USER_A_EMAIL = "AntonShlips@example.com"  # Владелец
USER_A_PASSWORD = "AntonShlips(1985)"

USER_B_EMAIL = "1@example.com"  # Редактор
USER_B_PASSWORD = "string"
USER_B_ID = 24  # <-- ЗАМЕНИТЕ НА ID пользователя 1@example.com

USER_C_EMAIL = "danikbelavin2006@gmail.com"  # Наблюдатель
USER_C_PASSWORD = "daniil157!?"
USER_C_ID = 21  # <-- ЗАМЕНИТЕ НА ID пользователя viewer@example.com

# Уникальные имена для таблиц
TIMESTAMP = int(time.time())
PROJECTS_TABLE_NAME = f"test_projects_{TIMESTAMP}"
TASKS_TABLE_NAME = f"test_tasks_{TIMESTAMP}"


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (без изменений) ---
def login(email, password):
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"\n[!!!] Ошибка входа для {email}: {e.response.text}")
        return None


def print_status(message, response, expected_status):
    is_ok = response.status_code == expected_status
    status_char = "[OK]" if is_ok else "[FAIL]"
    print(f"{status_char} {message} (Статус: {response.status_code}, Ожидался: {expected_status})")
    if not is_ok:
        print(f"       Ответ: {response.text[:200]}")
    return is_ok


# --- ОСНОВНОЙ СЦЕНАРИЙ ---
def run_test():
    print(">>> НАЧАЛО РАСШИРЕННОГО ТЕСТИРОВАНИЯ ДОСТУПОВ <<<")

    # --- ФАЗА 1: Вход и настройка ---
    token_a = login(USER_A_EMAIL, USER_A_PASSWORD)
    token_b = login(USER_B_EMAIL, USER_B_PASSWORD)
    token_c = login(USER_C_EMAIL, USER_C_PASSWORD)
    if not all([token_a, token_b, token_c]): return

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    headers_c = {"Authorization": f"Bearer {token_c}"}

    print("\n--- [ФАЗА 1] Пользователь А (Владелец) создает 2 таблицы ---")

    # Создаем таблицу Проекты
    resp_proj = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers_a,
                              json={"name": PROJECTS_TABLE_NAME, "display_name": "Проекты"})
    if not print_status("Создание таблицы 'Проекты'", resp_proj, 201): return
    projects_table_id = resp_proj.json()["id"]

    # Создаем таблицу Задачи
    resp_tasks = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers_a,
                               json={"name": TASKS_TABLE_NAME, "display_name": "Задачи"})
    if not print_status("Создание таблицы 'Задачи'", resp_tasks, 201): return
    tasks_table_id = resp_tasks.json()["id"]

    # --- ФАЗА 2: Владелец делится доступом к 'Проектам' ---
    print("\n--- [ФАЗА 2] Владелец делится доступом к 'Проектам' ---")
    share_b_resp = requests.post(f"{BASE_URL}/api/shares", headers=headers_a,
                                 json={"entity_type_id": projects_table_id, "grantee_user_id": USER_B_ID,
                                       "permission_level": "edit"})
    if not print_status("Предоставление доступа EDIT Пользователю Б", share_b_resp, 201): return

    share_c_resp = requests.post(f"{BASE_URL}/api/shares", headers=headers_a,
                                 json={"entity_type_id": projects_table_id, "grantee_user_id": USER_C_ID,
                                       "permission_level": "view"})
    if not print_status("Предоставление доступа VIEW Пользователю В", share_c_resp, 201): return

    # --- Фаза 3: Настройка ролей в Админке ---
    print("\n" + "=" * 70)
    print("!!! ВНИМАНИЕ: ТРЕБУЕТСЯ РУЧНОЕ ДЕЙСТВИЕ В АДМИН-ПАНЕЛИ !!!")
    print("1. Создайте 2 разрешения (Permissions):")
    print(f"   - data:view:{PROJECTS_TABLE_NAME}")
    print(f"   - data:edit:{PROJECTS_TABLE_NAME}")
    print("2. Настройте Роли:")
    print("   - Роли 'Test Viewer' дайте право 'data:view:...'")
    print("   - Роли 'Test Editor' дайте ОБА права: 'data:view:...' и 'data:edit:...'")
    print("3. Назначьте Роли Пользователям:")
    print(f"   - Пользователю {USER_B_EMAIL} назначьте роль 'Test Editor'.")
    print(f"   - Пользователю {USER_C_EMAIL} назначьте роль 'Test Viewer'.")
    input("После выполнения этих действий, нажмите Enter для продолжения...")
    print("=" * 70 + "\n")

    # --- ФАЗА 4: Проверки ---
    print("\n--- [ФАЗА 4] Проверка доступов для всех пользователей ---")

    # Проверки для Пользователя Б (Редактор)
    print("\n--- Проверки для Пользователя Б (Редактор) ---")
    resp_b_view = requests.get(f"{BASE_URL}/api/data/{PROJECTS_TABLE_NAME}", headers=headers_b)
    print_status("[Б] Может просматривать 'Проекты'", resp_b_view, 200)

    resp_b_create = requests.post(f"{BASE_URL}/api/data/{PROJECTS_TABLE_NAME}", headers=headers_b,
                                  json={"name": "Новый проект от Б"})
    print_status("[Б] НЕ может создавать записи в 'Проектах' (нужно право 'create')", resp_b_create, 403)

    # Сначала Владелец А создаст запись, чтобы Б мог ее отредактировать
    resp_a_create = requests.post(f"{BASE_URL}/api/data/{PROJECTS_TABLE_NAME}", headers=headers_a,
                                  json={"name": "Проект для редактирования"})
    entity_id = resp_a_create.json()["data"][0]["id"]

    resp_b_edit = requests.put(f"{BASE_URL}/api/data/{PROJECTS_TABLE_NAME}/{entity_id}", headers=headers_b,
                               json={"name": "Отредактировано Б"})
    print_status("[Б] Может редактировать записи в 'Проектах'", resp_b_edit, 200)

    resp_b_delete = requests.delete(f"{BASE_URL}/api/data/{PROJECTS_TABLE_NAME}/{entity_id}", headers=headers_b)
    print_status("[Б] НЕ может удалять записи из 'Проектов' (нужно право 'delete')", resp_b_delete, 403)

    resp_b_tasks = requests.get(f"{BASE_URL}/api/data/{TASKS_TABLE_NAME}", headers=headers_b)
    print_status("[Б] НЕ может видеть 'Задачи'", resp_b_tasks, 403)

    # Проверки для Пользователя В (Наблюдатель)
    print("\n--- Проверки для Пользователя В (Наблюдатель) ---")
    resp_c_view = requests.get(f"{BASE_URL}/api/data/{PROJECTS_TABLE_NAME}", headers=headers_c)
    print_status("[В] Может просматривать 'Проекты'", resp_c_view, 200)

    resp_c_edit = requests.put(f"{BASE_URL}/api/data/{PROJECTS_TABLE_NAME}/{entity_id}", headers=headers_c,
                               json={"name": "Попытка редактирования от В"})
    print_status("[В] НЕ может редактировать записи в 'Проектах'", resp_c_edit, 403)

    resp_c_tasks = requests.get(f"{BASE_URL}/api/data/{TASKS_TABLE_NAME}", headers=headers_c)
    print_status("[В] НЕ может видеть 'Задачи'", resp_c_tasks, 403)

    # --- ФАЗА 5: Очистка ---
    print("\n--- [ФАЗА 5] Очистка тестовых данных ---")
    del_proj = requests.delete(f"{BASE_URL}/api/meta/entity-types/{projects_table_id}", headers=headers_a)
    print_status("Удаление таблицы 'Проекты'", del_proj, 204)
    del_tasks = requests.delete(f"{BASE_URL}/api/meta/entity-types/{tasks_table_id}", headers=headers_a)
    print_status("Удаление таблицы 'Задачи'", del_tasks, 204)
    print("!!! Не забудьте удалить тестовые роли и разрешения в админ-панели !!!")

    print("\n>>> РАСШИРЕННОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО <<<")


if __name__ == "__main__":
    run_test()