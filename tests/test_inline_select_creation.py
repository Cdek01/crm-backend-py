# # # # -*- coding: utf-8 -*-
# # #
# # #
# # #
# # # # import requests
# # # # import json
# # # # import time
# # # #
# # # # # --- НАСТРОЙКИ ---
# # # # BASE_URL = "http://127.0.0.1:8000"
# # # # # BASE_URL = "http://89.111.169.47:8005"
# # # #
# # # # CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
# # # #
# # # #
# # # # def print_status(ok, message):
# # # #     if ok:
# # # #         print(f"✅ [PASS] {message}")
# # # #     else:
# # # #         print(f"❌ [FAIL] {message}"); exit(1)
# # # # def print_header(title):
# # # #     print("\n" + "=" * 60)
# # # #     print(f" {title} ".center(60, "="))
# # # #     print("=" * 60)
# # # #
# # # # def register_and_login():
# # # #     email = f"976@example.com"
# # # #     password = "sdsgsgbsdfbvsdf"
# # # #     reg_payload = {"email": email, "password": password, "full_name": "Select Tester",
# # # #                    "registration_token": CORRECT_REGISTRATION_TOKEN}
# # # #     requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
# # # #     auth_payload = {'username': email, 'password': password}
# # # #     token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
# # # #     return {'Authorization': f'Bearer {token}'}
# # # #
# # # #
# # # # def run_text_select_test():
# # # #     try:
# # # #         # --- ШАГ 1: ПОДГОТОВКА ---
# # # #         print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
# # # #         headers = register_and_login()
# # # #
# # # #         table_name = f"requests_{int(time.time())}"
# # # #         table_config = {"name": table_name, "display_name": "Заявки (text select)"}
# # # #         table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']
# # # #
# # # #         options_to_create = ["Техническая поддержка", "Вопрос по оплате", "Предложение"]
# # # #         attribute_payload = {
# # # #             "name": "request_type",
# # # #             "display_name": "Тип заявки",
# # # #             "value_type": "select",
# # # #             "list_items": options_to_create
# # # #         }
# # # #         requests.post(f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes", headers=headers,
# # # #                       json=attribute_payload).raise_for_status()
# # # #         print_status(True, f"Создана таблица '{table_name}' с колонкой-списком.")
# # # #
# # # #         # --- ШАГ 2: СОЗДАНИЕ И ПРОВЕРКА ---
# # # #         print_header("ШАГ 2: СОЗДАНИЕ ЗАПИСИ С ТЕКСТОВЫМ ЗНАЧЕНИЕМ")
# # # #
# # # #         payload1 = {"request_type": "Техническая поддержка"}
# # # #         record_id_1 = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload1).json()[0]['id']
# # # #
# # # #         payload2 = {"request_type": "Вопрос по оплате"}
# # # #         requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=payload2).raise_for_status()
# # # #
# # # #         record_1_data = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_id_1}", headers=headers).json()
# # # #
# # # #         print(f" -> Создана запись #{record_id_1}. Полученное значение: '{record_1_data.get('request_type')}'")
# # # #         print_status(record_1_data.get('request_type') == "Техническая поддержка", "Значение сохранилось корректно.")
# # # #
# # # #         # --- ШАГ 3: ОБНОВЛЕНИЕ ---
# # # #         print_header("ШАГ 3: ОБНОВЛЕНИЕ ЗАПИСИ")
# # # #
# # # #         update_payload = {"request_type": "Предложение"}
# # # #         requests.put(f"{BASE_URL}/api/data/{table_name}/{record_id_1}", headers=headers,
# # # #                      json=update_payload).raise_for_status()
# # # #
# # # #         updated_record_data = requests.get(f"{BASE_URL}/api/data/{table_name}/{record_id_1}", headers=headers).json()
# # # #         print(f" -> Запись #{record_id_1} обновлена. Новое значение: '{updated_record_data.get('request_type')}'")
# # # #         print_status(updated_record_data.get('request_type') == "Предложение", "Значение успешно обновлено.")
# # # #
# # # #         # --- ШАГ 4: ПРОВЕРКА ВАЛИДАЦИИ ---
# # # #         print_header("ШАГ 4: ПРОВЕРКА ВАЛИДАЦИИ (НЕГАТИВНЫЙ ТЕСТ)")
# # # #
# # # #         invalid_payload = {"request_type": "Спам"}
# # # #         invalid_resp = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=invalid_payload)
# # # #
# # # #         print(f" -> Попытка создать запись со значением 'Спам'. Статус ответа: {invalid_resp.status_code}")
# # # #         print(f" -> Тело ответа: {invalid_resp.text}")
# # # #         print_status(
# # # #             invalid_resp.status_code == 400,
# # # #             "Сервер корректно отклонил запрос с недопустимым значением (статус 400)."
# # # #         )
# # # #
# # # #         # --- ШАГ 5: ПРОВЕРКА ФИЛЬТРАЦИИ ---
# # # #         print_header("ШАГ 5: ПРОВЕРКА ФИЛЬТРАЦИИ ПО ТЕКСТУ")
# # # #
# # # #         print("\n -> Поиск по новому значению 'Предложение' (ожидается 1)")
# # # #         filters1 = [{"field": "request_type", "value": "Предложение"}]
# # # #         resp1 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
# # # #                              params={"filters": json.dumps(filters1)}).json()
# # # #         print_status(len(resp1) == 1, f"Найдено {len(resp1)} записей.")
# # # #
# # # #         print("\n -> Поиск по старому значению 'Техническая поддержка' (ожидается 0)")
# # # #         filters2 = [{"field": "request_type", "value": "Техническая поддержка"}]
# # # #         resp2 = requests.get(f"{BASE_URL}/api/data/{table_name}", headers=headers,
# # # #                              params={"filters": json.dumps(filters2)}).json()
# # # #         print_status(len(resp2) == 0, f"Найдено {len(resp2)} записей.")
# # # #
# # # #         print("\n" + "=" * 60)
# # # #         print("🎉🎉🎉 ТЕСТ ВЫПАДАЮЩИХ СПИСКОВ С ТЕКСТОМ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
# # # #
# # # #     except requests.exceptions.HTTPError as e:
# # # #         print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
# # # #     except Exception as e:
# # # #         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
# # # #
# # # #
# # # # # ... (вставьте сюда `register_and_login`, `print_status`, `print_header`)
# # # #
# # # # if __name__ == "__main__":
# # # #     run_text_select_test()
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # #
# # # # # def run_inline_select_test():
# # # # #     try:
# # # # #         # --- ШАГ 1: ПОДГОТОВКА ---
# # # # #         print_header("ПОДГОТОВКА: АВТОРИЗАЦИЯ И СОЗДАНИЕ ТАБЛИЦЫ")
# # # # #         headers = register_and_login()
# # # # #
# # # # #         table_name = f"tasks_inline_select_{int(time.time())}"
# # # # #         table_config = {"name": table_name, "display_name": "Задачи (inline select тест)"}
# # # # #         table_id = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_config).json()['id']
# # # # #
# # # # #         print_status(True, f"Создана тестовая таблица '{table_name}' с ID: {table_id}")
# # # # #
# # # # #         # --- ШАГ 2: СОЗДАНИЕ КОЛОНКИ-СПИСКА ОДНИМ ЗАПРОСОМ ---
# # # # #         print_header("ШАГ 2: СОЗДАНИЕ КОЛОНКИ С ОПЦИЯМИ")
# # # # #
# # # # #         options_to_create = ["To Do", "In Progress", "Done"]
# # # # #         attribute_payload = {
# # # # #             "name": "task_status",
# # # # #             "display_name": "Статус",
# # # # #             "value_type": "select",
# # # # #             "list_items": options_to_create
# # # # #         }
# # # # #
# # # # #         url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
# # # # #         create_attr_response = requests.post(url, headers=headers, json=attribute_payload)
# # # # #         create_attr_response.raise_for_status()
# # # # #
# # # # #         created_attribute = create_attr_response.json()
# # # # #         print_status(True, f"Запрос на создание колонки и списка прошел успешно.{created_attribute}")
# # # # #
# # # # #         # --- ШАГ 3: ПРОВЕРКА СТРУКТУРЫ КОЛОНКИ ---
# # # # #         print_header("ШАГ 3: ПРОВЕРКА СОЗДАННОЙ КОЛОНКИ")
# # # # #
# # # # #         # Получаем полную структуру таблицы
# # # # #         table_details = requests.get(f"{BASE_URL}/api/meta/entity-types/{table_id}", headers=headers).json()
# # # # #
# # # # #         # Находим наш атрибут
# # # # #         status_attribute = next((attr for attr in table_details['attributes'] if attr['name'] == 'task_status'), None)
# # # # #
# # # # #         print_status(status_attribute is not None, "Колонка 'task_status' найдена в структуре таблицы.")
# # # # #
# # # # #         # Проверяем, что ID списка был создан и присвоен
# # # # #         select_list_id = status_attribute.get('select_list_id')
# # # # #         print(f" -> ID связанного списка: {select_list_id}")
# # # # #         print_status(
# # # # #             select_list_id is not None and isinstance(select_list_id, int),
# # # # #             "Колонка корректно связана со списком опций (select_list_id установлен)."
# # # # #         )
# # # # #
# # # # #         # --- ШАГ 4: ПРОВЕРКА СОДЕРЖИМОГО СПИСКА ---
# # # # #         print_header("ШАГ 4: ПРОВЕРКА АВТОМАТИЧЕСКИ СОЗДАННОГО СПИСКА ОПЦИЙ")
# # # # #
# # # # #         list_details_url = f"{BASE_URL}/api/meta/select-lists/{select_list_id}"
# # # # #         list_details_response = requests.get(list_details_url, headers=headers)
# # # # #         list_details_response.raise_for_status()
# # # # #         list_data = list_details_response.json()
# # # # #
# # # # #         print(f" -> Получены опции для списка ID={select_list_id}: {list_data}")
# # # # #
# # # # #         # Проверяем количество
# # # # #         print_status(
# # # # #             len(list_data.get('options', [])) == len(options_to_create),
# # # # #             f"Создано корректное количество опций ({len(options_to_create)})."
# # # # #         )
# # # # #
# # # # #         # Проверяем содержимое
# # # # #         option_values = {opt['value'] for opt in list_data.get('options', [])}
# # # # #         print_status(
# # # # #             option_values == set(options_to_create),
# # # # #             "Содержимое опций совпадает с переданным в `list_items`."
# # # # #         )
# # # # #
# # # # #         print("\n" + "=" * 60)
# # # # #         print("🎉🎉🎉 ТЕСТ АВТОСОЗДАНИЯ СПИСКОВ ПРОЙДЕН УСПЕШНО! 🎉🎉🎉")
# # # # #
# # # # #     except requests.exceptions.HTTPError as e:
# # # # #         print(f"\n❌ ОШИБКА HTTP: {e.response.status_code} - {e.response.text}")
# # # # #     except Exception as e:
# # # # #         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
# # # # #
# # # # #
# # # # # # ... (вставьте сюда `register_and_login`, `print_status`, `print_header`)
# # # # #
# # # # # if __name__ == "__main__":
# # # # #     run_inline_select_test()
# # #
# # # TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYW5pa2JlbGF2aW4yMDA2QGdtYWlsLmNvbSIsImV4cCI6MjA3NTcwNTExNH0.JXxPMrye8Vigv684SmBMF6uqt6fxd9WHajwM3j8Jj8c"
# # #
# # #
# # #
# # #
# # #
# # # import json
# # # import requests
# # #
# # #
# # # def update_crm_data(payload: dict, entity_type_name: str, api_token: str):
# # #     """
# # #     Отправка POST запроса с JSON.
# # #     Работает на Python 3.7 и поддерживает кириллицу.
# # #     """
# # #     BASE_URL = f"http://89.111.169.47:8005/api/data/{entity_type_name}"
# # #
# # #     # Заголовки должны быть ASCII
# # #     headers = {
# # #         "Accept": "application/json",
# # #         "Content-Type": "application/json",  # UTF-8 для JSON
# # #         "Authorization": f"Bearer {api_token}"  # токен должен быть ASCII
# # #     }
# # #
# # #     try:
# # #         # Используем json=payload, чтобы requests сам сериализовал JSON в UTF-8
# # #         response = requests.post(BASE_URL, json=payload, headers=headers)
# # #         print(f"Статус ответа: {response.status_code}")
# # #         print(f"Текст ответа: {response.text}")
# # #         response.raise_for_status()
# # #     except requests.exceptions.RequestException as e:
# # #         print("Ошибка запроса:", e)
# # #         return None
# # #
# # #     # Обрабатываем ответ сервера
# # #     try:
# # #         return response.json()
# # #     except ValueError:
# # #         # JSON декодировать не удалось, выводим текст
# # #         print("Ответ сервера не является JSON, возвращаем текст")
# # #         return response.text
# # #
# # #
# # # if __name__ == "__main__":
# # #     API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYW5pa2JlbGF2aW4yMDA2QGdtYWlsLmNvbSIsImV4cCI6MjA3NTcwNTExNH0.JXxPMrye8Vigv684SmBMF6uqt6fxd9WHajwM3j8Jj8c"
# # #
# # #     payload = {
# # #         # --- string ---
# # #         "naimenovanie_str": "«Фри Моушн»",
# # #         "nds_str": "",
# # #         "dogovory_str": "ИМ-РФ-О9Р-5",
# # #         "inn_str": "7704818042",
# # #         "deyatelnost_str": "Производство кинофильмов, видеофильмов и телевизионных программ",
# # #         "fio_initsiatora_str": "Шлипс Антон Александрович",
# # #         "adres_str": "",
# # #         "identifikator_edo_str": "2BM-7704818042-770401001-201508230326178080771",
# # #         "nomer_telefona_str": "79033474107",
# # #         "el_pochtu_str": "info@kvartirniki.com",
# # #         "sayty_v_ek5_str": "kvartirniki.com",
# # #         "status_sayta_str": "301",
# # #         "vyruchka_za_proshlyy_god_str": "280928",
# # #         "kategoriya_tovarov_str": "билеты",
# # #         "storona_dogovora_str": "ИП Шлипс Антон Александрович",
# # #         "etapy_klienta_str": "Отдел сопровождения",
# # #         "zadacha_str": "",
# # #         "plan_razvitiya_str": "",
# # #         "menedzher_posledniy_pozvonivshiy_str": "",
# # #         "kommentariy_po_zvonku_str": "",
# # #         "plan_sleduyushchego_zvonka_str": "",
# # #         "status_str": "",
# # #         "status_dogovora_str": "",
# # #         "status_po_rassylkam_str": "",
# # #         "status_sayta_str": "301",
# # #         "status_sayta_str": "301",
# # #         "vse_telefony_v_ek5_str": "",
# # #         "uvod_vyruchki_ukazat_dogovor_zapodozrennyy_v_uvode_vyruchki_str": "",
# # #         "primechanie_str": "",
# # #
# # #         # --- integer ---
# # #         "prioritet": 5,
# # #         "vozrast_dogovora_mes": None,
# # #         "kreditnyy_limit": None,
# # #
# # #         # --- boolean ---
# # #         "edo": True,
# # #         "chestnyy_znak": False,
# # #         "vedet_biznes_ili_net": False,
# # #         "integratsiya": False,
# # #         "instrumenty_avtomatizatsii": False,
# # #         "marketpleysy": False,
# # #         "sdek_dokumenty": False,
# # #         "ved": False,
# # #         "ltl": False,
# # #         "ff": False,
# # #         "publikatsiya_otcheta_danet": False,
# # #         "rabotaet_s_konkurentami": False,
# # #         "otpravki_fizicheskim_litsom_nakladnye": False,
# # #         "otpravki_s_drugogo_dogovora_danet": False,
# # #         "peresechenie_po_nomeru_telefona": False,
# # #         "peresechenie_po_e_mail": False,
# # #         "peresechenie_po_inn": False,
# # #         "peresechenie_po_saytu": False,
# # #
# # #         # --- date ---
# # #         "data_podpisaniya_dogovora": "2021-03-05T00:00:00",
# # #         "data_pdz": None,
# # #         "data_zvonka": None,
# # #         "data_sleduyushchego_kontakta_pri_neobhodimosti": None,
# # #         "data_omp_robot": None,
# # #         "data_otpravki_soobshcheniya_po_promo_aktsii": None,
# # #
# # #         # --- required ---
# # #         "tenant_id": 2
# # #     }
# # #
# # #     result = update_crm_data(payload=payload, entity_type_name="kontragenty", api_token=API_TOKEN)
# # #     print("Результат:", result)
# # #
# #
# #
# #
# # # КАСКАДНОЕ УДАЛЕНИЕ ЗАПИСЕЙ С ТАБЛИЦЫ
# #
# # API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYW5pa2JlbGF2aW4yMDA2QGdtYWlsLmNvbSIsImV4cCI6MjA3NTcwNTExNH0.JXxPMrye8Vigv684SmBMF6uqt6fxd9WHajwM3j8Jj8c"
# # import requests
# # import json
# #
# # # --- НАСТРОЙКИ ---
# # API_BASE_URL = "http://89.111.169.47:8005"  # Замените на URL вашего API
# # TABLE_NAME = "kontragenty"                     # Системное имя таблицы
# #
# #
# # auth_token = API_TOKEN
# # def clear_table(token, table_name):
# #     """Получает все ID из таблицы и удаляет их."""
# #     headers = {"Authorization": f"Bearer {token}"}
# #
# #     # 1. Получить все записи из таблицы, чтобы узнать их ID
# #     try:
# #         print(f"Шаг 1: Получение всех записей из таблицы '{table_name}'...")
# #         # Устанавливаем большой limit, чтобы получить все записи
# #         get_response = requests.get(f"{API_BASE_URL}/api/data/{table_name}?limit=1000", headers=headers)
# #         get_response.raise_for_status()
# #         entities = get_response.json()
# #
# #         if not entities:
# #             print("Таблица уже пуста. Удалять нечего.")
# #             return
# #
# #         entity_ids = [entity["id"] for entity in entities]
# #         print(f"Найдено {len(entity_ids)} записей для удаления.")
# #
# #     except requests.exceptions.RequestException as e:
# #         print(f"Ошибка при получении записей: {e}")
# #         print(f"Ответ сервера: {e.response.text}")
# #         return
# #
# #     # 2. Отправить запрос на массовое удаление
# #     try:
# #         print(f"Шаг 2: Отправка запроса на удаление {len(entity_ids)} записей...")
# #         delete_response = requests.post(
# #             f"{API_BASE_URL}/api/data/{table_name}/bulk-delete",
# #             headers=headers,
# #             json={"ids": entity_ids}
# #         )
# #         delete_response.raise_for_status()
# #         result = delete_response.json()
# #         print(f"Успешно! API вернул ответ: {result}")
# #
# #     except requests.exceptions.RequestException as e:
# #         print(f"Ошибка при удалении записей: {e}")
# #         print(f"Ответ сервера: {e.response.text}")
# # if __name__ == "__main__":
# #
# #     if auth_token:
# #         clear_table(auth_token, TABLE_NAME)
#
#
# import requests
# from typing import List
#
# # --- ГЛАВНЫЕ НАСТРОЙКИ ---
# # URL вашего API
# API_BASE_URL = "http://89.111.169.47:8005"
#
# # Ваш токен доступа
# API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYW5pa2JlbGF2aW4yMDA2QGdtYWlsLmNvbSIsImV4cCI6MjA3NTcwNTExNH0.JXxPMrye8Vigv684SmBMF6uqt6fxd9WHajwM3j8Jj8c"
# # -------------------------
#
# # Глобальные заголовки для всех запросов
# HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}
# TABLE_NAME = "demo_formula_update_table"
#
#
# def cleanup_test_tables(table_names: List[str]):
#     """Удаляет тестовые таблицы."""
#     print("\n--- Шаг 0: Очистка старых тестовых таблиц ---")
#     try:
#         response = requests.get(f"{API_BASE_URL}/api/meta/entity-types", headers=HEADERS)
#         if response.status_code == 200:
#             for et in response.json():
#                 if et['name'] in table_names:
#                     print(f"Очистка: удаление старой таблицы '{et['name']}' (ID: {et['id']})")
#                     requests.delete(f"{API_BASE_URL}/api/meta/entity-types/{et['id']}", headers=HEADERS)
#     except requests.exceptions.RequestException as e:
#         print(f"Ошибка во время очистки: {e}")
#
#
# def run_demo():
#     """Выполняет демонстрацию обновления формулы."""
#     ids = {}
#
#     try:
#         # --- Шаг 1: Создание таблицы и колонок с начальной формулой ---
#         print("\n--- Шаг 1: Создание метаданных ---")
#
#         type_resp = requests.post(
#             f"{API_BASE_URL}/api/meta/entity-types", headers=HEADERS,
#             json={"name": TABLE_NAME, "display_name": "Демо обновления формул"}
#         )
#         type_resp.raise_for_status()
#         ids["type_id"] = type_resp.json()["id"]
#
#         requests.post(f"{API_BASE_URL}/api/meta/entity-types/{ids['type_id']}/attributes", headers=HEADERS,
#                       json={"name": "price", "display_name": "Цена", "value_type": "float"}).raise_for_status()
#         requests.post(f"{API_BASE_URL}/api/meta/entity-types/{ids['type_id']}/attributes", headers=HEADERS,
#                       json={"name": "quantity", "display_name": "Количество",
#                             "value_type": "integer"}).raise_for_status()
#
#         initial_formula = "{price} * {quantity}"
#         total_resp = requests.post(
#             f"{API_BASE_URL}/api/meta/entity-types/{ids['type_id']}/attributes", headers=HEADERS,
#             json={"name": "total", "display_name": "Итого", "value_type": "formula", "formula_text": initial_formula}
#         )
#         total_resp.raise_for_status()
#         ids["total_attr_id"] = total_resp.json()["id"]
#
#         print("✅ Метаданные (таблица и колонки) успешно созданы.")
#
#         # --- Шаг 2: Добавление тестовых данных ---
#         print("\n--- Шаг 2: Добавление строки с данными (Цена=100, Кол-во=2) ---")
#         requests.post(f"{API_BASE_URL}/api/data/{TABLE_NAME}", headers=HEADERS,
#                       json={"price": 100.0, "quantity": 2}).raise_for_status()
#         print("✅ Данные успешно добавлены.")
#
#         # --- Шаг 3: Проверка начального результата ---
#         print("\n--- Шаг 3: Проверка расчета по НАЧАЛЬНОЙ формуле ---")
#         get_resp_1 = requests.get(f"{API_BASE_URL}/api/data/{TABLE_NAME}", headers=HEADERS)
#         get_resp_1.raise_for_status()
#         initial_result = get_resp_1.json()[0]['total']
#         print(f"✅ Получен результат: {initial_result}")
#         assert initial_result == 200.0
#
#         # --- Шаг 4: ОБНОВЛЕНИЕ ФОРМУЛЫ ---
#         print("\n--- Шаг 4: Отправка PUT-запроса на изменение формулы ---")
#         new_formula = "({price} * {quantity}) * 1.2"
#         update_payload = {"formula_text": new_formula}
#
#         update_resp = requests.put(
#             f"{API_BASE_URL}/api/meta/entity-types/{ids['type_id']}/attributes/{ids['total_attr_id']}",
#             headers=HEADERS, json=update_payload
#         )
#         update_resp.raise_for_status()
#         print(f"✅ Формула успешно обновлена на: '{new_formula}'")
#
#         # --- Шаг 5: Проверка конечного результата ---
#         print("\n--- Шаг 5: Проверка пересчета по НОВОЙ формуле ---")
#         get_resp_2 = requests.get(f"{API_BASE_URL}/api/data/{TABLE_NAME}", headers=HEADERS)
#         get_resp_2.raise_for_status()
#         final_result = get_resp_2.json()[0]['total']
#         print(f"✅ Получен новый результат: {final_result}")
#         assert final_result == 240.0
#
#         print("\n🎉🎉🎉 Демонстрация успешно завершена! Функция работает корректно. 🎉🎉🎉")
#
#     except requests.exceptions.RequestException as e:
#         print(f"\n❌ ОШИБКА: {e}")
#         if e.response is not None:
#             print(f"Статус ответа сервера: {e.response.status_code}")
#             print(f"Тело ответа: {e.response.text}")
#     except (AssertionError, KeyError, IndexError):
#         print("\n❌ ПРОВЕРКА НЕ ПРОЙДЕНА: Результат вычислений не соответствует ожидаемому.")
#     finally:
#         # Удаляем созданную таблицу в любом случае
#         cleanup_test_tables([TABLE_NAME])
#
#
# if __name__ == "__main__":
#     run_demo()


print(56+7)