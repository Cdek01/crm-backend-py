import requests
import time
from datetime import time as dt_time
import psycopg2
import json

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"

# Данные для прямого подключения к БД для проверки таблиц Celery Beat
DB_NAME = "crm_db"
DB_USER = "crm_user"
DB_PASSWORD = "your_strong_password"
DB_HOST = "localhost"
DB_PORT = "5432"

# Тестовый API токен для Модульбанка
TEST_MODULBANK_TOKEN = "MGIwMjlmZjEtMjM2MC00ZWJmLWE4NTktNmI1ZDA4Y2RmYWE4NmRjOTQ0MGYtYzUzNi00MGQ3LWIwNmYtZDZmNDQxZjlmMDFl"


# --- КОНЕЦ КОНФИГУРАЦИИ ---

# --- Вспомогательные функции ---

def login(email, password):
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"\n[!!!] Ошибка входа для {email}: {e.response.text if e.response else e}")
        return None


def print_status(message, is_ok, details=""):
    status_char = "[OK]" if is_ok else "[FAIL]"
    print(f"{status_char} {message} {details}")
    return is_ok


def get_db_connection():
    """Устанавливает прямое соединение с БД."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"[FAIL] Не удалось подключиться к базе данных: {e}")
        return None


def get_periodic_task_for_tenant(conn, tenant_id):
    """Находит задачу Celery Beat для клиента в БД."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT pt.id, pt.name, cs.minute, cs.hour, cs.day_of_week
            FROM django_celery_beat_periodictask pt
            JOIN django_celery_beat_crontabschedule cs ON pt.crontab_id = cs.id
            WHERE pt.args = %s
            """,
            (json.dumps([tenant_id]),)
        )
        return cursor.fetchone()


# --- Основной сценарий теста ---

def run_integration_test():
    print(">>> НАЧАЛО ТЕСТИРОВАНИЯ ИНТЕГРАЦИИ С МОДУЛЬБАНКОМ <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}

    db_conn = get_db_connection()
    if not db_conn: return

    try:
        # --- [ШАГ 1] Начальное состояние: Отключаем интеграцию ---
        print("\n--- [ШАГ 1] Начальная очистка и отключение интеграции ---")
        resp_disconnect = requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
        print_status("Отключение интеграции (для чистоты теста)", resp_disconnect.status_code == 200)

        # Проверяем, что в БД нет задачи для этого клиента (получаем tenant_id)
        resp_me = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        tenant_id = resp_me.json().get('tenant_id')
        if not tenant_id:
            print_status("Не удалось получить tenant_id", False)
            return

        task = get_periodic_task_for_tenant(db_conn, tenant_id)
        print_status("Проверка: в БД нет периодической задачи для клиента", task is None)

        # --- [ШАГ 2] Сохранение с ЕЖЕДНЕВНЫМ расписанием ---
        print("\n--- [ШАГ 2] Тест: Сохранение с ЕЖЕДНЕВНЫМ расписанием (9:30) ---")
        settings_daily = {
            "api_token": TEST_MODULBANK_TOKEN,
            "schedule_type": "daily",
            "sync_time": "09:30:00"
        }
        resp_daily = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                   json=settings_daily)
        if not print_status("Запрос на сохранение ежедневного расписания", resp_daily.status_code == 200): return

        # Проверяем, что в БД появилась правильная задача
        db_conn.commit()  # Завершаем предыдущие транзакции
        task_daily = get_periodic_task_for_tenant(db_conn, tenant_id)
        is_daily_ok = (
                task_daily is not None and
                task_daily[2] == '30' and  # minute
                task_daily[3] == '9' and  # hour
                task_daily[4] == '*'  # day_of_week
        )
        print_status("Проверка: в БД создана корректная ЕЖЕДНЕВНАЯ задача", is_daily_ok)

        # --- [ШАГ 3] Сохранение с ЕЖЕНЕДЕЛЬНЫМ расписанием ---
        print("\n--- [ШАГ 3] Тест: Сохранение с ЕЖЕНЕДЕЛЬНЫМ расписанием (Ср, 15:00) ---")
        settings_weekly = {
            # Токен не передаем, он должен остаться старым
            "schedule_type": "weekly",
            "sync_time": "15:00:00",
            "sync_weekday": 2  # 0=Пн, 1=Вт, 2=Ср
        }
        resp_weekly = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                    json=settings_weekly)
        if not print_status("Запрос на сохранение еженедельного расписания", resp_weekly.status_code == 200): return

        # Проверяем, что старая задача удалена, а новая создана
        db_conn.commit()
        task_weekly = get_periodic_task_for_tenant(db_conn, tenant_id)
        is_weekly_ok = (
                task_weekly is not None and
                task_weekly[2] == '0' and  # minute
                task_weekly[3] == '15' and  # hour
                task_weekly[4] == '2'  # day_of_week (Среда)
        )
        print_status("Проверка: в БД создана корректная ЕЖЕНЕДЕЛЬНАЯ задача", is_weekly_ok)

        # --- [ШАГ 4] Отключение (перевод в ручной режим) ---
        print("\n--- [ШАГ 4] Тест: Отключение авто-синхронизации (ручной режим) ---")
        settings_manual = {"schedule_type": "manual"}
        resp_manual = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                    json=settings_manual)
        if not print_status("Запрос на перевод в ручной режим", resp_manual.status_code == 200): return

        # Проверяем, что задача из БД удалена
        db_conn.commit()
        task_manual = get_periodic_task_for_tenant(db_conn, tenant_id)
        print_status("Проверка: периодическая задача в БД удалена", task_manual is None)

    finally:
        if db_conn:
            # Финальная очистка
            print("\n--- [Финал] Полное отключение интеграции для чистоты ---")
            requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
            db_conn.close()

    print("\n>>> ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ЗАВЕРШЕНО <<<")


if __name__ == "__main__":
    run_integration_test()