from typing import Optional, Any

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


def login(email, password):
    """Логинится и возвращает JWT токен."""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        print("[OK] Успешный вход в систему")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Ошибка входа для {email}: {e.response.text if e.response else e}")
        return None


def print_status(message, is_ok, details=""):
    """Красиво выводит результат проверки."""
    status_char = "[OK]" if is_ok else "[FAIL]"
    print(f"{status_char} {message} {details}")
    return is_ok


def get_db_connection():
    """Устанавливает прямое соединение с БД."""
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        print("[OK] Успешное подключение к базе данных")
        return conn
    except Exception as e:
        print(f"[FAIL] Не удалось подключиться к базе данных: {e}")
        return None


def get_tenant_sync_sources(conn, tenant_id):
    """Получает сохраненные источники синхронизации из БД."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT modulbank_sync_sources FROM tenants WHERE id = %s", (tenant_id,))
        result = cursor.fetchone()
        if result and result[0]:
            try:
                return json.loads(result[0])
            except (json.JSONDecodeError, TypeError):
                return None
        return None


# --- Основной сценарий теста ---

def run_select_company_test():
    print(">>> Тест: Настройка интеграции с выбором второй компании <<<")

    if "ВАШ_РЕАЛЬНЫЙ_API_ТОКЕН" in REAL_MODULBANK_TOKEN:
        print("[FAIL] Пожалуйста, вставьте ваш реальный API токен от Модульбанка.")
        return

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}

    db_conn = get_db_connection()
    if not db_conn: return

    try:
        resp_me = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        if not resp_me.ok:
            print_status("Не удалось получить данные пользователя.", False, f"Статус: {resp_me.status_code}")
            return
        tenant_id = resp_me.json().get('tenant_id')
        print(f"[INFO] Работаем с клиентом (tenant_id): {tenant_id}")

        # --- [ШАГ 1] Начальная очистка ---
        print("\n--- [ШАГ 1] Начальная очистка ---")
        resp_delete = requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
        if print_status("Запрос на отключение старой интеграции", resp_delete.status_code == 200,
                        f"| Статус: {resp_delete.status_code}"):
            print("    Старые настройки интеграции удалены.")

        # --- [ШАГ 2] Проверка токена и получение списка компаний ---
        print("\n--- [ШАГ 2] Проверка токена и получение списка компаний от API ---")
        resp_validate = requests.post(
            f"{BASE_URL}/api/integrations/modulbank/validate-token",
            headers=headers,
            json={"api_token": REAL_MODULBANK_TOKEN}
        )
        if not print_status("Запрос на валидацию токена", resp_validate.status_code == 200,
                            f"| Статус: {resp_validate.status_code}, Ответ: {resp_validate.text[:150]}..."):
            return

        companies = resp_validate.json()
        print(f"    Получено {len(companies)} компаний от Модульбанка.")

        if len(companies) < 2:
            print_status("Для этого теста необходимо как минимум 2 компании в ответе API.", False)
            return

        # --- [ШАГ 3] Выбор второй компании и ее счетов ---
        print("\n--- [ШАГ 3] Выбор второй компании и всех ее счетов для синхронизации ---")

        try:
            second_company = companies[1]
            selected_company_id = second_company.get('companyId')
            selected_account_ids = [acc.get('id') for acc in second_company.get('bankAccounts', []) if acc.get('id')]

            if not selected_company_id:
                print_status("У второй компании в ответе API отсутствует поле 'companyId'.", False)
                return

            print(f"    Выбрана компания: '{second_company.get('companyName')}' (ID: {selected_company_id})")
            print(f"    Выбрано счетов для синхронизации: {len(selected_account_ids)}")
            if not selected_account_ids:
                print("[ПРЕДУПРЕЖДЕНИЕ] У выбранной компании нет счетов. Тест будет неполным, но продолжим.")

        except (IndexError, KeyError, TypeError) as e:
            print_status("Ошибка при разборе ответа от API на Шаге 3.", False, f"Детали: {e}")
            return

        # --- [ШАГ 4] Сохранение всех настроек ---
        print("\n--- [ШАГ 4] Сохранение всех настроек (ключ, выбор, расписание) ---")
        settings_payload = {
            "api_token": REAL_MODULBANK_TOKEN,
            "schedule_type": "daily",
            "sync_time": "13:30",
            "selected_company_ids": [selected_company_id],
            "selected_account_ids": selected_account_ids
        }

        resp_save = requests.post(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers,
                                  json=settings_payload)
        if not print_status("Запрос на сохранение настроек", resp_save.status_code == 200,
                            f"| Статус: {resp_save.status_code}, Ответ: {resp_save.text[:150]}..."):
            return

        # --- [ШАГ 5] Проверка результата в базе данных ---
        print("\n--- [ШАГ 5] Проверка сохраненных настроек в базе данных ---")
        db_conn.commit()

        saved_sources = get_tenant_sync_sources(db_conn, tenant_id)
        if not saved_sources:
            print_status("Проверка сохраненных источников", False, "Запись не найдена в БД.")
            return

        print(f"    Сохраненные в БД ID счетов: {saved_sources.get('accounts')}")

        is_ok = set(saved_sources.get('accounts', [])) == set(selected_account_ids)
        print_status("Проверка: сохраненные в БД счета соответствуют выбранным", is_ok)

        if is_ok:
            print("\n[SUCCESS] Тест пройден! Система правильно обработала выбор компании и сохранила нужные счета.")

    except Exception as e:
        print(f"\n[CRITICAL] В ходе теста произошла непредвиденная ошибка!", False, f"Детали: {e}")

    # finally:
    #     if db_conn:
    #         print("\n--- [Финал] Отключение интеграции ---")
    #         requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
    #         db_conn.close()

    print("\n>>> ТЕСТ ВЫБОРА КОМПАНИИ ЗАВЕРШЕН <<<")


if __name__ == "__main__":
    run_select_company_test()