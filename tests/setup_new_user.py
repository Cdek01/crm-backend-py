# import requests
# import json
# import time
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
#
# # BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# BASE_URL = "http://89.111.169.47:8005"
#
# CORRECT_REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"
#
# # --- Данные нового пользователя ---
# USER_EMAIL = "real_user@company.com"
# USER_PASSWORD = "a_very_strong_password"
# USER_FULL_NAME = "Шлипс Антон"
#
# # --- Структура таблиц, основанная на ваших скриншотах ---
# TABLES_STRUCTURE = {
#     # 1. Лиды
#     "leads_custom": {
#         "display_name": "Лиды",
#         "attributes": [
#             {"name": "lead_name", "display_name": "Название компании", "value_type": "string"},
#             {"name": "lead_rating", "display_name": "Оценка лида", "value_type": "string"},
#             {"name": "inn", "display_name": "ИНН", "value_type": "string"},
#             {"name": "company_reg_date", "display_name": "Дата регистрации компании", "value_type": "date"},
#             {"name": "card_reg_date_in_eks", "display_name": "Дата создания карточки контрагента в ЕКС",
#              "value_type": "date"},
#             {"name": "card_reg_date_in_crm", "display_name": "Дата создания лида в CRM", "value_type": "date"},
#             {"name": "form_of_incorporation", "display_name": "Форма образования", "value_type": "string"},
#             {"name": "is_duplicate_inn", "display_name": "Дубликат контрагента", "value_type": "boolean"},
#             {"name": "duplicate_actions", "display_name": "Предлагаемые действия", "value_type": "string"},
#             {"name": "phone", "display_name": "Телефон", "value_type": "string"},
#             {"name": "last_contact_date", "display_name": "Дата контакта", "value_type": "date"},
#             {"name": "site", "display_name": "Сайт", "value_type": "string"},
#             {"name": "is_contract_signed", "display_name": "Есть заключенный договор?", "value_type": "boolean"},
#             {"name": "omp_creation_note", "display_name": "Отметка о создании ОМП (ЕКС)", "value_type": "boolean"},
#             {"name": "omp_history", "display_name": "Наличие истории ОМП", "value_type": "boolean"},
#             {"name": "last_omp_date", "display_name": "Дата предоставления последнего ОМП", "value_type": "date"},
#             {"name": "omp_type", "display_name": "Тип ОМП", "value_type": "string"},
#             {"name": "manager_notes", "display_name": "Текст отчета менеджера", "value_type": "string"},
#             {"name": "contact_person", "display_name": "Контакт (руководитель и т.д.)", "value_type": "string"},
#             {"name": "orders_count", "display_name": "Количество заказов (общее)", "value_type": "integer"},
#             {"name": "orders_dynamics", "display_name": "Есть динамика", "value_type": "string"},
#             {"name": "orders_sum", "display_name": "Сумма заказов (общая)", "value_type": "float"},
#             {"name": "bpi_term", "display_name": "Срок окончания ВЗП", "value_type": "date"},
#             {"name": "whatsapp", "display_name": "WhatsApp", "value_type": "string"},
#             {"name": "telegram", "display_name": "Telegramm", "value_type": "string"},
#             {"name": "commercial_offer_sent", "display_name": "Коммерческое предложение отправлено на",
#              "value_type": "date"},
#             {"name": "has_certificates", "display_name": "Наличие сертификатов", "value_type": "boolean"},
#             {"name": "contact_phone_number", "display_name": "Контактный номер телефона", "value_type": "string"},
#         ]
#     },
#     # 2. Архив лидов
#     "archived_leads": {
#         "display_name": "Архив лидов",
#         "attributes": [
#             {"name": "archived_lead_name", "display_name": "Название компании", "value_type": "string"},
#             {"name": "responsible_manager", "display_name": "Ответственный менеджер", "value_type": "string"},
#             {"name": "archived_date", "display_name": "Дата перевода в архив", "value_type": "date"},
#             {"name": "archive_reason", "display_name": "Причина архивации", "value_type": "string"},
#             {"name": "details", "display_name": "Детали причины", "value_type": "string"},
#             {"name": "archive_stage", "display_name": "Этап на момент архивации", "value_type": "string"},
#             {"name": "last_contact_date", "display_name": "Последний статус контакта", "value_type": "string"},
#             {"name": "check_after_archive_date", "display_name": "Дата следующей проверки перед архивацией",
#              "value_type": "date"},
#             {"name": "can_restore", "display_name": "Возможность восстановления", "value_type": "boolean"},
#             {"name": "source", "display_name": "Источник лида", "value_type": "string"},
#             {"name": "creation_date", "display_name": "Дата создания лида", "value_type": "date"},
#             {"name": "notes", "display_name": "Примечания", "value_type": "string"},
#             {"name": "creation_in_crm_date", "display_name": "Появление в CRM", "value_type": "date"},
#             {"name": "lead_scenario", "display_name": "Сценарий лида", "value_type": "string"},
#             {"name": "inn", "display_name": "ИНН", "value_type": "string"},
#             {"name": "sales_funnel_source", "display_name": "Источник воронки продаж", "value_type": "string"},
#         ]
#     },
#     # 3. Мониторинг
#     "monitoring": {
#         "display_name": "Мониторинг",
#         "attributes": [
#             {"name": "company_name", "display_name": "Название компании", "value_type": "string"},
#             {"name": "responsible_manager", "display_name": "Ответственный менеджер", "value_type": "string"},
#             {"name": "client_status", "display_name": "Статус клиента", "value_type": "string"},
#             {"name": "bpi_status", "display_name": "Статус ВЗП (закрепления)", "value_type": "boolean"},
#             {"name": "bpi_end_date", "display_name": "Срок окончания ВЗП", "value_type": "date"},
#             {"name": "contract_status", "display_name": "Статус договора", "value_type": "string"},
#             {"name": "dynamics_3m", "display_name": "Динамика заказов за 3 мес", "value_type": "boolean"},
#             {"name": "orders_count_period", "display_name": "Кол-во заказов за период", "value_type": "integer"},
#             {"name": "revenue_period", "display_name": "Сумма выручки за период", "value_type": "float"},
#             {"name": "no_dynamics_reason", "display_name": "Признак 'нет динамики'", "value_type": "boolean"},
#             {"name": "last_contact_date", "display_name": "Последний контакт", "value_type": "date"},
#             {"name": "next_planned_action_date", "display_name": "Следующее запланированное действие",
#              "value_type": "date"},
#             {"name": "next_planned_action_type", "display_name": "Тип 'следующего действия'", "value_type": "string"},
#             {"name": "monitoring_notes", "display_name": "Примечания", "value_type": "string"},
#             {"name": "signal_source", "display_name": "Источник сигнала", "value_type": "string"},
#             {"name": "check_status", "display_name": "Статус проверки", "value_type": "string"},
#             {"name": "check_end_date", "display_name": "Дата завершения проверки", "value_type": "date"},
#             {"name": "bpi_active", "display_name": "Действующий ВЗП", "value_type": "string"},
#         ]
#     },
#     # 4. Сделка
#     "deals": {
#         "display_name": "Сделка",
#         "attributes": [
#             {"name": "start_date", "display_name": "Дата_начала_переговоров", "value_type": "date"},
#             {"name": "deal_stage", "display_name": "Цикл_сделки", "value_type": "string"},
#             {"name": "last_contact_date", "display_name": "Результат_текущего_контакта", "value_type": "string"},
#             {"name": "responsible_manager", "display_name": "Привлеченный_менеджер", "value_type": "string"},
#             {"name": "next_action_date", "display_name": "Запланированная_дата_следующего_шага", "value_type": "date"},
#             {"name": "deal_status", "display_name": "Статус_в_переговорах", "value_type": "string"},
#             {"name": "priority", "display_name": "Признак_Срочно", "value_type": "boolean"},
#             {"name": "document_automation", "display_name": "Автоматизация_документооборота", "value_type": "string"},
#             {"name": "kpi_sent", "display_name": "КП_отправлено", "value_type": "boolean"},
#             {"name": "kpi_sent_date", "display_name": "Дата_отправки_КП", "value_type": "date"},
#             {"name": "docs_received", "display_name": "Документы_получены", "value_type": "boolean"},
#             {"name": "docs_received_date", "display_name": "Дата_получения_документов", "value_type": "date"},
#             {"name": "category_required", "display_name": "Требуется_категория", "value_type": "boolean"},
#             {"name": "deal_closed", "display_name": "Завершение", "value_type": "boolean"},
#             {"name": "archive_reason", "display_name": "Архив_переговоров", "value_type": "string"},
#             {"name": "next_action_type", "display_name": "Дата следующего действия", "value_type": "date"},
#         ]
#     },
#     # 5. Договоры
#     "contracts": {
#         "display_name": "Договоры",
#         "attributes": [
#             {"name": "company_name", "display_name": "Название компании", "value_type": "string"},
#             {"name": "responsible_manager", "display_name": "Ответственный менеджер", "value_type": "string"},
#             {"name": "contract_type", "display_name": "Тип договора", "value_type": "string"},
#             {"name": "doc_date", "display_name": "Дата подписания", "value_type": "date"},
#             {"name": "deal_type", "display_name": "Вид договора", "value_type": "string"},
#             {"name": "start_date", "display_name": "Дата начала действия", "value_type": "date"},
#             {"name": "end_date", "display_name": "Дата окончания действия", "value_type": "date"},
#             {"name": "bpi_attached", "display_name": "ВЗП (Бронирование)", "value_type": "boolean"},
#             {"name": "bpi_end_date", "display_name": "Срок окончания ВЗП", "value_type": "date"},
#             {"name": "is_dynamic", "display_name": "Динамика заказов", "value_type": "boolean"},
#             {"name": "total_sum", "display_name": "Сумма договора", "value_type": "float"},
#             {"name": "orders_count", "display_name": "Количество заказов", "value_type": "integer"},
#             {"name": "no_dynamics_3m", "display_name": "Признак 'Есть динамика'", "value_type": "boolean"},
#             {"name": "diadoc_docs", "display_name": "Документы в Диадок", "value_type": "boolean"},
#             {"name": "source", "display_name": "Источник договора", "value_type": "string"},
#             {"name": "notes", "display_name": "Примечания", "value_type": "string"},
#             {"name": "is_archived", "display_name": "Архивация договора", "value_type": "boolean"},
#         ]
#     },
#     # 6. Учредители и директора
#     "founders_directors": {
#         "display_name": "Учредители и директора",
#         "attributes": [
#             {"name": "person_name", "display_name": "ФИО", "value_type": "string"},
#             {"name": "position", "display_name": "Должность", "value_type": "string"},
#             {"name": "contact_type", "display_name": "Тип_Контакта", "value_type": "string"},
#             {"name": "phone", "display_name": "Телефон", "value_type": "string"},
#             {"name": "email", "display_name": "Email", "value_type": "string"},
#             {"name": "birth_date", "display_name": "Дата Рождения", "value_type": "date"},
#             {"name": "responsible_for_payment", "display_name": "Ответственный_за_Оплату", "value_type": "boolean"},
#         ]
#     },
# }
#
#
# # ----------------------------------------------------------------------
# # --- ОСНОВНОЙ КОД ---
# def run_setup():
#     print(f"НАСТРОЙКА НОВОГО ПОЛЬЗОВАТЕЛЯ: {USER_EMAIL}")
#
#     try:
#         # 1. Регистрация и авторизация
#         print(" -> Шаг 1: Регистрация и авторизация...")
#         reg_payload = {"email": USER_EMAIL, "password": USER_PASSWORD, "full_name": USER_FULL_NAME,
#                        "registration_token": CORRECT_REGISTRATION_TOKEN}
#         requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload).raise_for_status()
#         auth_payload = {'username': USER_EMAIL, 'password': USER_PASSWORD}
#         token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#         print(" -> Пользователь успешно создан и авторизован.")
#
#         # 2. Создание таблиц и колонок
#         print("\n -> Шаг 2: Создание структуры таблиц...")
#         for table_name, table_data in TABLES_STRUCTURE.items():
#             print(f"\n  --> Создание таблицы: '{table_data['display_name']}'")
#             table_payload = {"name": table_name, "display_name": table_data['display_name']}
#
#             # Отправляем запрос на создание таблицы
#             table_resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers, json=table_payload)
#             if table_resp.status_code == 400 and "уже существует" in table_resp.text:
#                 print(f"  --> Таблица с системным именем '{table_name}' уже существует, пропускаем.")
#                 # Нам нужно получить ID существующей таблицы для добавления колонок
#                 all_tables_resp = requests.get(f"{BASE_URL}/api/meta/entity-types", headers=headers)
#                 existing_table = next((t for t in all_tables_resp.json() if t['name'] == table_name), None)
#                 if not existing_table:
#                     print(f"  --> КРИТИЧЕСКАЯ ОШИБКА: Не удалось найти ID существующей таблицы '{table_name}'")
#                     continue
#                 table_id = existing_table['id']
#             else:
#                 table_resp.raise_for_status()
#                 table_id = table_resp.json()['id']
#
#             # Создаем колонки для этой таблицы
#             for attr_payload in table_data['attributes']:
#                 print(f"    - Создание колонки: '{attr_payload['display_name']}'")
#                 attr_url = f"{BASE_URL}/api/meta/entity-types/{table_id}/attributes"
#                 attr_resp = requests.post(attr_url, headers=headers, json=attr_payload)
#                 if attr_resp.status_code == 400 and "уже существует" in attr_resp.text:
#                     pass  # Просто пропускаем, если колонка уже есть
#                 else:
#                     attr_resp.raise_for_status()
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА! 🎉🎉🎉")
#         print(f"Пользователь {USER_EMAIL} и все его таблицы созданы.")
#         print("Теперь вы можете зайти в админ-панель, перезапустить сервер и настроить роли.")
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
#     run_setup()
#
#
# import requests
# import json
# import random
# from faker import Faker
# from datetime import datetime, timedelta
#
# # --- НАСТРОЙКИ (Отредактируйте эту секцию) ---
#
# BASE_URL = "http://127.0.0.1:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
# BASE_URL = "http://89.111.169.47:8005"  # ИЛИ "http://89.111.169.47:8005" для сервера
#
# # --- Данные пользователя, для которого заполняем таблицы ---
# USER_EMAIL = "real_user@company.com"
# USER_PASSWORD = "a_very_strong_password"
#
# # --- Сколько записей создать для каждой таблицы ---
# RECORDS_TO_CREATE = 5
#
# # ----------------------------------------------------------------------
# # Инициализация Faker для генерации русскоязычных данных
# fake = Faker('ru_RU')
#
#
# def print_status(ok, message):
#     if ok:
#         print(f"✅ [OK] {message}")
#     else:
#         print(f"❌ [FAIL] {message}")
#
#
# def print_header(title):
#     print("\n" + "=" * 60)
#     print(f" {title} ".center(60, "="))
#     print("=" * 60)
#
#
# # --- Генераторы тестовых данных для каждой таблицы ---
#
# def generate_lead_data():
#     return {
#         "lead_name": fake.company(),
#         "lead_rating": random.choice(["A", "B", "C"]),
#         "inn": fake.numerify(text="############"),
#         "company_reg_date": (datetime.now() - timedelta(days=random.randint(30, 3650))).isoformat(),
#         "phone": fake.phone_number(),
#         "site": fake.url(),
#         "contact_person": fake.name(),
#         "orders_count": random.randint(0, 50),
#         "orders_sum": round(random.uniform(1000, 500000), 2),
#     }
#
#
# def generate_contract_data():
#     return {
#         "company_name": fake.company(),
#         "responsible_manager": fake.name(),
#         "contract_type": random.choice(["Основной", "Дополнительный", "Оферта"]),
#         "doc_date": (datetime.now() - timedelta(days=random.randint(10, 500))).isoformat(),
#         "total_sum": round(random.uniform(5000, 1000000), 2),
#         "orders_count": random.randint(1, 20),
#         "is_archived": fake.boolean(chance_of_getting_true=10),
#     }
#
#
# def generate_founder_data():
#     return {
#         "person_name": fake.name(),
#         "position": random.choice(["Генеральный директор", "Учредитель", "Бухгалтер", "Менеджер по закупкам"]),
#         "contact_type": "Основной",
#         "phone": fake.phone_number(),
#         "email": fake.email(),
#         "birth_date": fake.date_of_birth(minimum_age=30, maximum_age=65).isoformat(),
#         "responsible_for_payment": fake.boolean(chance_of_getting_true=25),
#     }
#
#
# # Добавьте сюда другие генераторы, если нужно (generate_deal_data, etc.)
#
# # Словарь, связывающий системные имена таблиц с функциями-генераторами
# TABLE_GENERATORS = {
#     "leads_custom": generate_lead_data,
#     "contracts": generate_contract_data,
#     "founders_directors": generate_founder_data,
#     # "deals": generate_deal_data, # Раскомментируйте, если добавите генератор
# }
#
#
# # --- ОСНОВНОЙ КОД ---
# def run_population():
#     print_header(f"ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ ДЛЯ: {USER_EMAIL}")
#
#     try:
#         # 1. Авторизация
#         print(" -> Шаг 1: Авторизация...")
#         auth_payload = {'username': USER_EMAIL, 'password': USER_PASSWORD}
#         token = requests.post(f"{BASE_URL}/api/auth/token", data=auth_payload).json()['access_token']
#         headers = {'Authorization': f'Bearer {token}'}
#         print(" -> Авторизация успешна.")
#
#         # 2. Заполнение таблиц
#         print("\n -> Шаг 2: Заполнение таблиц...")
#         for table_name, generator_func in TABLE_GENERATORS.items():
#             print(f"\n  --> Заполнение таблицы: '{table_name}'")
#             try:
#                 # Генерируем и отправляем данные
#                 for i in range(RECORDS_TO_CREATE):
#                     record_data = generator_func()
#                     print(f"    - Отправка записи #{i + 1}...")
#                     resp = requests.post(f"{BASE_URL}/api/data/{table_name}", headers=headers, json=record_data)
#                     if resp.status_code != 201:
#                         # Если API вернуло ошибку, сообщаем о ней, но не прерываем скрипт
#                         print(f"    - ⚠️  Ошибка при создании записи: {resp.status_code} - {resp.text}")
#                     else:
#                         print(f"    - Запись #{i + 1} успешно создана.")
#                 print_status(True, f"Таблица '{table_name}' заполнена.")
#             except requests.exceptions.HTTPError as he:
#                 print_status(False,
#                              f"Критическая ошибка HTTP при работе с таблицей '{table_name}': {he.response.status_code} - {he.response.text}")
#
#         print("\n" + "=" * 60)
#         print("🎉🎉🎉 ЗАПОЛНЕНИЕ ДАННЫМИ УСПЕШНО ЗАВЕРШЕНО! 🎉🎉🎉")
#
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ ОШИБКА HTTP.")
#         print(f"Статус: {e.response.status_code}, Ответ: {e.response.text}")
#     except Exception as e:
#         print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")
#
#
# if __name__ == "__main__":
#     run_population()


import requests
import json

# --- НАСТРОЙКИ (Отредактируйте эту секцию) ---

# Адрес запущенного API
# BASE_URL = "http://127.0.0.1:8000"  # ИЛИ "http://89.111.169.47:8005" для сервера
BASE_URL = "http://89.111.169.47:8005"  # для сервера
# Секретный токен для регистрации, указанный в вашем .env файле
REGISTRATION_TOKEN = "your-super-secret-and-unique-token-12345"

# --- Данные нового пользователя ---
NEW_USER_EMAIL = "new.user@example.com"
NEW_USER_PASSWORD = "Password123!"
NEW_USER_FULL_NAME = "Иван Иванов"


# ----------------------------------------------------

def create_user():
    """
    Отправляет запрос на регистрацию одного нового пользователя.
    """
    print(f"--- Попытка создать пользователя: {NEW_USER_EMAIL} ---")

    # Формируем тело запроса
    payload = {
        "email": NEW_USER_EMAIL,
        "password": NEW_USER_PASSWORD,
        "full_name": NEW_USER_FULL_NAME,
        "registration_token": REGISTRATION_TOKEN
    }

    try:
        # Отправляем POST запрос
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)

        # Проверяем результат
        if response.status_code == 201:
            print("\n✅ УСПЕХ! Пользователь успешно создан.")
            print("   Для него также была автоматически создана новая 'Компания' (тенант).")
            print("\n   Получены следующие данные:")
            # Красиво печатаем ответ от сервера
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        elif response.status_code == 400 and "уже существует" in response.text:
            print(f"\nℹ️  ИНФОРМАЦИЯ: Пользователь с email '{NEW_USER_EMAIL}' уже существует в базе данных.")

        elif response.status_code == 403:
            print(f"\n❌ ОШИБКА: Неверный токен регистрации (403 Forbidden).")
            print(
                f"   Проверьте, что 'REGISTRATION_TOKEN' в скрипте совпадает с 'REGISTRATION_SECRET_TOKEN' в вашем .env файле.")

        else:
            # Для всех других ошибок, вызываем исключение, чтобы увидеть детали
            response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ОШИБКА HTTP: {e.response.status_code}")
        print(f"   Ответ сервера: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ: Не удалось подключиться к серверу.")
        print(f"   Убедитесь, что сервер запущен по адресу {BASE_URL} и доступен.")
        print(f"   Детали: {e}")
    except Exception as e:
        print(f"\n❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")


if __name__ == "__main__":
    create_user()