import requests
import time
import psycopg2
import json
from typing import Dict, Any, Optional



# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"  # Замените на ваш пароль

# ВАЖНО: Вставьте сюда ваш РЕАЛЬНЫЙ токен от Модульбанка
REAL_MODULBANK_TOKEN = "MGIwMjlmZjEtMjM2MC00ZWJmLWE4NTktNmI1ZDA4Y2RmYWE4NmRjOTQ0MGYtYzUzNi00MGQ3LWIwNmYtZDZmNDQxZjlmMDFl"

# Данные для прямого подключения к БД
DB_NAME = "crm_db"
DB_USER = "crm_user"
DB_PASSWORD = "your_strong_password"  # Замените на ваш пароль от БД
DB_HOST = "localhost"
DB_PORT = "5432"


# --- КОНЕЦ КОНФИГУРАЦИИ ---

# --- Вспомогательные функции ---
def print_status(message, is_ok, details=""):
    # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
    status_char = "[OK]" if is_ok else "[FAIL]"
    print(f"{status_char} {message} {details}")
    return is_ok


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


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
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        print("[OK] Успешное подключение к базе данных через SSH-туннель")
        return conn
    except Exception as e:
        print(f"[FAIL] Не удалось подключиться к базе данных: {e}")
        return None

def get_task_for_tenant(conn, tenant_id):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT pt.id, pt.name, cs.minute, cs.hour, cs.day_of_week
            FROM celery_periodic_task pt
            JOIN celery_crontab_schedule cs ON pt.crontab_id = cs.id
            WHERE pt.args = %s
            """,
            (json.dumps([tenant_id]),)
        )
        return cursor.fetchone()

def check_banking_operations(conn, tenant_id, min_count=1):
    """Проверяет, появились ли записи в таблице banking_operations."""
    with conn.cursor() as cursor:
        # Находим ID таблицы banking_operations
        cursor.execute("SELECT id FROM entity_types WHERE name = 'banking_operations' AND tenant_id = %s", (tenant_id,))
        entity_type_id_row = cursor.fetchone()
        if not entity_type_id_row:
            return False, "EAV-таблица 'banking_operations' не найдена для этого клиента."
        entity_type_id = entity_type_id_row[0]

        # Считаем количество записей
        cursor.execute("SELECT COUNT(*) FROM entities WHERE entity_type_id = %s", (entity_type_id,))
        count = cursor.fetchone()[0]

        if count >= min_count:
            return True, f"Найдено {count} записей."
        else:
            return False, f"Найдено {count} записей, ожидалось как минимум {min_count}."


# --- Основной сценарий полного end-to-end теста ---

def run_full_test():
    print(">>> НАЧАЛО ПОЛНОГО E2E ТЕСТА ИНТЕГРАЦИИ С МОДУЛЬБАНКОМ <<<")

    if "ВАШ_РЕАЛЬНЫЙ_API_ТОКЕН" in REAL_MODULBANK_TOKEN:
        print("[FAIL] Пожалуйста, вставьте ваш реальный API токен от Модульбанка в переменную REAL_MODULBANK_TOKEN.")
        return

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}

    db_conn = get_db_connection()
    if not db_conn: return

    try:
        resp_me = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        tenant_id = resp_me.json().get('tenant_id')

        # --- [ШАГ 1] Начальная очистка ---
        print("\n--- [ШАГ 1] Начальная очистка ---")
        requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
        print("    Старые настройки интеграции удалены.")
        # (Здесь можно добавить код для очистки старых операций из banking_operations, если нужно)

        # --- [ШАГ 2] Подключение интеграции с реальным ключом ---
        print("\n--- [ШАГ 2] Подключение интеграции с реальным API ключом ---")
        settings_payload = {
            "api_token": REAL_MODULBANK_TOKEN,
            "schedule_type": "manual"  # Запускать будем вручную
        }
        resp_connect = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                     json=settings_payload)
        if not print_status("Запрос на подключение интеграции", resp_connect.status_code == 200):
            print("    Тест не может продолжаться без успешного подключения.")
            return

        # --- [ШАГ 3] Ожидание завершения фоновой задачи ---
        print("\n--- [ШАГ 3] Ожидание завершения первой фоновой синхронизации (до 60 секунд)... ---")
        sync_completed = False
        for i in range(12):  # Проверяем 12 раз с интервалом 5 секунд
            time.sleep(5)
            print(f"    Проверка #{i + 1}...")

            resp_status = requests.get(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
            status_data = resp_status.json()

            if status_data.get("last_error"):
                print_status("Синхронизация завершилась с ошибкой", False, f"Детали: {status_data['last_error']}")
                sync_completed = True
                break

            if status_data.get("last_sync"):
                print_status("Синхронизация успешно завершена", True, f"Время: {status_data['last_sync']}")
                sync_completed = True
                break

        if not sync_completed:
            print_status("Время ожидания синхронизации истекло", False)
            # Не прерываем тест, проверим, может что-то все же успело загрузиться

        # --- [ШАГ 4] Проверка результата в базе данных ---
        print("\n--- [ШАГ 4] Проверка наличия данных в таблице 'banking_operations' ---")
        db_conn.commit()  # Обновляем состояние транзакции

        # Проверяем, что в таблице появилась хотя бы одна запись
        # (Если у вас на счете нет операций за последний месяц, этот шаг может упасть)
        data_exists, details = check_banking_operations(db_conn, tenant_id, min_count=1)
        print_status("Данные из банка появились в CRM", data_exists, f"({details})")

    finally:
        if db_conn:
            print("\n--- [Финал] Отключение интеграции ---")
            requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
            db_conn.close()

    print("\n>>> ПОЛНЫЙ ТЕСТ ЗАВЕРШЕН <<<")


if __name__ == "__main__":
    # Скопируйте сюда код функций login, print_status, get_db_connection
    run_full_test()