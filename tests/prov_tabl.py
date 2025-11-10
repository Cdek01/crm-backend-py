
import requests
import sys

# --- НАСТРОЙКИ ---
# URL вашего сервера
BASE_URL = "http://89.111.169.47:8005"
# Данные для авторизации
EMAIL = "1@example.com"
PASSWORD = "string"

# --- ВАЖНО: Укажите системное имя таблицы, которую хотите проверить ---
TABLE_NAME = "roadmap_1762774095"  # <-- ЗАМЕНИТЕ НА ИМЯ ВАШЕЙ ТАБЛИЦЫ


# ---------------------------------------------------------------------


def main():
    """
    Авторизуется, запрашивает данные из таблицы и выводит общее количество строк.
    """
    print("=" * 60)
    print(f"Запрашиваем количество строк в таблице: '{TABLE_NAME}'")
    print("=" * 60)

    # 1. Авторизация
    try:
        auth_url = f"{BASE_URL}/api/auth/token"
        response = requests.post(auth_url, data={'username': EMAIL, 'password': PASSWORD})
        response.raise_for_status()
        token = response.json().get("access_token")
        print("✅ Авторизация прошла успешно.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка авторизации: {e}")
        sys.exit(1)

    # 2. Запрос данных из таблицы
    try:
        # Мы запрашиваем всего 1 запись (limit=1), так как нам не нужны сами данные,
        # а только общее количество, которое сервер вернет в поле `total`.
        # Это очень быстрый и эффективный запрос.
        data_url = f"{BASE_URL}/api/data/{TABLE_NAME}?limit=1"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(data_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        total_rows = data.get("total")

        if total_rows is not None:
            print("\n" + "*" * 60)
            print(f"  В таблице '{TABLE_NAME}' найдено строк: {total_rows}")
            print("*" * 60)
        else:
            print("❌ Ошибка: Сервер не вернул поле 'total' в ответе.")
            print(f"   └─ Ответ сервера: {data}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе данных из таблицы: {e}")
        if e.response is not None:
            print(f"   └─ Ответ сервера (статус {e.response.status_code}): {e.response.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()