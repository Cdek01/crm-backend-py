# import requests
# import time
# import sys
# import json
#
# # --- НАСТРОЙКИ ---
# BASE_URL = "http://89.111.169.47:8005"
# EMAIL = "1@example.com"
# PASSWORD = "string"
#
#
# # -----------------
#
# # --- Вспомогательные функции ---
# def print_status(ok, message):
#     if ok:
#         print(f"✅ [OK] {message}")
#     else:
#         print(f"❌ [FAIL] {message}\n")
#         # Не выходим из скрипта, чтобы выполнился блок finally
#         # sys.exit(1)
#
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
#
# def login():
#     try:
#         auth_payload = {'username': EMAIL, 'password': PASSWORD}
#         token_resp = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
#         token_resp.raise_for_status()
#         return {'Authorization': f'Bearer {token_resp.json()["access_token"]}'}
#     except Exception as e:
#         print(f"Критическая ошибка при авторизации: {e}")
#         return None
#
#
# # --- Основная функция демонстрации ---
# def run_smart_relation_test():
#     headers = login()
#     if not headers: return
#
#     ids = {}
#
#     try:
#         # --- ШАГ 1: ПОДГОТОВКА ---
#         print_header("Шаг 1: Создание таблиц 'Компании' и 'Контакты'")
#
#         companies_name = f"companies_smart_{int(time.time())}"
#         contacts_name = f"contacts_smart_{int(time.time())}"
#
#         resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
#                              json={"name": companies_name, "display_name": "Компании (Smart)"})
#         resp.raise_for_status();
#         ids['companies_table'] = resp.json()
#
#         resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
#                              json={"name": contacts_name, "display_name": "Контакты (Smart)"})
#         resp.raise_for_status();
#         ids['contacts_table'] = resp.json()
#
#         # Создаем "главные" колонки для названий
#         resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['companies_table']['id']}/attributes",
#                              headers=headers,
#                              json={"name": "company_name", "display_name": "Название компании", "value_type": "string"})
#         resp.raise_for_status();
#         ids['company_name_attr'] = resp.json()
#
#         resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}/attributes",
#                              headers=headers,
#                              json={"name": "contact_name", "display_name": "Имя контакта", "value_type": "string"})
#         resp.raise_for_status();
#         ids['contact_name_attr'] = resp.json()
#         print_status(True, "Подготовительный этап завершен.")
#
#         # --- ТЕСТ 1: МИНИМАЛЬНАЯ ОДНОСТОРОННЯЯ СВЯЗЬ ---
#         print_header("Тест 1: Минимальная ОДНОСТОРОННЯЯ связь")
#
#         payload1 = {
#             "name": "contact_company", "display_name": "Компания контакта", "value_type": "relation",
#             "target_entity_type_id": ids['companies_table']['id']
#             # display_attribute_id НЕ передаем!
#         }
#
#         print(" -> Отправляем POST, указав только целевую таблицу...")
#         resp1 = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}/attributes",
#                               headers=headers, json=payload1)
#         resp1.raise_for_status()
#         created_attr1 = resp1.json()
#
#         print_status(resp1.status_code == 201, "Запрос успешно выполнен.")
#         print_status(
#             created_attr1['display_attribute_id'] == ids['company_name_attr']['id'],
#             "Бэкенд сам нашел и установил правильное отображаемое поле ('Название компании')."
#         )
#
#         # --- ТЕСТ 2: МИНИМАЛЬНАЯ ДВУСТОРОННЯЯ СВЯЗЬ ---
#         print_header("Тест 2: Минимальная ДВУСТОРОННЯЯ связь")
#
#         payload2 = {
#             "name": "company_contacts", "display_name": "Контакты компании", "value_type": "relation",
#             "target_entity_type_id": ids['contacts_table']['id'],
#             "create_back_relation": True
#             # display_attribute_id НЕ передаем!
#             # back_relation_... НЕ передаем!
#         }
#
#         print(" -> Отправляем POST, указав только целевую таблицу и флаг create_back_relation...")
#         resp2 = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['companies_table']['id']}/attributes",
#                               headers=headers, json=payload2)
#         resp2.raise_for_status()
#         main_attr2 = resp2.json()
#
#         print_status(resp2.status_code == 201, "Запрос успешно выполнен.")
#
#         print("\n--- Проверяем ПРЯМУЮ связь ('Контакты компании' в 'Компаниях') ---")
#         print_status(
#             main_attr2['display_attribute_id'] == ids['contact_name_attr']['id'],
#             " -> Бэкенд сам нашел отображаемое поле для прямой связи ('Имя контакта')."
#         )
#         print_status(main_attr2['reciprocal_attribute_id'] is not None, " -> Прямая связь 'знает' о своей паре.")
#
#         # Получаем детали обратной связи для проверки
#         resp_contacts_table = requests.get(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}",
#                                            headers=headers)
#         contacts_attrs = resp_contacts_table.json()['attributes']
#         back_relation_attr = next(
#             (attr for attr in contacts_attrs if attr['id'] == main_attr2['reciprocal_attribute_id']), None)
#
#         print("\n--- Проверяем ОБРАТНУЮ связь (авто-созданную в 'Контактах') ---")
#         print_status(back_relation_attr is not None, " -> Обратная связь была автоматически создана.")
#         if back_relation_attr:
#             print(f" -> Сгенерированное имя: '{back_relation_attr['display_name']}'")
#             print_status(
#                 back_relation_attr['target_entity_type_id'] == ids['companies_table']['id'],
#                 " -> Обратная связь правильно ссылается на таблицу 'Компании'."
#             )
#             print_status(
#                 back_relation_attr['display_attribute_id'] == ids['company_name_attr']['id'],
#                 " -> Бэкенд сам нашел отображаемое поле для обратной связи ('Название компании')."
#             )
#
#     except requests.exceptions.HTTPError as e:
#         print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
#     except Exception as e:
#         print_status(False, f"Произошла непредвиденная ошибка: {e}")
#     finally:
#         # --- ОЧИСТКА ---
#         print_header("Очистка (удаление тестовых таблиц)")
#         if 'companies_table' in ids:
#             requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['companies_table']['id']}", headers=headers)
#             print(f" -> Таблица 'Компании (Smart)' удалена.")
#         if 'contacts_table' in ids:
#             requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}", headers=headers)
#             print(f" -> Таблица 'Контакты (Smart)' удалена.")
#         print_status(True, "Очистка завершена.")
#
#
# if __name__ == "__main__":
#     run_smart_relation_test()


import requests
import time
import sys
import json

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"


# -----------------

# --- Вспомогательные функции ---
def print_status(ok, message):
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}\n")
        # Не выходим, чтобы выполнился блок finally
        # sys.exit(1)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def login():
    try:
        auth_payload = {'username': EMAIL, 'password': PASSWORD}
        token_resp = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload)
        token_resp.raise_for_status()
        return {'Authorization': f'Bearer {token_resp.json()["access_token"]}'}
    except Exception as e:
        print(f"Критическая ошибка при авторизации: {e}")
        return None


# --- Основная функция демонстрации ---
def run_smart_relation_test():
    headers = login()
    if not headers: return

    ids = {}
    test_failed = False  # Флаг для отслеживания ошибок

    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("Шаг 1: Создание таблиц 'Компании' и 'Контакты'")
        companies_name = f"companies_smart_{int(time.time())}"
        contacts_name = f"contacts_smart_{int(time.time())}"

        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": companies_name, "display_name": "Компании (Smart)"})
        resp.raise_for_status();
        ids['companies_table'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": contacts_name, "display_name": "Контакты (Smart)"})
        resp.raise_for_status();
        ids['contacts_table'] = resp.json()

        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['companies_table']['id']}/attributes",
                             headers=headers,
                             json={"name": "company_name", "display_name": "Название компании", "value_type": "string"})
        resp.raise_for_status();
        ids['company_name_attr'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}/attributes",
                             headers=headers,
                             json={"name": "contact_name", "display_name": "Имя контакта", "value_type": "string"})
        resp.raise_for_status();
        ids['contact_name_attr'] = resp.json()
        print_status(True, "Подготовительный этап завершен.")

        # --- ТЕСТ 1: МИНИМАЛЬНАЯ ОДНОСТОРОННЯЯ СВЯЗЬ ---
        print_header("Тест 1: Минимальная ОДНОСТОРОННЯЯ связь")
        payload1 = {"name": "contact_company", "display_name": "Компания контакта", "value_type": "relation",
                    "target_entity_type_id": ids['companies_table']['id']}
        resp1 = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}/attributes",
                              headers=headers, json=payload1)
        resp1.raise_for_status();
        created_attr1 = resp1.json()
        print_status(resp1.status_code == 201, "Запрос успешно выполнен.")
        if not (created_attr1.get('display_attribute_id') == ids['company_name_attr']['id']):
            print_status(False, "Бэкенд сам нашел и установил правильное отображаемое поле ('Название компании').");
            test_failed = True
        else:
            print_status(True, "Бэкенд сам нашел и установил правильное отображаемое поле ('Название компании').")

        # --- ТЕСТ 2: МИНИМАЛЬНАЯ ДВУСТОРОННЯЯ СВЯЗЬ ---
        print_header("Тест 2: Минимальная ДВУСТОРОННЯЯ связь")
        payload2 = {"name": "company_contacts", "display_name": "Контакты компании", "value_type": "relation",
                    "target_entity_type_id": ids['contacts_table']['id'], "create_back_relation": True}
        resp2 = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['companies_table']['id']}/attributes",
                              headers=headers, json=payload2)
        resp2.raise_for_status();
        main_attr2 = resp2.json()
        print_status(resp2.status_code == 201, "Запрос успешно выполнен.")

        print("\n--- Проверяем ПРЯМУЮ связь ('Контакты компании' в 'Компаниях') ---")
        if not (main_attr2.get('display_attribute_id') == ids['contact_name_attr']['id']):
            print_status(False, " -> Бэкенд сам нашел отображаемое поле для прямой связи ('Имя контакта').");
            test_failed = True
        else:
            print_status(True, " -> Бэкенд сам нашел отображаемое поле для прямой связи ('Имя контакта').")

        if not main_attr2.get('reciprocal_attribute_id'):
            print_status(False, " -> Прямая связь 'знает' о своей паре.");
            test_failed = True
        else:
            print_status(True, " -> Прямая связь 'знает' о своей паре.")

        # Получаем детали обратной связи для проверки
        resp_contacts_table = requests.get(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}",
                                           headers=headers)
        contacts_attrs = resp_contacts_table.json()['attributes']
        back_relation_attr = next(
            (attr for attr in contacts_attrs if attr.get('id') == main_attr2.get('reciprocal_attribute_id')), None)

        print("\n--- Проверяем ОБРАТНУЮ связь (авто-созданную в 'Контактах') ---")
        if not back_relation_attr:
            print_status(False, " -> Обратная связь была автоматически создана.");
            test_failed = True
        else:
            print_status(True, " -> Обратная связь была автоматически создана.")
            print(f" -> Сгенерированное имя: '{back_relation_attr.get('display_name')}'")
            if not (back_relation_attr.get('target_entity_type_id') == ids['companies_table']['id']):
                print_status(False, " -> Обратная связь правильно ссылается на таблицу 'Компании'.");
                test_failed = True
            else:
                print_status(True, " -> Обратная связь правильно ссылается на таблицу 'Компании'.")

            if not (back_relation_attr.get('display_attribute_id') == ids['company_name_attr']['id']):
                print_status(False, " -> Бэкенд сам нашел отображаемое поле для обратной связи ('Название компании').");
                test_failed = True
            else:
                print_status(True, " -> Бэкенд сам нашел отображаемое поле для обратной связи ('Название компании').")

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}");
        test_failed = True
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}");
        test_failed = True
    finally:
        # --- ОЧИСТКА ---
        print_header("Очистка (удаление тестовых таблиц)")
        if 'companies_table' in ids:
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['companies_table']['id']}", headers=headers)
            print(f" -> Таблица 'Компании (Smart)' удалена.")
        if 'contacts_table' in ids:
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['contacts_table']['id']}", headers=headers)
            print(f" -> Таблица 'Контакты (Smart)' удалена.")
        print_status(True, "Очистка завершена.")

        # Финальный вердикт
        if test_failed:
            sys.exit(1)


if __name__ == "__main__":
    run_smart_relation_test()