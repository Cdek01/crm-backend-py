# import requests
# import sys
# import json
# import time
# import pandas as pd
# import io
# from typing import Dict, Any, Optional
# from urllib.parse import quote_plus
#
# # --- НАСТРОЙКИ ---
# BASE_URL = "http://89.111.169.47:8005"  # Укажите правильный URL вашего сервера
# EMAIL = "1@example.com"
# PASSWORD = "string"
# # -----------------
#
# # --- Глобальные переменные ---
# test_failed = False
# UNIQUE_TABLE_NAME = f"export_test_{int(time.time())}"
# test_table_info = {}
#
#
# # --- Вспомогательные функции ---
# def print_status(ok: bool, message: str, data: Optional[Any] = None):
#     global test_failed
#     if ok:
#         print(f"✅ [OK] {message}")
#     else:
#         test_failed = True
#         print(f"❌ [FAIL] {message}")
#         if data:
#             try:
#                 print(f"  └─ Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
#             except (TypeError, json.JSONDecodeError):
#                 print(f"  └─ Ответ сервера: {data}")
#         print("")
#
#
# def print_header(title: str):
#     print("\n" + "=" * 80)
#     print(f" {title} ".center(80, "="))
#     print("=" * 80)
#
#
# def login() -> Optional[Dict[str, str]]:
#     print_header("Этап 0: Авторизация")
#     try:
#         url = f"{BASE_URL}/api/auth/token"
#         r = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})
#         r.raise_for_status()
#         token = r.json()["access_token"]
#         print_status(True, "Успешно получен токен доступа.")
#         return {'Authorization': f'Bearer {token}'}
#     except Exception as e:
#         response_text = getattr(e, 'response', 'N/A')
#         if hasattr(response_text, 'text'): response_text = response_text.text
#         print_status(False, f"Критическая ошибка при авторизации: {e}", response_text)
#         return None
#
#
# # --- Функции для подготовки и очистки ---
# def create_test_table(headers: Dict[str, str]) -> Optional[str]:
#     global test_table_info
#     print_header(f"Этап 1: Создание тестовой таблицы '{UNIQUE_TABLE_NAME}'")
#     try:
#         url = f"{BASE_URL}/api/meta/entity-types"
#         payload = {"name": UNIQUE_TABLE_NAME, "display_name": f"Тест экспорта {time.time()}"}
#         r = requests.post(url, headers=headers, json=payload)
#         r.raise_for_status()
#         table_id = r.json()["id"]
#         test_table_info = {"id": table_id, "name": UNIQUE_TABLE_NAME}
#         print_status(True, f"Таблица создана, ID: {table_id}")
#
#         columns = [
#             {"name": "product_name", "display_name": "Название товара", "value_type": "string"},
#             {"name": "quantity", "display_name": "Количество", "value_type": "integer"},
#             {"name": "price", "display_name": "Цена", "value_type": "float"},
#         ]
#         for col in columns:
#             url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
#             r = requests.post(url, headers=headers, json=col)
#             r.raise_for_status()
#             print_status(True, f"Колонка '{col['display_name']}' добавлена.")
#         return UNIQUE_TABLE_NAME
#     except Exception as e:
#         print_status(False, "Не удалось создать тестовую таблицу", getattr(e, 'response', 'N/A').text)
#         return None
#
#
# def populate_test_data(headers: Dict[str, str], table_name: str) -> Optional[Dict[str, Any]]:
#     print_header(f"Этап 2: Наполнение таблицы '{table_name}' данными")
#     try:
#         records_to_add = [
#             {"product_name": "Тестовый Товар А", "quantity": 15, "price": 99.90},
#             {"product_name": "Тестовый Товар Б", "quantity": 200, "price": 12.50},
#             {"product_name": "Товар для фильтра", "quantity": 1, "price": 1000.0},
#         ]
#         created_id = None
#         filter_value = "Товар для фильтра"
#
#         for record in records_to_add:
#             url = f"{BASE_URL}/api/data/{table_name}"
#             r = requests.post(url, headers=headers, json=record)
#             r.raise_for_status()
#             new_record_data = r.json()['data'][0]
#             print_status(True, f"Запись добавлена, ID: {new_record_data['id']}, Имя: {new_record_data['product_name']}")
#             if record["product_name"] == filter_value:
#                 created_id = new_record_data['id']
#
#         if created_id:
#             return {"id": created_id, "product_name": filter_value}
#         else:
#             print_status(False, "Не удалось получить ID записи для теста фильтрации.")
#             return None
#     except Exception as e:
#         print_status(False, "Не удалось наполнить таблицу данными", getattr(e, 'response', 'N/A').text)
#         return None
#
#
# def delete_test_table(headers: Dict[str, str]):
#     if not test_table_info: return
#     print_header(f"Этап 5: Очистка (удаление таблицы '{test_table_info['name']}')")
#     try:
#         url = f"{BASE_URL}/api/meta/entity-types/{test_table_info['id']}"
#         r = requests.delete(url, headers=headers)
#         if r.status_code == 204:
#             print_status(True, f"Тестовая таблица ID {test_table_info['id']} успешно удалена.")
#         else:
#             print_status(False, f"Не удалось удалить тестовую таблицу. Статус: {r.status_code}", r.text)
#     except Exception as e:
#         print_status(False, "Произошла ошибка при удалении тестовой таблицы", getattr(e, 'response', 'N/A'))
#
#
# # --- Тестовые функции ---
# def test_export(headers: Dict[str, str], table_name: str, format: str):
#     print_header(f"Тест: Экспорт таблицы '{table_name}' в формат {format.upper()}")
#     try:
#         url = f"{BASE_URL}/api/data/{table_name}/export?format={format}"
#         print(f"-> Запрос на URL: {url}")
#         r = requests.get(url, headers=headers)
#
#         if r.status_code != 200:
#             # Пытаемся декодировать JSON, если не получается - показываем текст
#             try:
#                 error_data = r.json()
#             except json.JSONDecodeError:
#                 error_data = r.text
#             print_status(False, f"Ожидался статус-код 200, получен {r.status_code}", error_data)
#             return
#
#         print_status(True, "Сервер вернул статус-код 200 OK.")
#
#         # ... остальные проверки ...
#         file_content = r.content
#         if not file_content:
#             print_status(False, "Тело ответа пустое, файл не получен.")
#             return
#
#         stream = io.BytesIO(file_content)
#         if format == "csv":
#             df = pd.read_csv(stream)
#         else:
#             df = pd.read_excel(stream, engine='openpyxl')
#
#         print_status(True, f"Файл успешно прочитан. Строк: {len(df)}, колонок: {len(df.columns)}.")
#         print("-> Превью данных:")
#         print(df.head())
#
#     except Exception as e:
#         print_status(False, f"Во время теста произошла ошибка: {e}", getattr(e, 'response', 'N/A'))
#
#
# def test_export_with_filter(headers: Dict[str, str], table_name: str, filter_data: Dict[str, Any]):
#     print_header(f"Тест: Экспорт с фильтром (product_name = '{filter_data['product_name']}')")
#     try:
#         filters_obj = [{"field": "product_name", "op": "eq", "value": filter_data['product_name']}]
#         filters_str = quote_plus(json.dumps(filters_obj))
#
#         url = f"{BASE_URL}/api/data/{table_name}/export?format=csv&filters={filters_str}"
#         print(f"-> Запрос на URL: {url}")
#         r = requests.get(url, headers=headers)
#         r.raise_for_status()
#
#         df = pd.read_csv(io.BytesIO(r.content))
#         if len(df) == 1:
#             print_status(True, f"Фильтр сработал. В файле найдена 1 запись с ID={df.iloc[0]['ID']}.")
#             if df.iloc[0]['ID'] != filter_data['id']:
#                 print_status(False, f"ID в файле ({df.iloc[0]['ID']}) не совпадает с ожидаемым ({filter_data['id']}).")
#         else:
#             print_status(False, f"Фильтр сработал некорректно. Ожидалась 1 запись, получено {len(df)}.", df.to_dict())
#
#     except Exception as e:
#         print_status(False, f"Во время теста с фильтром произошла ошибка: {e}", getattr(e, 'response', 'N/A'))
#
#
# def test_error_scenarios(headers: Dict[str, str], table_name: str):
#     print_header("Тест: Сценарии с ошибками")
#     try:
#         bad_table = "nonexistent_table_12345"
#         url = f"{BASE_URL}/api/data/{bad_table}/export?format=csv"
#         r = requests.get(url, headers=headers)
#         if r.status_code == 404:
#             print_status(True, "Сервер корректно вернул 404 Not Found для несуществующей таблицы.")
#         else:
#             print_status(False, f"Ожидался статус 404, но получен {r.status_code}", r.text)
#     except Exception as e:
#         print_status(False, f"Ошибка при тесте несуществующей таблицы: {e}")
#
#     try:
#         url = f"{BASE_URL}/api/data/{table_name}/export?format=pdf"
#         r = requests.get(url, headers=headers)
#         if r.status_code == 422:
#             print_status(True, "Сервер корректно вернул 422 Unprocessable Entity для неверного формата.")
#         else:
#             print_status(False, f"Ожидался статус 422, но получен {r.status_code}", r.text)
#     except Exception as e:
#         print_status(False, f"Ошибка при тесте неверного формата: {e}")
#
#
# # --- Главная функция ---
# def main():
#     auth_headers = login()
#     if not auth_headers: sys.exit(1)
#
#     try:
#         table_name = create_test_table(auth_headers)
#         if not table_name: sys.exit(1)
#
#         filter_data = populate_test_data(auth_headers, table_name)
#         if not filter_data: sys.exit(1)
#
#         print_header("Этап 3: Тестирование эндпоинта экспорта")
#         test_export(auth_headers, table_name, "csv")
#         test_export(auth_headers, table_name, "xlsx")
#
#         print_header("Этап 4: Тестирование фильтрации при экспорте")
#         test_export_with_filter(auth_headers, table_name, filter_data)
#
#         print_header("Этап 5: Тестирование обработки ошибок")
#         test_error_scenarios(auth_headers, table_name)
#     finally:
#         delete_test_table(auth_headers)
#
#     print_header("Итоги тестирования")
#     if not test_failed:
#         print("🎉 ✅ Все тесты функции экспорта успешно пройдены!")
#     else:
#         print("🚨 ❌ Во время тестирования были обнаружены ошибки.")
#         sys.exit(1)
#
#
# if __name__ == "__main__":
#     main()








from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())