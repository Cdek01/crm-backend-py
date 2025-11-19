import requests
import json
from datetime import datetime, timedelta

REAL_MODULBANK_TOKEN = "MGIwMjlmZjEtMjM2MC00ZWJmLWE4NTktNmI1ZDA4Y2RmYWE4NmRjOTQ0MGYtYzUzNi00MGQ3LWIwNmYtZDZmNDQxZjlmMDFl"

def check_all_companies_operations():
    print(">>> СБОР ОПЕРАЦИЙ ПО ВСЕМ КОМПАНИЯМ <<<")
    headers = {'Authorization': f'Bearer {REAL_MODULBANK_TOKEN}'}

    # 1. Загружаем список компаний
    print("\n--- Шаг 1: Загружаем список компаний и счетов ---")
    account_info_url = "https://api.modulbank.ru/v1/account-info"

    try:
        response_acc = requests.post(account_info_url, headers=headers, timeout=10)
        response_acc.raise_for_status()

        companies = response_acc.json()
        print(f"[OK] Найдено компаний: {len(companies)}")

    except Exception as e:
        print("[FAIL] Ошибка при загрузке компаний:", e)
        return

    # 2. Идём по каждой компании
    all_operations = []

    for company in companies:
        company_name = company.get("name", "Без имени")
        print(f"\n=== Компания: {company_name} ===")

        bank_accounts = company.get("bankAccounts", [])

        if not bank_accounts:
            print("  ❗ У компании нет счетов")
            continue

        # 3. Идём по каждому счёту этой компании
        for acc in bank_accounts:
            account_id = acc["id"]
            acc_number = acc["number"]
            print(f"  --- Счёт {acc_number} (ID: {account_id}) ---")

            # Параметры периода
            from_date = (datetime.now() - timedelta(days=30)).isoformat()

            operations_url = f"https://api.modulbank.ru/v1/operation-history/{account_id}"
            payload = {
                "from": from_date,
                "records": 50
            }

            try:
                response_ops = requests.post(operations_url, headers=headers, json=payload, timeout=10)
                response_ops.raise_for_status()

                operations = response_ops.json()
                print(f"      Получено операций: {len(operations)}")

                # добавляем в общий список с указанием компании и счета
                all_operations.append({
                    "company": company_name,
                    "account": acc_number,
                    "operations": operations
                })

            except Exception as e:
                print(f"      [FAIL] Ошибка для счета {acc_number}: {e}")

    print("\n>>> ГОТОВО! Сбор данных завершён. <<<")
    return all_operations


if __name__ == "__main__":
    data = check_all_companies_operations()
    print("\nРЕЗУЛЬТАТ:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
