import requests
import json
import time  # <-- Добавьте этот импорт, он пригодился в Шаге 4

# --- ИСПРАВЛЕНИЕ ЗДЕСЬ: Добавляем импорт timedelta ---
from datetime import datetime, timedelta

# --- КОНЕЦ ИСПРАВЛЕНИЯ ---


# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"
TEST_BEELINE_TOKEN = "f0744ced-44e3-4d88-9ec7-f7823d83d634"


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


def run_beeline_integration_test():
    """
    Основной сценарий теста для эндпоинтов интеграции с Билайн.
    """
    print(">>> Тест: Проверка API-эндпоинтов для интеграции с Билайн <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    try:
        # --- [ШАГ 1] Начальная очистка ---
        print("\n--- [ШАГ 1] Начальная очистка настроек интеграции ---")
        resp_delete = requests.delete(f"{BASE_URL}/api/integrations/beeline/settings", headers=headers)
        print_status("Запрос на отключение старой интеграции", resp_delete.ok, f"| Статус: {resp_delete.status_code}")

        # --- [ШАГ 2] Проверка токена ---
        print("\n--- [ШАГ 2] Проверка валидности токена Билайн ---")
        resp_validate = requests.post(
            f"{BASE_URL}/api/integrations/beeline/validate-token",
            headers=headers,
            json={"api_token": TEST_BEELINE_TOKEN}
        )
        print_status("Запрос на валидацию токена", resp_validate.ok,
                     f"| Статус: {resp_validate.status_code}, Ответ: {resp_validate.text}")
        if not resp_validate.ok:
            return

        # --- [ШАГ 3] Сохранение настроек ---
        print("\n--- [ШАГ 3] Сохранение настроек (токен и расписание) ---")
        sync_time_str = (datetime.now() + timedelta(minutes=3)).strftime("%H:%M")

        settings_payload = {
            "api_token": TEST_BEELINE_TOKEN,
            "schedule_type": "daily",
            "sync_time": sync_time_str,
        }
        resp_save = requests.post(f"{BASE_URL}/api/integrations/beeline/settings", headers=headers,
                                  json=settings_payload)
        print_status("Запрос на сохранение настроек", resp_save.ok,
                     f"| Статус: {resp_save.status_code}, Ответ: {resp_save.json().get('message')}")
        if not resp_save.ok:
            return

        # --- [ШАГ 4] Проверка сохраненных настроек ---
        print("\n--- [ШАГ 4] Проверка сохраненных настроек через GET-запрос ---")
        time.sleep(1)
        resp_get = requests.get(f"{BASE_URL}/api/integrations/beeline/settings", headers=headers)
        if not print_status("Запрос на получение настроек", resp_get.ok, f"| Статус: {resp_get.status_code}"):
            return

        current_settings = resp_get.json()
        print(f"    Полученные настройки: {current_settings}")

        is_active_ok = current_settings.get('is_active') is True
        schedule_ok = current_settings.get('schedule_type') == 'daily'
        # Сравниваем только часы и минуты, т.к. секунды могут отличаться
        time_ok = current_settings.get('sync_time', '').startswith(sync_time_str)

        print_status("Проверка: интеграция активна", is_active_ok)
        print_status("Проверка: тип расписания 'daily'", schedule_ok)
        print_status(f"Проверка: время синхронизации '{sync_time_str}'", time_ok)

        if not (is_active_ok and schedule_ok and time_ok):
            print("[FAIL] Сохраненные настройки не соответствуют отправленным!")

        # # --- [ШАГ 5] Финальная очистка ---
        # print("\n--- [ШАГ 5] Финальная очистка настроек ---")
        # resp_final_delete = requests.delete(f"{BASE_URL}/api/integrations/beeline/settings", headers=headers)
        # print_status("Запрос на финальное отключение интеграции", resp_final_delete.ok,
        #              f"| Статус: {resp_final_delete.status_code}")

    except Exception as e:
        print(f"\n[CRITICAL] В ходе теста произошла непредвиденная ошибка: {e}")

    print("\n>>> ТЕСТ ЭНДПОИНТОВ ЗАВЕРШЕН <<<")


if __name__ == "__main__":
    run_beeline_integration_test()