import requests
import time
import json

# --- КОНФИГУРАЦИЯ ---
# Замените на URL вашего API
BASE_URL = "http://89.111.169.47:8005"

# Учетные данные пользователей
USER_A_EMAIL = "AntonShlips@example.com"
USER_A_PASSWORD = "AntonShlips(1985)"

USER_B_EMAIL = "1@example.com"
USER_B_PASSWORD = "string"
# ВАЖНО: Вставьте сюда ID пользователя 1@example.com из админ-панели
USER_B_ID = 24  # <-- ЗАМЕНИТЕ ЭТО ЧИСЛО

# --- КОНЕЦ КОНФИГУРАЦИИ ---

# Уникальное имя для нашей тестовой таблицы, чтобы не пересекаться с другими
TEST_TABLE_SYSTEM_NAME = f"test_projects_{int(time.time())}"
TEST_TABLE_DISPLAY_NAME = "Тестовые проекты для проверки доступа"


def login(email, password):
    """Логинится и возвращает JWT токен."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/token",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"\n[!!!] Ошибка входа для пользователя {email}: {e}")
        if e.response is not None:
            print(f"    Ответ сервера: {e.response.text}")
        return None


def print_status(message, response, expected_status):
    """Красиво выводит результат проверки статуса ответа."""
    if response.status_code == expected_status:
        print(f"[OK] {message} (Статус: {response.status_code})")
        return True
    else:
        print(f"[FAIL] {message} (Ожидался: {expected_status}, Получен: {response.status_code})")
        print(f"       Ответ сервера: {response.text[:200]}")
        return False


def main():
    """Основной сценарий тестирования."""
    print(">>> НАЧАЛО ТЕСТИРОВАНИЯ ДОСТУПОВ <<<")

    # --- Фаза 1: Настройка ---
    print("\n--- [ФАЗА 1] Пользователь А (Владелец) создает таблицу и данные ---")
    token_a = login(USER_A_EMAIL, USER_A_PASSWORD)
    if not token_a: return

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1.1 Создаем таблицу
    table_response = requests.post(
        f"{BASE_URL}/api/meta/entity-types",
        headers=headers_a,
        json={"name": TEST_TABLE_SYSTEM_NAME, "display_name": TEST_TABLE_DISPLAY_NAME}
    )
    if not print_status("Создание тестовой таблицы", table_response, 201): return
    table_id = table_response.json()["id"]

    # 1.2 Создаем запись в таблице
    data_response = requests.post(
        f"{BASE_URL}/api/data/{TEST_TABLE_SYSTEM_NAME}",
        headers=headers_a,
        json={"name": "Секретный проект"}
    )
    if not print_status("Создание тестовой записи", data_response, 201): return

    # --- Фаза 2: Проверка доступов для Пользователя Б ---
    print("\n--- [ФАЗА 2] Проверки от имени Пользователя Б (без прав и доступов) ---")
    token_b = login(USER_B_EMAIL, USER_B_PASSWORD)
    if not token_b: return
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2.1 Пытаемся получить список таблиц
    tables_list_resp = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers_b)
    if print_status("Получение списка таблиц", tables_list_resp, 200):
        tables = tables_list_resp.json()
        if any(t['name'] == TEST_TABLE_SYSTEM_NAME for t in tables):
            print(f"[FAIL] Пользователь Б видит таблицу '{TEST_TABLE_DISPLAY_NAME}', хотя не должен!")
        else:
            print(f"[OK] Пользователь Б НЕ видит чужую таблицу в списке.")

    # 2.2 Пытаемся получить данные напрямую (самая важная проверка)
    data_access_resp = requests.get(f"{BASE_URL}/api/data/{TEST_TABLE_SYSTEM_NAME}", headers=headers_b)
    print_status("Попытка прямого доступа к данным чужой таблицы", data_access_resp, 403)  # Ожидаем ошибку "Forbidden"

    # --- Фаза 3: Владелец делится доступом (но у пользователя Б все еще НЕТ РОЛИ) ---
    print(f"\n--- [ФАЗА 3] Пользователь А делится таблицей с Пользователем Б (у которого нет ролей) ---")
    share_response = requests.post(
        f"{BASE_URL}/api/shares",
        headers=headers_a,
        json={
            "entity_type_id": table_id,
            "grantee_user_id": USER_B_ID,
            "permission_level": "view"
        }
    )
    if not print_status("Предоставление доступа (sharing)", share_response, 201): return
    share_id = share_response.json()["id"]

    # 3.1 Повторная проверка от имени Пользователя Б
    print("\n--- [ПРОВЕРКА УЯЗВИМОСТИ] Пользователь Б пытается получить доступ, имея 'share', но не имея роли ---")
    data_access_resp_2 = requests.get(f"{BASE_URL}/api/data/{TEST_TABLE_SYSTEM_NAME}", headers=headers_b)
    print_status("Попытка доступа к данным (только 'share', без роли)", data_access_resp_2, 403)

    # --- Фаза 4: Администратор выдает роль Пользователю Б ---
    print("\n" + "=" * 70)
    print("!!! ВНИМАНИЕ: ТРЕБУЕТСЯ РУЧНОЕ ДЕЙСТВИЕ !!!")
    print("1. Зайдите в Админ-панель.")
    print("2. Перейдите в 'Разрешения' и создайте новое разрешение с именем:")
    print(f"   data:view:{TEST_TABLE_SYSTEM_NAME}")
    print("3. Перейдите в 'Роли', выберите роль 'Test Viewer' и добавьте ей это новое разрешение.")
    print(
        "4. Перейдите в 'Назначение Ролей', выберите пользователя '1@example.com' и назначьте ему роль 'Test Viewer'.")
    input("После выполнения этих действий, нажмите Enter для продолжения теста...")
    print("=" * 70 + "\n")

    # --- Фаза 5: Финальная проверка (есть и share, и роль) ---
    print("\n--- [ФАЗА 5] Финальная проверка. У Пользователя Б есть и 'share', и роль ---")
    data_access_resp_3 = requests.get(f"{BASE_URL}/api/data/{TEST_TABLE_SYSTEM_NAME}", headers=headers_b)
    print_status("Попытка доступа к данным (есть 'share' И роль)", data_access_resp_3, 200)

    # --- Фаза 6: Отзыв доступа ---
    print("\n--- [ФАЗА 6] Пользователь А отзывает доступ ---")
    revoke_response = requests.delete(f"{BASE_URL}/api/shares/{share_id}", headers=headers_a)
    print_status("Отзыв доступа (sharing)", revoke_response, 204)

    # 6.1 Проверка, что доступ снова пропал
    data_access_resp_4 = requests.get(f"{BASE_URL}/api/data/{TEST_TABLE_SYSTEM_NAME}", headers=headers_b)
    print_status("Попытка доступа к данным после отзыва 'share' (роль осталась)", data_access_resp_4, 403)

    # --- Фаза 7: Очистка ---
    print("\n--- [ФАЗА 7] Очистка тестовых данных ---")
    delete_response = requests.delete(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers_a)
    print_status("Удаление тестовой таблицы", delete_response, 204)

    print("\n>>> ТЕСТИРОВАНИЕ ЗАВЕРШЕНО <<<")


if __name__ == "__main__":
    main()