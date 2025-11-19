import requests
import time
import psycopg2
import json

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://localhost:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"  # Замените на ваш пароль

# Данные для прямого подключения к БД
DB_NAME = "crm_db"
DB_USER = "crm_user"
DB_PASSWORD = "your_strong_password"  # Замените на ваш пароль от БД
DB_HOST = "localhost"
DB_PORT = "5432"

TEST_MODULBANK_TOKEN = "MGIwMjlmZjEtMjM2MC00ZWJmLWE4NTktNmI1ZDA4Y2RmYWE4NmRjOTQ0MGYtYzUzNi00MGQ3LWIwNmYtZDZmNDQxZjlmMDFl"

# --- КОНЕЦ КОНФИГУРАЦИИ ---


# --- Вспомогательные функции ---

def login(email, password):
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        print("[OK] Успешный вход в систему")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Ошибка входа для {email}: {e.response.text if e.response else e}")
        return None


def get_db_connection():
    try:
        return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    except Exception as e:
        print(f"[FAIL] Не удалось подключиться к базе данных: {e}")
        return None


def get_task_for_tenant(conn, tenant_id):
    """Находит задачу Celery для клиента в БД."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT pt.id, pt.name
            FROM celery_periodic_task pt
            WHERE pt.args = %s
            """,
            (json.dumps([tenant_id]),)
        )
        return cursor.fetchone()


# --- Основной сценарий теста ---

def run_cancel_test():
    print(">>> Тест: Создание и отмена периодической задачи <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}

    db_conn = get_db_connection()
    if not db_conn: return

    try:
        # Получаем tenant_id для проверок
        resp_me = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        tenant_id = resp_me.json().get('tenant_id')
        if not tenant_id:
            print("[FAIL] Не удалось получить tenant_id от API.")
            return
        print(f"[INFO] Работаем с клиентом (tenant_id): {tenant_id}")

        # --- [ШАГ 1] Начальная очистка ---
        print("\n--- [ШАГ 1] Начальная очистка (отключаем интеграцию)... ---")
        requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)

        # --- [ШАГ 2] Создаем задачу ---
        print("\n--- [ШАГ 2] Отправка запроса на создание задачи... ---")
        settings_payload = {
            "api_token": TEST_MODULBANK_TOKEN, # <-- ДОБАВЛЯЕМ КЛЮЧ
            "schedule_type": "daily",
            "sync_time": "14:30:00"
        }
        resp_api = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                 json=settings_payload)

        if resp_api.status_code != 200:
            print(f"[FAIL] API вернул ошибку при создании задачи! (Статус: {resp_api.status_code})")
            return
        print("[OK] API успешно создал задачу.")

        # Проверяем, что задача действительно появилась в БД
        time.sleep(1)  # Небольшая пауза
        db_conn.commit()
        task_info = get_task_for_tenant(db_conn, tenant_id)
        if task_info:
            print(f"[OK] Проверка: Задача ID={task_info[0]} найдена в базе данных.")
        else:
            print("[FAIL] Проверка: Задача не найдена в базе данных после создания!")
            return

        # --- [ШАГ 3] Отменяем задачу ---
        print("\n--- [ШАГ 3] Отправка запроса на отмену задачи (DELETE-запросом)... ---")
        resp_delete = requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)

        if resp_delete.status_code != 200:
            print(f"[FAIL] API вернул ошибку при отмене задачи! (Статус: {resp_delete.status_code})")
            return
        print("[OK] API успешно обработал запрос на отмену.")

        # Проверяем, что задача действительно исчезла из БД
        time.sleep(1)
        db_conn.commit()
        task_after_cancel = get_task_for_tenant(db_conn, tenant_id)
        if task_after_cancel is None:
            print("[SUCCESS] Тест пройден! Задача успешно удалена из расписания.")
        else:
            print("[FAIL] Тест провален! Задача все еще существует в БД после отмены.")

    finally:
        if db_conn:
            db_conn.close()

    print("\n>>> ПРОВЕРКА ЗАВЕРШЕНА <<<")


if __name__ == "__main__":
    run_cancel_test()