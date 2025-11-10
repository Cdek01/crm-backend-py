import requests
import json
import sys
from typing import Optional

# --- НАСТРОЙКИ ---
# Замените на URL вашего сервера
BASE_URL = "http://89.111.169.47:8005"
# Используйте email и пароль пользователя, от имени которого хотите сделать запрос
# Если это суперадминистратор, он увидит роли всех клиентов.
# Если обычный пользователь - только роли своего клиента.
EMAIL = "1@example.com"
PASSWORD = "string"


# -----------------


def print_header(title: str):
    """Печатает красивый заголовок в консоль."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def get_auth_token() -> Optional[str]:
    """Получает токен авторизации с сервера."""
    print_header("Этап 1: Авторизация")
    try:
        url = f"{BASE_URL}/api/auth/token"
        response = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})

        # Проверяем на ошибки (4xx, 5xx)
        response.raise_for_status()

        token = response.json().get("access_token")
        if not token:
            print("❌ Ошибка: Токен не найден в ответе сервера.")
            return None

        print("✅ Успешно получен токен доступа.")
        return token

    except requests.exceptions.RequestException as e:
        print(f"❌ Критическая ошибка при авторизации: {e}")
        if e.response is not None:
            print(f"   └─ Ответ сервера: {e.response.text}")
        return None


def get_detailed_roles(token: str):
    """Запрашивает детальный список ролей с их разрешениями."""
    print_header("Этап 2: Получение детального списка ролей (GET /api/roles/)")
    try:
        url = f"{BASE_URL}/api/roles/"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        roles_data = response.json()

        print("✅ Запрос успешно выполнен. Полученные роли и их права:")
        # Используем json.dumps для красивого вывода с отступами
        print(json.dumps(roles_data, indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при получении детального списка ролей: {e}")
        if e.response is not None:
            print(f"   └─ Ответ сервера: {e.response.text}")


def get_simple_roles_list(token: str):
    """Запрашивает простой список ролей (id, name)."""
    print_header("Этап 3: Получение простого списка ролей (GET /api/roles/simple-list)")
    try:
        url = f"{BASE_URL}/api/roles/simple-list"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        roles_data = response.json()

        print("✅ Запрос успешно выполнен. Получен простой список ролей:")
        print(json.dumps(roles_data, indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при получении простого списка ролей: {e}")
        if e.response is not None:
            print(f"   └─ Ответ сервера: {e.response.text}")


def main():
    """Главная функция для выполнения всех шагов."""
    auth_token = get_auth_token()

    if not auth_token:
        sys.exit(1)  # Завершаем скрипт, если авторизация не удалась

    # Выполняем запросы на получение ролей
    get_detailed_roles(auth_token)
    get_simple_roles_list(auth_token)


if __name__ == "__main__":
    main()