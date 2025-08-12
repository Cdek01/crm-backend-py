# # test_custom_data_flow.py
# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ ---
# # BASE_URL = "http://127.0.0.1:8005"  # Укажите адрес вашего сервера
# BASE_URL = "http://89.111.169.47:8005"  # Укажите адрес вашего сервера если тестируете на сервере
#
# # ВАЖНО: Укажите здесь ваш токен, который вы добавили в .env
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # -----------------
#
# UNIQUE_ID = int(time.time())
#
#
# def print_status(ok, message):
#     """Выводит красивый статус операции."""
#     if ok:
#         print(f"✅ [SUCCESS] {message}")
#     else:
#         print(f"❌ [FAILURE] {message}")
#         exit(1)
#
#
# def run_custom_table_test():
#     """
#     Выполняет полный цикл тестирования записи в кастомную таблицу:
#     1. Регистрация и авторизация.
#     2. Создание кастомной таблицы 'vacancies' через /meta API.
#     3. Добавление в нее колонок 'title', 'salary', 'is_remote'.
#     4. Запись двух вакансий в эту таблицу через /data API.
#     5. Получение списка и проверка, что данные сохранились корректно.
#     """
#     headers = {}
#
#     try:
#         # --- ШАГ 1: АВТОРИЗАЦИЯ ---
#         print("-" * 50)
#         print("1. АВТОРИЗАЦИЯ")
#         user_email = f"custom_data_tester@example.com"
#         password = "password123"
#         reg_payload = {"email": user_email, "password": password, "registration_token": CORRECT_REGISTRATION_TOKEN}
#         requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#
#         auth_payload = {"username": user_email, "password": password}
#         token_response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
#         token_response.raise_for_status()
#         token = token_response.json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#         print_status(True, "Пользователь успешно авторизован.")
#
#         # --- ШАГ 2: СОЗДАНИЕ СТРУКТУРЫ ---
#         print("-" * 50)
#         print("2. СОЗДАНИЕ СТРУКТУРЫ ТАБЛИЦЫ 'vacancies'")
#
#         table_name = f"vacancies_{UNIQUE_ID}"
#         entity_payload = {"name": table_name, "display_name": "Вакансии"}
#         response = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=entity_payload)
#         response.raise_for_status()
#         entity_type_id = response.json()['id']
#         print(f" -> Создана таблица '{table_name}' с ID={entity_type_id}")
#
#         # Добавляем колонки
#         attributes_to_create = [
#             {"name": "title", "display_name": "Название вакансии", "value_type": "string"},
#             {"name": "salary", "display_name": "Зарплата", "value_type": "integer"},
#             {"name": "is_remote", "display_name": "Удаленка", "value_type": "boolean"},
#         ]
#         for attr_payload in attributes_to_create:
#             response = requests.post(f"{BASE_URL}/api/meta/entity-types/{entity_type_id}/attributes", headers=headers,
#                                      json=attr_payload)
#             response.raise_for_status()
#             print(f" -> Создана колонка '{attr_payload['name']}'")
#         print_status(True, "Структура таблицы успешно создана.")
#
#         # --- ШАГ 3: ЗАПИСЬ ДАННЫХ В КАСТОМНУЮ ТАБЛИЦУ ---
#         print("-" * 50)
#         print(f"3. ЗАПИСЬ ДАННЫХ В '{table_name}' (POST /api/data/{table_name})")
#
#         # Запись первой вакансии
#         vacancy1_data = {
#             "title": "Python Developer",
#             "salary": 200000,
#             "is_remote": True,
#             "phone_number": "+79990000001"  # Заполняем системное поле
#         }
#         response1 = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=vacancy1_data)
#         response1.raise_for_status()
#         print_status(response1.status_code == 201, f"Запись '{vacancy1_data['title']}' успешно создана.")
#
#         # Запись второй вакансии
#         vacancy2_data = {
#             "title": "Frontend Developer",
#             "salary": 180000,
#             "is_remote": False,
#         }
#         response2 = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=vacancy2_data)
#         response2.raise_for_status()
#         print_status(response2.status_code == 201, f"Запись '{vacancy2_data['title']}' успешно создана.")
#
#         # --- ШАГ 4: ПРОВЕРКА ЗАПИСАННЫХ ДАННЫХ ---
#         print("-" * 50)
#         print(f"4. ПРОВЕРКА ДАННЫХ (GET /api/data/{table_name})")
#
#         response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
#         response.raise_for_status()
#         all_vacancies = response.json()
#
#         print_status(len(all_vacancies) == 2, f"В таблице найдено {len(all_vacancies)} записи, как и ожидалось.")
#
#         # Ищем нашу первую вакансию в ответе
#         python_dev = next((v for v in all_vacancies if v.get("title") == "Python Developer"), None)
#
#         print_status(python_dev is not None, "Вакансия 'Python Developer' найдена в списке.")
#
#         if python_dev:
#             print_status(
#                 python_dev.get("salary") == vacancy1_data["salary"],
#                 "Поле 'salary' для Python Developer сохранено корректно."
#             )
#             print_status(
#                 python_dev.get("is_remote") == vacancy1_data["is_remote"],
#                 "Поле 'is_remote' для Python Developer сохранено корректно."
#             )
#             print_status(
#                 python_dev.get("phone_number") == vacancy1_data["phone_number"],
#                 "Системное поле 'phone_number' сохранено корректно."
#             )
#
#         print("\n🎉 Все тесты для записи и чтения из кастомной таблицы пройдены успешно!")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP.")
#         print(f"URL: {e.request.method} {e.request.url}")
#         print(f"Статус: {e.response.status_code}")
#         print(f"Ответ: {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
#
#
# if __name__ == "__main__":
#     run_custom_table_test()


# view_custom_data.py
import requests
import json

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8005"  # Укажите адрес вашего сервера

# --- ДАННЫЕ ДЛЯ АВТОРИЗАЦИИ ---
# Используйте email и пароль пользователя, который создал таблицу
USER_EMAIL = "custom1.com"  # <--- ЗАМЕНИТЕ НА СВОЙ EMAIL
USER_PASSWORD = "password123"

# --- ИМЯ КАСТОМНОЙ ТАБЛИЦЫ ---
# Замените на системное имя таблицы, которую хотите посмотреть
TABLE_NAME_TO_VIEW = "vacancies_1754478335"  # <--- ЗАМЕНИТЕ НА ИМЯ ВАШЕЙ ТАБЛИЦЫ


# ------------------------------------

def get_auth_token(email, password):
    """Получает токен авторизации."""
    print("1. Получение токена авторизации...")
    try:
        auth_payload = {"username": email, "password": password}
        response = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValueError("Токен не найден в ответе сервера.")
        print("   ✅ Токен успешно получен.")
        return token
    except Exception as e:
        print(f"   ❌ Не удалось получить токен: {e}")
        return None


def view_custom_table_data(token, table_name):
    """Запрашивает и выводит данные из кастомной таблицы."""
    print(f"\n2. Запрос данных из таблицы '{table_name}'...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)

        # Проверяем, не вернул ли сервер ошибку
        if response.status_code == 404:
            print(f"   ❌ Ошибка: Таблица с именем '{table_name}' не найдена (404 Not Found).")
            print("   -> Проверьте, что имя таблицы указано правильно.")
            return

        response.raise_for_status()  # Проверяем на другие HTTP ошибки (401, 500 и т.д.)

        data = response.json()

        print(f"   ✅ Успешно получено {len(data)} записей.")

        if not data:
            print("   -> Таблица пуста.")
            return

        print("\n--- Содержимое таблицы ---")
        # Красиво выводим каждую запись в формате JSON
        for i, record in enumerate(data, 1):
            print(f"\n--- Запись #{i} ---")
            print(json.dumps(record, indent=2, ensure_ascii=False))
        print("\n--------------------------")

    except requests.exceptions.HTTPError as e:
        print(f"   ❌ Ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"   ❌ Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":

        # 1. Получаем токен
        access_token = get_auth_token(USER_EMAIL, USER_PASSWORD)

        # 2. Если токен получен, запрашиваем данные
        if access_token:
            view_custom_table_data(access_token, TABLE_NAME_TO_VIEW)