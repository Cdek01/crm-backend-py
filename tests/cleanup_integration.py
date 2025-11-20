# tests/cleanup_integration.py
import requests
from integration_test import BASE_URL, USER_EMAIL, USER_PASSWORD, login


def cleanup():
    """Отключает интеграцию с Модульбанком."""
    print(">>> Запуск очистки интеграции с Модульбанком...")

    token = login(USER_EMAIL, USER_PASSWORD)
    if not token:
        print("[FAIL] Не удалось войти в систему для очистки.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(f"{BASE_URL}/api/integrations/modulbank/settings", headers=headers)
        response.raise_for_status()
        print(f"[OK] Запрос на отключение интеграции успешно отправлен. Статус: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Ошибка при отключении интеграции: {e}")


if __name__ == "__main__":
    cleanup()
