import requests
import json
import time

# --- КОНФИГУРАЦИЯ ---
BASE_URL = "http://89.111.169.47:8005"
USER_EMAIL = "AntonShlips@example.com"
USER_PASSWORD = "AntonShlips(1985)"


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


def run_ai_dashboard_test():
    """
    Тестирует асинхронную генерацию AI-сводки для дашборда.
    """
    print(">>> Тест: Проверка асинхронной генерации AI-сводки <<<")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}
    task_id = None

    try:
        # --- [ШАГ 1] Запуск задачи на генерацию ---
        print("\n--- [ШАГ 1] Запуск задачи на генерацию AI-сводки ---")
        resp_start = requests.post(f"{BASE_URL}/api/dashboards/summary/generate", headers=headers)

        if not print_status("Запрос на запуск задачи", resp_start.status_code == 202,
                            f"| Статус: {resp_start.status_code}"):
            print(f"    Ответ сервера: {resp_start.text}")
            return

        task_id = resp_start.json().get("task_id")
        if not task_id:
            print("[FAIL] Сервер не вернул task_id в ответе.")
            return

        print(f"    [INFO] Задача успешно запущена. Task ID: {task_id}")

        # --- [ШАГ 2] Ожидание результата выполнения задачи (Polling) ---
        print("\n--- [ШАГ 2] Ожидание результата выполнения задачи ---")

        start_time = time.time()
        max_wait_time = 90  # Максимальное время ожидания в секундах (AI может отвечать долго)

        while True:
            # Проверка на таймаут
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                print_status("Проверка результата", False, "| Причина: Таймаут ожидания.")
                return

            # Запрос статуса
            resp_status = requests.get(f"{BASE_URL}/api/dashboards/summary/status/{task_id}", headers=headers)
            if not resp_status.ok:
                print_status("Запрос статуса задачи", False,
                             f"| Статус: {resp_status.status_code}, Ответ: {resp_status.text}")
                return

            status_data = resp_status.json()
            current_status = status_data.get("status")

            print(f"    Проверка... Текущий статус: {current_status} (Прошло {int(elapsed_time)} сек.)")

            if current_status == "SUCCESS":
                print_status("Задача успешно выполнена!", True)
                print("\n--- [РЕЗУЛЬТАТ] ---")
                print(status_data.get("result"))
                print("--------------------")
                break

            if current_status == "FAILURE":
                print_status("Задача завершилась с ошибкой!", False)
                print("\n--- [ОШИБКА] ---")
                print(status_data.get("result"))
                print("------------------")
                break

            # Ждем перед следующей проверкой
            time.sleep(3)

    except Exception as e:
        print(f"\n[CRITICAL] В ходе теста произошла непредвиденная ошибка: {e}")

    print("\n>>> ТЕСТ ГЕНЕРАЦИИ AI-СВОДКИ ЗАВЕРШЕН <<<")


if __name__ == "__main__":
    run_ai_dashboard_test()