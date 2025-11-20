import requests
import time
import psycopg2
import json
from typing import Optional, Any

# --- КОНФИГУРАЦИЯ ---
# URL вашего API-сервера
BASE_URL = "http://89.111.169.47:8005"

# Учетные данные пользователя для входа
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"

# ВАЖНО: Вставьте сюда ваш РЕАЛЬНЫЙ токен от Модульбанка
REAL_MODULBANK_TOKEN = "MGIwMjlmZjEtMjM2MC00ZWJmLWE4NTktNmI1ZDA4Y2RmYWE4NmRjOTQ0MGYtYzUzNi00MGQ3LWIwNmYtZDZmNDQxZjlmMDFl"

# Данные для прямого подключения к БД (например, через SSH-туннель)
DB_NAME = "crm_db"
DB_USER = "crm_user"
DB_PASSWORD = "your_strong_password"  # Замените на ваш пароль от БД
DB_HOST = "localhost"  # 'localhost', если используете SSH-туннель
DB_PORT = "5432"


def login(email, password):
    """Логинится в систему и возвращает JWT токен."""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        print("[OK] Успешный вход в систему")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Ошибка входа для {email}: {e.response.text if e.response else e}")
        return None


def print_status(message, is_ok, details=""):
    """Удобно выводит результат проверки в консоль."""
    status_char = "[OK]" if is_ok else "[FAIL]"
    print(f"{status_char} {message} {details}")
    return is_ok


def get_db_connection():
    """Устанавливает прямое соединение с базой данных."""
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        print("[OK] Успешное подключение к базе данных")
        return conn
    except Exception as e:
        print(f"[FAIL] Не удалось подключиться к базе данных: {e}")
        return None


def get_tenant_sync_sources(conn, tenant_id):
    """Получает сохраненные ID счетов для синхронизации из базы данных."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT modulbank_sync_sources FROM tenants WHERE id = %s", (tenant_id,))
        result = cursor.fetchone()
        if result and result[0]:
            try:
                return json.loads(result[0])
            except (json.JSONDecodeError, TypeError):
                return None
        return None


def run_setup_integration_test():
    """
    Основной сценарий теста: настраивает и активирует интеграцию.
    """
    print(">>> Тест: НАСТРОЙКА интеграции с выбором ВСЕХ доступных компаний <<<")

    if "ВАШ_РЕАЛЬНЫЙ_API_ТОКЕН" in REAL_MODULBANK_TOKEN:
        print("[FAIL] Пожалуйста, вставьте ваш реальный API токен от Модульбанка в переменную REAL_MODULBANK_TOKEN.")
        return

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    db_conn = get_db_connection()
    if not db_conn:
        return

    try:
        # Получаем ID текущего клиента (tenant_id)
        resp_me = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        if not print_status("Получение данных пользователя", resp_me.ok, f"| Статус: {resp_me.status_code}"):
            return
        tenant_id = resp_me.json().get('tenant_id')
        print(f"[INFO] Работаем с клиентом (tenant_id): {tenant_id}")

        # --- [ШАГ 1] Проверка токена и получение списка компаний от API ---
        print("\n--- [ШАГ 1] Проверка токена и получение списка компаний от API ---")
        resp_validate = requests.post(
            f"{BASE_URL}/api/integrations/modulbank/validate-token",
            headers=headers,
            json={"api_token": REAL_MODULBANK_TOKEN}
        )
        if not print_status("Запрос на валидацию токена", resp_validate.ok,
                            f"| Статус: {resp_validate.status_code}, Ответ: {resp_validate.text[:150]}..."):
            return

        companies = resp_validate.json()
        print(f"    Получено {len(companies)} компаний от Модульбанка.")

        # --- [ШАГ 2] Выбор ВСЕХ компаний и их счетов ---
        print("\n--- [ШАГ 2] Выбор ВСЕХ компаний и всех их счетов для синхронизации ---")
        selected_company_ids = []
        selected_account_ids = []

        if not companies:
            print_status("API не вернуло ни одной компании. Тест остановлен.", False)
            return

        for company in companies:
            company_id = company.get('companyId')
            company_name = company.get('companyName')

            if not company_id:
                print(f"[ПРЕДУПРЕЖДЕНИЕ] Пропуск компании без 'companyId': {company_name or 'Без имени'}")
                continue

            selected_company_ids.append(company_id)
            accounts = company.get('bankAccounts', [])
            account_ids_for_company = [acc.get('id') for acc in accounts if acc.get('id')]
            selected_account_ids.extend(account_ids_for_company)

            print(
                f"    -> Добавлена компания: '{company_name}' (ID: {company_id}) с {len(account_ids_for_company)} счетами.")

        print(f"\n    Итого выбрано компаний: {len(selected_company_ids)}")
        print(f"    Итого выбрано счетов для синхронизации: {len(selected_account_ids)}")

        # --- [ШАГ 3] Сохранение всех настроек ---
        print("\n--- [ШАГ 3] Сохранение всех настроек (ключ, выбор, расписание) ---")
        settings_payload = {
            "api_token": REAL_MODULBANK_TOKEN,
            "schedule_type": "daily",
            "sync_time": "13:55",  # Установите время на несколько минут вперед от текущего
            "selected_company_ids": selected_company_ids,
            "selected_account_ids": selected_account_ids
        }

        resp_save = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                  json=settings_payload)
        if not print_status("Запрос на сохранение настроек", resp_save.ok,
                            f"| Статус: {resp_save.status_code}, Ответ: {resp_save.text[:150]}..."):
            return

        # --- [ШАГ 4] Проверка результата в базе данных ---
        print("\n--- [ШАГ 4] Проверка сохраненных настроек в базе данных ---")
        time.sleep(1)  # Небольшая пауза, чтобы данные гарантированно записались
        db_conn.commit()

        saved_sources = get_tenant_sync_sources(db_conn, tenant_id)
        if not saved_sources:
            print_status("Проверка сохраненных источников", False, "Запись не найдена в БД.")
            return

        print(f"    Сохраненные в БД ID счетов: {saved_sources.get('accounts')}")
        is_ok = set(saved_sources.get('accounts', [])) == set(selected_account_ids)
        print_status("Проверка: сохраненные в БД счета соответствуют ВСЕМ выбранным", is_ok)

        if is_ok:
            print("\n[SUCCESS] Тест пройден! Интеграция настроена и активна.")

    except Exception as e:
        print(f"\n[CRITICAL] В ходе теста произошла непредвиденная ошибка!", False, f"Детали: {e}")
    finally:
        # Закрываем соединение с БД в любом случае
        if db_conn:
            db_conn.close()

    print("\n>>> ТЕСТ НАСТРОЙКИ ИНТЕГРАЦИИ ЗАВЕРШЕН <<<")


if __name__ == "__main__":
    run_setup_integration_test()