import requests
import json
import time
from datetime import datetime
from unittest.mock import patch

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8000"
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
    email = f"select_tester_{unique_id}@example.com"
    password = "password123"
    reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
                   "registration_token": CORRECT_REGISTRATION_TOKEN}
    requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
    auth_payload = {'username': email, 'password': password}
    token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def get_current_state(headers, table_name):
    """Получает текущий список записей и возвращает его."""
    response = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers)
    response.raise_for_status()
    return response.json()


def move_task(headers, table_name, current_state, task_to_move_id, after_task_id, before_task_id):
    """Эмулирует перетаскивание одной задачи."""
    after_pos = None
    if after_task_id:
        after_pos = next(item['position'] for item in current_state if item['id'] == after_task_id)

    before_pos = None
    if before_task_id:
        before_pos = next(item['position'] for item in current_state if item['id'] == before_task_id)

    payload = {
        "entity_id": task_to_move_id,
        "after_position": after_pos,
        "before_position": before_pos
    }

    url = f"{BASE_URL}/api/data/{table_name}/position"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    print(f" -> Перемещение ID {task_to_move_id} завершено. Новая позиция: {response.json().get('new_position')}")


def verify_order(state, expected_ids, test_name):
    """Проверяет, что порядок ID в `state` соответствует `expected_ids`."""
    actual_ids = [item['id'] for item in state]
    print(f" -> Ожидаемый порядок: {expected_ids}")
    print(f" -> Фактический порядок: {actual_ids}")
    print_status(actual_ids == expected_ids, test_name)


# --- ОСНОВНОЙ ТЕСТ ---
@patch('services.external_api_client.send_update_to_colleague')
# @patch('services.eav_service.external_api_client.send_update_to_colleague')
def run_full_ordering_test(mock_send_update):
    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
        headers = register_and_login()

        table_name = f"tasks_full_order_{int(time.time())}"
        table_config = {"name": table_name, "display_name": "Задачи (полный тест сортировки)"}
        table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']
        requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
                      json={"name": "title", "display_name": "Название", "value_type": "string"}).raise_for_status()

        # --- ШАГ 2: ПРОВЕРКА ДОБАВЛЕНИЯ В НАЧАЛО ---
        print_header("ШАГ 2: ПРОВЕРКА, ЧТО НОВЫЕ ЗАПИСИ ДОБАВЛЯЮТСЯ ВВЕРХ")

        # Создаем первую запись
        id_a = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={"title": "Задача А"}).json()[
            'id']
        state1 = get_current_state(headers, table_name)
        print(" -> Создана 'Задача А'. Текущий порядок:", [item['id'] for item in state1])
        print_status(state1[0]['id'] == id_a, "Первая запись на первом месте.")

        # Создаем вторую запись
        id_b = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json={"title": "Задача Б"}).json()[
            'id']
        state2 = get_current_state(headers, table_name)
        print(" -> Создана 'Задача Б'. Текущий порядок:", [item['id'] for item in state2])
        print_status(state2[0]['id'] == id_b, "Вторая (новая) запись теперь на первом месте.")
        print_status(state2[1]['id'] == id_a, "Первая запись сдвинулась на второе место.")

        # --- ШАГ 3: ПРОВЕРКА DRAG-N-DROP И УВЕДОМЛЕНИЯ ---
        print_header("ШАГ 3: ПРОВЕРКА DRAG-N-DROP И ОТПРАВКИ УВЕДОМЛЕНИЯ")

        # Перемещаем 'Задачу Б' (которая сейчас первая) в конец, после 'Задачи А'
        print("\n -> Перемещаем 'Задачу Б' в конец...")
        move_task(headers, table_name, state2, task_to_move_id=id_b, after_task_id=id_a, before_task_id=None)

        # Проверяем, что порядок на сервере изменился
        state3 = get_current_state(headers, table_name)
        expected_order = [id_a, id_b]
        verify_order(state3, expected_order, "Порядок 'А, Б' успешно сохранен.")

        # Проверяем, что уведомление НЕ было отправлено, так как это системное изменение
        # (Предполагаем, что вы НЕ хотите уведомлять коллегу о смене порядка)
        # Если хотите, логику нужно будет добавить в `set_entity_order`.
        try:
            mock_send_update.assert_not_called()
            print_status(True, "Уведомление НЕ было отправлено при смене порядка (это правильно).")
        except AssertionError:
            print_status(False, "ОШИБКА: Уведомление было отправлено при смене порядка.")

        # --- ШАГ 4: ПРОВЕРКА УВЕДОМЛЕНИЯ ПРИ ОБНОВЛЕНИИ ДАННЫХ ---
        print_header("ШАГ 4: ПРОВЕРКА УВЕДОМЛЕНИЯ ПРИ ОБНОВЛЕНИИ ДАННЫХ")

        # Сбрасываем мок
        mock_send_update.reset_mock()

        # Обновляем данные в строке
        print("\n -> Обновляем 'Задачу А'...")
        update_payload = {"title": "Задача А (обновлено)"}
        requests.put(f"{BASE_URL}/api/data/{table_name}/{id_a}", headers=headers,
                     json=update_payload).raise_for_status()

        # Даем Celery немного времени (в реальном приложении это может быть дольше)
        time.sleep(1)

        # Проверяем, что уведомление было вызвано
        try:
            mock_send_update.assert_called_once()
            print_status(True, "Уведомление было отправлено при обновлении данных.")
            # Можно проверить и аргументы вызова
            call_args, call_kwargs = mock_send_update.call_args
            print(f"   -> Аргументы вызова: {call_kwargs}")
            print_status(
                call_kwargs.get('event_type') == 'update' and call_kwargs.get('entity_id') == id_a,
                "Уведомление отправлено с правильными параметрами."
            )
        except AssertionError:
            print_status(False, "ОШИБКА: Уведомление НЕ было отправлено при обновлении данных.")

        print("\n" + "=" * 60)
        print("🎉🎉🎉 ПОЛНЫЙ ТЕСТ СОРТИРОВКИ И УВЕДОМЛЕНИЙ ПРОЙДЕН! 🎉🎉🎉")

    except Exception as e:
        print()



if __name__ == "__main__":
    run_full_ordering_test()