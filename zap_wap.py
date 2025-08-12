import requests
import json
import time

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---

# BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
BASE_URL = "http://89.111.169.47:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера

# Секретный токен для регистрации новых пользователей
CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"

# --- ДАННЫЕ ДЛЯ ОТПРАВКИ РЕАЛЬНОГО SMS ---

# ВАЖНО: Укажите ваш РЕАЛЬНЫЙ номер телефона в международном формате (начиная с 7)
REAL_PHONE_NUMBER = "79952116323"

# Текст сообщения, который будет отправлен
MESSAGE_TO_SEND = f"Проверка API {time.strftime('%H:%M:%S')}. Если вы получили это сообщение, все работает."

# Системное имя для таблицы, где будут храниться логи отправки
SMS_LOG_TABLE_NAME = "sms_sending_log"

# ----------------------------------------------------

def print_status(ok, message):
    if ok: print(f"✅ [SUCCESS] {message}")
    else: print(f"❌ [FAILURE] {message}"); exit(1)

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

# --- Основная функция ---

def send_real_sms():
    try:
        # --- ШАГ 1: АВТОРИЗАЦИЯ И ПОДГОТОВКА СРЕДЫ ---
        print_header("ШАГ 1: ПОДГОТОВКА")

        # 1.1. Регистрация или вход
        unique_id = int(time.time())
        email = f"real_sms_sender_{unique_id}@example.com"
        password = "password123"
        reg_payload = {"email": email, "password": password, "full_name": "Real SMS Sender", "registration_token": CORRECT_REGISTRATION_TOKEN}
        requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
        auth_payload = {'username': email, 'password': password}
        token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print(f" -> Авторизация прошла успешно.")

        # 1.2. Проверка и создание таблицы для логов
        meta_response = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
        existing_tables = {t['name'] for t in meta_response.json()}
        if SMS_LOG_TABLE_NAME not in existing_tables:
            print(f" -> Таблица '{SMS_LOG_TABLE_NAME}' не найдена, создаем...")
            table_config = {"name": SMS_LOG_TABLE_NAME, "display_name": "Логи отправки SMS"}
            requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).raise_for_status()
            print(f" -> Таблица успешно создана.")
        else:
            print(f" -> Таблица '{SMS_LOG_TABLE_NAME}' уже существует.")

        # --- ШАГ 2: СОЗДАНИЕ ЗАПИСИ ДЛЯ ОТПРАВКИ ---
        print_header("ШАГ 2: СОЗДАНИЕ ЗАПИСИ И ЗАПУСК ОТПРАВКИ")

        payload = {
            "phone_number": REAL_PHONE_NUMBER,
            "message_text": MESSAGE_TO_SEND,
        }
        create_response = requests.post(f"{BASE_URL}/api/data/{SMS_LOG_TABLE_NAME}", headers=headers, json=payload)
        create_response.raise_for_status()
        entity_id = create_response.json()['id']
        print(f" -> Создана запись для отправки с ID: {entity_id}")

        # --- ШАГ 3: ЗАПУСК ТРИГГЕРА ---
        update_url = f"{BASE_URL}/api/data/{SMS_LOG_TABLE_NAME}/{entity_id}"
        trigger_response = requests.put(update_url, headers=headers, json={"send_sms_trigger": True})
        trigger_response.raise_for_status()

        initial_status = trigger_response.json().get('sms_status')
        print_status(
            initial_status == 'pending',
            f" -> Триггер успешно запущен. Статус записи: '{initial_status}'."
        )

        # --- ШАГ 4: МОНИТОРИНГ СТАТУСА ---
        print_header("ШАГ 4: МОНИТОРИНГ")

        for i in range(10): # Проверяем 10 раз с интервалом 3 секунды (всего 30 секунд)
            print(f" -> Попытка {i+1}/10: Проверяем статус...")
            time.sleep(3)

            status_response = requests.get(update_url, headers=headers)
            current_status = status_response.json().get('sms_status')

            if current_status != 'pending':
                print(f" -> Статус изменился на '{current_status}'!")

                if current_status == 'sent':
                    print_status(True, "Бэкенд сообщает, что SMS успешно отправлен.")
                elif current_status == 'error':
                    last_error = status_response.json().get('sms_last_error')
                    print_status(False, f"Бэкенд сообщает об ошибке отправки: {last_error}")
                else:
                    print_status(False, f"Неизвестный финальный статус: {current_status}")

                return # Завершаем скрипт

        print_status(False, "Статус не изменился с 'pending' за 30 секунд. Проверьте логи Celery воркера.")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP.")
        print(f"URL: {e.request.method} {e.request.url}")
        print(f"Статус: {e.response.status_code}")
        print(f"Ответ: {e.response.text}")
    except Exception as e:
        print(f"\n❌ ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")

if __name__ == "__main__":
    send_real_sms()