# # test_registration_token.py
# import requests
# import time
#
# # --- НАСТРОЙКИ ---
# BASE_URL = "http://127.0.0.1:8005"
# # --- НАСТРОЙКИ ---
# # BASE_URL = "http://89.111.169.47:8005"
# # ВАЖНО: Укажите здесь тот же токен, что и в вашем .env файле
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # -----------------
#
# UNIQUE_ID = int(time.time())
#
#
# def print_status(ok, message):
#     """Выводит статус операции."""
#     if ok:
#         print(f"✅ [PASS] {message}")
#     else:
#         print(f"❌ [FAIL] {message}")
#         exit(1)
#
#
# def run_test():
#     print("-" * 50)
#     print("--- ТЕСТ 1: ПОПЫТКА РЕГИСТРАЦИИ С НЕВЕРНЫМ ТОКЕНОМ ---")
#     USER_EMAIL = "user@example.com"
#     USER_PASSWORD = "string"
#     payload_fail = {
#         "email": USER_EMAIL,
#         "password": USER_PASSWORD,
#         "full_name": "user",
#         "registration_token": "this-is-a-wrong-token"
#     }
#
#     response_fail = requests.post(f"{BASE_URL}/api/auth/register", json=payload_fail)
#
#     print(f"Отправлен запрос с токеном: '{payload_fail['registration_token']}'")
#     print(f"Сервер ответил со статусом: {response_fail.status_code}")
#     print(f"Тело ответа: {response_fail.text}")
#
#     print_status(
#         response_fail.status_code == 403,
#         "Сервер корректно отклонил запрос с неверным токеном (статус 403 Forbidden)."
#     )
#
#     print("-" * 50)
#     print("--- ТЕСТ 2: ПОПЫТКА РЕГИСТРАЦИИ С ВЕРНЫМ ТОКЕНОМ ---")
#
#     payload_success = {
#         "email": f"success_user_{UNIQUE_ID}@example.com",
#         "password": "password123",
#         "full_name": "Success User",
#         "registration_token": CORRECT_REGISTRATION_TOKEN
#     }
#
#     response_success = requests.post(f"{BASE_URL}/api/auth/register", json=payload_success)
#
#     print(f"Отправлен запрос с токеном: '{payload_success['registration_token']}'")
#     print(f"Сервер ответил со статусом: {response_success.status_code}")
#
#     print_status(
#         response_success.status_code == 201,
#         "Сервер успешно обработал запрос с верным токеном (статус 201 Created)."
#     )
#
#     print("-" * 50)
#     print("\n🎉 Все тесты для токена регистрации пройдены успешно!")
#
#
# if __name__ == "__main__":
#     run_test()








import requests
import time

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"   # "http://127.0.0.1:8005"
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"

def print_status(ok, message):
    if ok:
        print(f"✅ [PASS] {message}")
    else:
        print(f"❌ [FAIL] {message}"); exit(1)

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def register_and_login():
    unique_id = int(time.time())
    email = f"AntonShlips@example.com"
    password = "AntonShlips(1985)"
    reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}

if __name__ == "__main__":
    print_header("РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ")
    headers = register_and_login()
    print_status(True, f"Пользователь успешно зарегистрирован. Токен: {headers['Authorization'][:30]}...")