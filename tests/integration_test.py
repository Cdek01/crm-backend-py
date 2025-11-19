import requests
import time
import psycopg2
import json

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"  # Замените на ваш пароль

# ВАЖНО: Вставьте сюда ваш РЕАЛЬНЫЙ токен от Модульбанка
# Он нужен, чтобы API-запрос на активацию прошел успешно
REAL_MODULBANK_TOKEN = "MGIwMjlmZjEtMjM2MC00ZWJmLWE4NTktNmI1ZDA4Y2RmYWE4NmRjOTQ0MGYtYzUzNi00MGQ3LWIwNmYtZDZmNDQxZjlmMDFl"

# Данные для прямого подключения к БД (через SSH-туннель, если локально)
DB_NAME = "crm_db"
DB_USER = "crm_user"
DB_PASSWORD = "your_strong_password"  # Замените на ваш пароль от БД
DB_HOST = "localhost"  # 'localhost', если используете SSH-туннель
DB_PORT = "5432"  # Порт для SSH-туннеля (например, 5433)


# --- КОНЕЦ КОНФИГУРАЦИИ ---


# --- Вспомогательные функции (без изменений) ---

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
        print("[OK] Успешное подключение к базе данных")
        return conn
    except Exception as e:
        print(f"[FAIL] Не удалось подключиться к базе данных: {e}")
        return None


def get_task_for_tenant(conn, tenant_id):
    """Находит задачу Celery для клиента в БД."""
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


# --- Основной сценарий теста ---

def setup_11am_schedule():
    print(">>> Тест: Создание задачи синхронизации на 11:00 <<<")

    if "ВАШ_РЕАЛЬНЫЙ_API_ТОКЕН" in REAL_MODULBANK_TOKEN:
        print("[FAIL] Пожалуйста, вставьте ваш реальный API токен в переменную REAL_MODULBANK_TOKEN.")
        return

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}

    db_conn = get_db_connection()
    if not db_conn: return

    try:
        # Получаем tenant_id для проверки в БД
        resp_me = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        tenant_id = resp_me.json().get('tenant_id')
        if not tenant_id:
            print("[FAIL] Не удалось получить tenant_id от API.")
            return
        print(f"[INFO] Работаем с клиентом (tenant_id): {tenant_id}")

        # --- [ШАГ 1] Отправляем запрос на настройку ---
        print("\n--- [ШАГ 1] Отправка запроса на создание/обновление расписания на 11:30 ---")
        settings_payload = {
            "api_token": REAL_MODULBANK_TOKEN,  # Передаем токен для активации
            "schedule_type": "daily",
            "sync_time": "11:30:00"
        }
        resp_api = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                 json=settings_payload)

        if resp_api.status_code == 200:
            print(f"[OK] API успешно обработал запрос (Статус: {resp_api.status_code})")
        else:
            print(f"[FAIL] API вернул ошибку! (Статус: {resp_api.status_code}, Ответ: {resp_api.text})")
            return

        # --- [ШАГ 2] Проверка результата в БД ---
        print("\n--- [ШАГ 2] Проверка расписания напрямую в базе данных Celery... ---")
        db_conn.commit()  # Сбрасываем транзакцию, чтобы увидеть изменения
        task_info = get_task_for_tenant(db_conn, tenant_id)

        if not task_info:
            print("[FAIL] Задача для клиента не была найдена в базе данных!")
            return

        task_id, task_name, minute, hour, day_of_week = task_info
        print(f"    Найдена задача: ID={task_id}, Имя='{task_name}'")
        print(f"    Параметры расписания в БД: Минута='{minute}', Час='{hour}', День недели='{day_of_week}'")

        # Главная проверка
        if minute == '0' and hour == '11' and day_of_week == '*':
            print("\n[SUCCESS] Тест пройден! Задача на ежедневную синхронизацию в 11:00 успешно создана.")
        else:
            print("\n[FAIL] Тест провален! Параметры расписания в базе данных неверные.")
            print(f"          Ожидалось: Минута='0', Час='11'. Получено: Минута='{minute}', Час='{hour}'.")

    finally:
        if db_conn:
            db_conn.close()

    print("\n>>> ПРОВЕРКА ЗАВЕРШЕНА <<<")


if __name__ == "__main__":
    setup_11am_schedule()