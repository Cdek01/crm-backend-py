# import requests
#
#
# def get_statements_with_token(access_token, account_id=None):
#     """Простая функция для получения выписок с готовым токеном"""
#     url = "https://enter.tochka.com/uapi/open-banking/v1.0/statements"
#
#     headers = {
#         'Accept': 'application/json',
#         'Authorization': f'Bearer {access_token}'
#     }
#
#     params = {}
#     if account_id:
#         params['accountId'] = account_id
#
#     try:
#         response = requests.get(url, headers=headers, params=params)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.HTTPError as e:
#         print(f"Ошибка: {e}")
#         print(f"Ответ сервера: {e.response.text}")
#         return None
#
#
# # Использование
# if __name__ == "__main__":
#     ACCESS_TOKEN = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1Mjc2ODVkZDNkNzMyOTQ5ODg2NzYzNTY3ZTQzYTRjMyIsInN1YiI6IjQ4ZDU0ZTJkLWYyMzgtNDUwNy04OThlLWNlYTRhMzhlNTFjMSIsImN1c3RvbWVyX2NvZGUiOiIzMDMxMDgxNDQifQ.Dxn0lfJ8mzGZ665nhdQLE3clqFjVU_NcGcCgRnWY6T7TaWtUqeqMohXGUcEmBI9kA8FgzWXzGUl9R1BAXXLqmCg6mHreXMPoN3guuHjGAqpQnu0QmigUlA2oVvactGFSWGtLI1Jtzlu2vShC2lAdC5nX1VSoSgRLGFQWUjIXYUMjafTM2vVN3QicMhMYkCO0_qK_c6qHNpQ7NiuV_i5EMP2j7Vf7IHorHDJzXgZ5udX7SpjrvPLhsrVbLRZ7S4-3VVcwEApT64ih-HGcKARq8IPs3TUGZC-84QKpLM7efD4TgtjWPovbEhYUNrLL4wcy0teIdsbFVEnhCxywGNEA1frNlo_KUOYu32Q_P-F9hA34ApDPDaPlJ44l4EM4OajI2A2ruurebe1eFtApq3gtNLruiuHfAWrWNHmjD5OFXr8FLd1FM4ksQGuskrbfufP_7UG2Z4BGuAjODwTO7rCUq1OCA_sLuXnUDtd_FECr9S4i8egvSHe0CBPStZOCuwPd'
#
#
#     statements = get_statements_with_token(ACCESS_TOKEN)
#     if statements:
#         print("Выписки успешно получены!", statements)
#         # Обработка данных выписок
#         for statement in statements.get('Data', {}).get('Statement', []):
#             print(f"Счет: {statement.get('accountId')}")
#             # Дополнительная обработка...

import requests
from datetime import datetime, timedelta
import json


def get_statements_with_token(access_token, account_id=None, days_back=30):
    """Получение выписок с готовым токеном и диагностикой"""
    url = "https://enter.tochka.com/uapi/open-banking/v1.0/statements"

    # Формируем даты (последние N дней)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'startDateTime': start_date.isoformat(),
        'endDateTime': end_date.isoformat()
    }

    if account_id:
        params['accountId'] = account_id

    try:
        print(f"Отправляем запрос с параметрами: {params}")
        response = requests.get(url, headers=headers, params=params)
        print(f"HTTP статус: {response.status_code}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e}")
        if e.response.status_code == 401:
            print("Ошибка аутентификации: неверный или просроченный токен")
        elif e.response.status_code == 403:
            print("Ошибка авторизации: недостаточно прав")
        elif e.response.status_code == 404:
            print("Ресурс не найден: проверьте URL и параметры")
        print(f"Ответ сервера: {e.response.text}")
        return None
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return None


def get_accounts(access_token):
    """Получение списка счетов"""
    url = "https://enter.tochka.com/uapi/open-banking/v1.0/accounts"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        print("Запрашиваем список счетов...")
        response = requests.get(url, headers=headers)
        print(f"HTTP статус для счетов: {response.status_code}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"Ошибка при получении счетов: {e}")
        print(f"Ответ сервера: {e.response.text}")
        return None


def debug_token(access_token):
    """Диагностика токена (без раскрытия чувствительной информации)"""
    try:
        # Базовая проверка формата JWT
        parts = access_token.split('.')
        if len(parts) == 3:
            print("✓ Токен имеет правильный JWT формат")
            # Декодируем payload (вторая часть)
            import base64
            import json as json_lib
            payload = parts[1]
            # Добавляем padding если нужно
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            decoded_payload = base64.b64decode(payload)
            token_info = json_lib.loads(decoded_payload)
            print("✓ Информация из токена:")
            print(f"  - Customer code: {token_info.get('customer_code', 'не указан')}")
            print(f"  - Issuer: {token_info.get('iss', 'не указан')}")
            print(f"  - Subject: {token_info.get('sub', 'не указан')[:20]}...")
        else:
            print("✗ Токен имеет неверный формат")
    except Exception as e:
        print(f"Ошибка при анализе токена: {e}")


# Основная программа
if __name__ == "__main__":
    ACCESS_TOKEN = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1Mjc2ODVkZDNkNzMyOTQ5ODg2NzYzNTY3ZTQzYTRjMyIsInN1YiI6IjQ4ZDU0ZTJkLWYyMzgtNDUwNy04OThlLWNlYTRhMzhlNTFjMSIsImN1c3RvbWVyX2NvZGUiOiIzMDMxMDgxNDQifQ.Dxn0lfJ8mzGZ665nhdQLE3clqFjVU_NcGcCgRnWY6T7TaWtUqeqMohXGUcEmBI9kA8FgzWXzGUl9R1BAXXLqmCg6mHreXMPoN3guuHjGAqpQnu0QmigUlA2oVvactGFSWGtLI1Jtzlu2vShC2lAdC5nX1VSoSgRLGFQWUjIXYUMjafTM2vVN3QicMhMYkCO0_qK_c6qHNpQ7NiuV_i5EMP2j7Vf7IHorHDJzXgZ5udX7SpjrvPLhsrVbLRZ7S4-3VVcwEApT64ih-HGcKARq8IPs3TUGZC-84QKpLM7efD4TgtjWPovbEhYUNrLL4wcy0teIdsbFVEnhCxywGNEA1frNlo_KUOYu32Q_P-F9hA34ApDPDaPlJ44l4EM4OajI2A2ruurebe1eFtApq3gtNLruiuHfAWrWNHmjD5OFXr8FLd1FM4ksQGuskrbfufP_7UG2Z4BGuAjODwTO7rCUq1OCA_sLuXnUDtd_FECr9S4i8egvSHe0CBPStZOCuwPd'

    print("=== ДИАГНОСТИКА ТОКЕНА ===")
    debug_token(ACCESS_TOKEN)

    print("\n=== ПОЛУЧЕНИЕ СПИСКА СЧЕТОВ ===")
    accounts = get_accounts(ACCESS_TOKEN)

    if accounts:
        print("Счета получены успешно!")
        account_list = accounts.get('Data', {}).get('Account', [])
        print(f"Найдено счетов: {len(account_list)}")

        for i, account in enumerate(account_list, 1):
            account_id = account.get('accountId')
            currency = account.get('currency', 'RUB')
            status = account.get('status', 'неизвестно')
            print(f"{i}. Счет: {account_id}")
            print(f"   Валюта: {currency}, Статус: {status}")

            # Получаем выписки для каждого счета
            print(f"   Запрашиваем выписки для счета...")
            statements = get_statements_with_token(ACCESS_TOKEN, account_id=account_id)

            if statements and statements.get('Data', {}).get('Statement'):
                statement_list = statements['Data']['Statement']
                print(f"   Найдено выписок: {len(statement_list)}")
                for statement in statement_list:
                    print(f"   - Выписка {statement.get('statementId')}: "
                          f"{statement.get('startDateTime')} - {statement.get('endDateTime')}")
            else:
                print("   Выписок не найдено")
            print()

    else:
        print("Не удалось получить список счетов")
        # Пробуем получить выписки без указания счета
        print("\n=== ПОПЫТКА ПОЛУЧЕНИЯ ВЫПИСОК БЕЗ УКАЗАНИЯ СЧЕТА ===")
        statements = get_statements_with_token(ACCESS_TOKEN)
        if statements:
            print("Ответ сервера:", json.dumps(statements, indent=2, ensure_ascii=False))



