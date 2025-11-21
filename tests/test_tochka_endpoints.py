import requests
import json
import time
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"
# !!! ВАЖНО: Замените на ваш действующий токен от Точка Банка !!!
TEST_TOCHKA_TOKEN = 'eyJhbGciOiJSUzI1NiIsInRNzMyOTQ5ODg2NzYzNTY3ZTQzYTRjMyIsInN1YiI6IjQ4ZDU0ZTJkLWYyMzgtNDUwNy04OThlLWNlYTRhMzhlNTFjMSIsImN1c3RvbWVyX2NvZGUiOiIzMDMxMDgxNDQifQ.Dxn0lfJ8mzGZ665nhdQLE3clqFjVU_NcGcCgRnWY6T7TaWtUqeqMohXGUcEmBI9kA8FgzWXzGUl9R1BAXXLqmCg6mHreXMPoN3guuHjGAqpQnu0QmigUlA2oVvactGFSWGtLI1Jtzlu2vShC2lAdC5nX1VSoSgRLGFQWUjIXYUMjafTM2vVN3QicMhMYkCO0_qK_c6qHNpQ7NiuV_i5EMP2j7Vf7IHorHDJzXgZ5udX7SpjrvPLhsrVbLRZ7S4-3VVcwEApT64ih-HGcKARq8IPs3TUGZC-84QKpLM7efD4TgtjWPovbEhYUNrLL4wcy0teIdsbFVEnhCxywGNEA1frNlo_KUOYu32Q_P-F9hA34ApDPDaPlJ44l4EM4OajI2A2ruurebe1eFtApq3gtNLruiuHfAWrWNHmjD5OFXr8FLd1FM4ksQGuskrbfufP_7UG2Z4BGuAjODwTO7rCUq1OCA_sLuXnUDtd_FECr9S4i8egvSHe0CBPStZOCuwPd'


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


def run_tochka_integration_test():
    """
    Основной сценарий теста для эндпоинтов интеграции с Точка Банком.
    """
    print(">>> Тест: Проверка API-эндпоинтов для интеграции с Точка Банком <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    try:
        # --- [ШАГ 1] Начальная очистка ---
        print("\n--- [ШАГ 1] Начальная очистка настроек интеграции ---")
        resp_delete = requests.delete(f"{BASE_URL}/api/integrations/tochka/settings", headers=headers)
        print_status("Запрос на отключение старой интеграции", resp_delete.ok, f"| Статус: {resp_delete.status_code}")

        # --- [ШАГ 2] Проверка токена и получение счетов ---
        print("\n--- [ШАГ 2] Проверка токена и получение списка счетов ---")
        resp_validate = requests.post(
            f"{BASE_URL}/api/integrations/tochka/validate-token",
            headers=headers,
            json={"api_token": TEST_TOCHKA_TOKEN}
        )
        if not print_status("Запрос на валидацию токена", resp_validate.ok, f"| Статус: {resp_validate.status_code}"):
            print(f"    Ответ сервера: {resp_validate.text}")
            return

        # Извлекаем ID счетов из ответа для следующего шага
        companies_info = resp_validate.json()
        accounts_to_sync = []
        if companies_info and companies_info[0].get("bankAccounts"):
            # Для теста возьмем только первый счет
            first_account_id = companies_info[0]["bankAccounts"][0]["accountId"]
            accounts_to_sync.append(first_account_id)
            print(f"    [INFO] Найдены счета. Для теста будет использован счет: {first_account_id}")

        if not accounts_to_sync:
            print("[FAIL] Не удалось найти ни одного счета для теста. Прерываем.")
            return

        # --- [ШАГ 3] Сохранение настроек ---
        print("\n--- [ШАГ 3] Сохранение настроек (токен, счета и расписание) ---")
        sync_time_str = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")

        settings_payload = {
            "api_token": TEST_TOCHKA_TOKEN,
            "selected_account_ids": accounts_to_sync,  # <-- Передаем ID счета
            "schedule_type": "daily",
            "sync_time": sync_time_str,
        }
        resp_save = requests.post(f"{BASE_URL}/api/integrations/tochka/settings", headers=headers,
                                  json=settings_payload)

        if not print_status("Запрос на сохранение настроек", resp_save.ok, f"| Статус: {resp_save.status_code}"):
            print(f"    Ответ сервера: {resp_save.text}")
            return
        print(f"    Ответ: {resp_save.json().get('message')}")

        # --- [ШАГ 4] Проверка сохраненных настроек ---
        print("\n--- [ШАГ 4] Проверка сохраненных настроек через GET-запрос ---")
        time.sleep(1)  # Небольшая пауза на всякий случай
        resp_get = requests.get(f"{BASE_URL}/api/integrations/tochka/settings", headers=headers)
        if not print_status("Запрос на получение настроек", resp_get.ok, f"| Статус: {resp_get.status_code}"):
            return

        current_settings = resp_get.json()
        print(f"    Полученные настройки: {json.dumps(current_settings, indent=4)}")

        # Проводим детальную проверку
        is_active_ok = current_settings.get('is_active') is True
        schedule_ok = current_settings.get('schedule_type') == 'daily'
        time_ok = current_settings.get('sync_time', '').startswith(sync_time_str)
        accounts_ok = current_settings.get('selected_account_ids') == accounts_to_sync

        print_status("Проверка: интеграция активна", is_active_ok)
        print_status("Проверка: тип расписания 'daily'", schedule_ok)
        print_status(f"Проверка: время синхронизации '{sync_time_str}'", time_ok)
        print_status(f"Проверка: сохраненные счета {accounts_to_sync}", accounts_ok)

        if not (is_active_ok and schedule_ok and time_ok and accounts_ok):
            print("[FAIL] Сохраненные настройки не соответствуют отправленным!")

        # # --- [ШАГ 5] Финальная очистка (раскомментируйте, если нужно) ---
        # print("\n--- [ШАГ 5] Финальная очистка настроек ---")
        # resp_final_delete = requests.delete(f"{BASE_URL}/api/integrations/tochka/settings", headers=headers)
        # print_status("Запрос на финальное отключение интеграции", resp_final_delete.ok,
        #              f"| Статус: {resp_final_delete.status_code}")

    except Exception as e:
        print(f"\n[CRITICAL] В ходе теста произошла непредвиденная ошибка: {e}")

    print("\n>>> ТЕСТ ЭНДПОИНТОВ ЗАВЕРШЕН <<<")


if __name__ == "__main__":
    run_tochka_integration_test()