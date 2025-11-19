import requests
import json
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
# ВАЖНО: Вставьте сюда ваш РЕАЛЬНЫЙ, ПРАВИЛЬНО СГЕНЕРИРОВАННЫЙ токен
REAL_MODULBANK_TOKEN = "MGIwMjlmZjEtMjM2MC00ZWJmLWE4NTktNmI1ZDA4Y2RmYWE4NmRjOTQ0MGYtYzUzNi00MGQ3LWIwNmYtZDZmNDQxZjlmMDFl"


# --- КОНЕЦ КОНФИГУРАЦИИ ---

def check_api():
    """
    Делает тестовые запросы к API Модульбанка для проверки токена и прав.
    """
    print(">>> НАЧАЛО ПРОВЕРКИ API МОДУЛЬБАНКА <<<")

    if "ВАШ_НОВЫЙ_ТОКЕН" in REAL_MODULBANK_TOKEN:
        print("\n[ОШИБКА] Пожалуйста, вставьте ваш реальный API токен в переменную REAL_MODULBANK_TOKEN.")
        return

    headers = {'Authorization': f'Bearer {REAL_MODULBANK_TOKEN}'}

    # --- Шаг 1: Проверка получения счетов (требует 'account-info') ---
    print("\n--- Шаг 1: Запрос списка банковских счетов... ---")
    accounts_url = "https://api.modulbank.ru/v1/account-info"

    try:
        response_acc = requests.get(accounts_url, headers=headers, timeout=10)
        # Проверяем на ошибки (4xx, 5xx)
        response_acc.raise_for_status()

        accounts = response_acc.json()
        print(f"[OK] Успешно получен список из {len(accounts)} счетов.")

        # Выводим информацию о первом счете для наглядности
        if accounts:
            print("    Информация о первом счете:")
            print(json.dumps(accounts[0], indent=2, ensure_ascii=False))
            first_account_id = accounts[0]['id']
        else:
            print("[ПРЕДУПРЕЖДЕНИЕ] Список счетов пуст. Дальнейшая проверка операций невозможна.")
            return

    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Ошибка при запросе счетов! Статус: {e.response.status_code if e.response else 'N/A'}")
        print(f"       Текст ошибки: {e.response.text if e.response else e}")
        print("       Возможная причина: токен недействителен или отсутствует право 'account-info'.")
        return

    # --- Шаг 2: Проверка получения операций (требует 'operation-history') ---
    print("\n--- Шаг 2: Запрос операций для первого счета за последние 30 дней... ---")
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')
    operations_url = f"https://api.modulbank.ru/v1/bank-accounts/{first_account_id}/operations?from={from_date}"

    try:
        response_ops = requests.get(operations_url, headers=headers, timeout=10)
        response_ops.raise_for_status()

        operations = response_ops.json()
        print(f"[OK] Успешно получено {len(operations)} операций.")

        if operations:
            print("    Информация о последней операции:")
            print(json.dumps(operations[-1], indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Ошибка при запросе операций! Статус: {e.response.status_code if e.response else 'N/A'}")
        print(f"       Текст ошибки: {e.response.text if e.response else e}")
        print("       Возможная причина: у токена отсутствует право 'operation-history'.")
        return

    print("\n>>> ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО! Токен валиден и имеет необходимые права. <<<")


if __name__ == "__main__":
    check_api()