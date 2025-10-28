import requests
import time
import sys
import json
import os
from typing import List, Dict, Any, Optional

# --- НАСТРОЙКИ ---
# Замените на ваш URL, email и пароль
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Глобальные переменные для теста ---
test_failed = False
# Уникальное имя для тестовой таблицы
NEW_TABLE_NAME = f"import_test_{int(time.time())}"
TEST_CSV_FILENAME = "test_import_data.csv"


# --- Вспомогательные функции (можно скопировать из другого теста) ---

def print_status(ok: bool, message: str, data: Optional[Any] = None):
    """Выводит статус теста и устанавливает флаг ошибки."""
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}")
        if data:
            try:
                print(f"  └─ Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except (TypeError, json.JSONDecodeError):
                print(f"  └─ Ответ сервера: {data}")
        print("")
        test_failed = True


def print_header(title: str):
    """Выводит красивый заголовок для каждого тестового блока."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def login() -> Optional[Dict[str, str]]:
    """Аутентифицируется и возвращает заголовки для последующих запросов."""
    try:
        url = f"{BASE_URL}/api/auth/token"
        r = requests.post(url, data={'username': EMAIL, 'password': PASSWORD})
        r.raise_for_status()
        print_status(True, "Авторизация прошла успешно")
        return {'Authorization': f'Bearer {r.json()["access_token"]}'}
    except Exception as e:
        print_status(False, f"Критическая ошибка при авторизации: {e}", getattr(e, 'response', 'N/A'))
        return None


# --- Основные функции теста ---

def create_test_csv():
    """Создает временный, более сложный CSV-файл для теста."""
    csv_content = (
        '"Ref ID","Компания","Дата сделки","Выручка","Кол-во лицензий","Активен","Рейтинг (1-5)","Комментарий"\n'
        '"ID-001","ООО ""Альфа, Гамма""","15.01.2024","150000.50","10","true","5","Все хорошо, оплата прошла"\n'
        '"ID-002","ИП Сидоров А.Б.","20/11/2023","85000","5","Да","4",""\n'
        '"ID-003","ЗАО \'Вектор\'","2024-03-30","","1","no","3","Нужно перезвонить"\n'
        '"ID-004","ОАО ""Техно-Строй""","01 Aug 2022","320000.00","25","1","",""\n'
        '"ID-005","Интернет-магазин ""Все для дома""","10-02-2024","999.90","1","Yes","5","Срочный заказ"\n'
        '"ID-006","Пустая строка","","","","","","Эта строка содержит только текст"\n'
        '"ID-007","Нулевые значения","12.12.2025","0","0","0","1",""\n'
    )
    with open(TEST_CSV_FILENAME, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    print_status(True, f"Тестовый файл '{TEST_CSV_FILENAME}' (сложная версия) создан.")


def run_import_test(headers: Dict[str, str]) -> Optional[int]:
    """Выполняет полный цикл импорта и возвращает ID созданной таблицы."""
    created_table_id = None
    try:
        # --- Шаг 1: Загрузка файла ---
        print_header("Шаг 1: Загрузка файла на сервер")
        url_upload = f"{BASE_URL}/api/imports/upload"

        with open(TEST_CSV_FILENAME, 'rb') as f:
            files = {'file': (TEST_CSV_FILENAME, f, 'text/csv')}
            response_upload = requests.post(url_upload, headers=headers, files=files)

        response_upload.raise_for_status()
        upload_data = response_upload.json()

        file_id = upload_data.get("file_id")
        headers_from_file = upload_data.get("headers")

        # --- ИСПРАВЛЕНИЕ 1: Проверяем на 8 колонок ---
        ok = file_id and headers_from_file and len(headers_from_file) == 8
        print_status(ok, f"Файл успешно загружен. Получен file_id: {file_id}. Распознано колонок: {len(headers_from_file)}")
        if not ok: return None

        # --- Шаг 2: Формирование конфигурации и запуск обработки ---
        print_header("Шаг 2: Отправка конфигурации и запуск импорта")

        import_config = {
            "new_table_name": NEW_TABLE_NAME,
            "new_table_display_name": "Сложный импорт",
            "columns": []
        }
        for header_info in headers_from_file:
            original_header = header_info['original_header']
            # Включаем все колонки, кроме "Комментарий"
            do_import = "Комментарий" not in original_header

            import_config["columns"].append({
                "original_header": original_header,
                "display_name": original_header,  # Оставляем оригинальное имя
                "value_type": header_info['suggested_type'],  # Используем предложенный тип
                "do_import": do_import
            })

        url_process = f"{BASE_URL}/api/imports/process/{file_id}"
        response_process = requests.post(url_process, headers=headers, json=import_config)
        response_process.raise_for_status()
        print_status(True, f"Фоновая задача на импорт успешно запущена.")

        # --- Шаг 3: Ожидание и проверка результата ---
        print_header("Шаг 3: Ожидание и проверка результата")
        print("-> Ждем 15 секунд, пока Celery обработает файл...")
        time.sleep(15)

        # Проверяем, появилась ли таблица
        url_get_tables = f"{BASE_URL}/api/meta/entity-types"
        response_tables = requests.get(url_get_tables, headers=headers)
        tables_data = response_tables.json()

        new_table_meta = next((tbl for tbl in tables_data if tbl['name'] == NEW_TABLE_NAME), None)

        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        if new_table_meta:
            print_status(True, f"Новая таблица '{NEW_TABLE_NAME}' найдена в метаданных.")
            created_table_id = new_table_meta['id']
        else:
            print_status(False, f"Тест провален: таблица '{NEW_TABLE_NAME}' не была создана Celery за 15 секунд.",
                         tables_data)
            return None  # Выходим из теста, если таблица не создана
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        # Проверяем данные в новой таблице
        url_get_data = f"{BASE_URL}/api/data/{NEW_TABLE_NAME}"
        response_data = requests.get(url_get_data, headers=headers)
        imported_data = response_data.json()

        total_rows = imported_data.get('total', 0)
        ok_rows_count = total_rows == 3
        print_status(ok_rows_count, f"В новой таблице создано {total_rows} строк (ожидалось 3).")

        # Проверяем содержимое второй строки (у которой нет суммы)
        # Данные могут приходить в разном порядке, найдем нужную строку
        target_row = next((row for row in imported_data.get('data', []) if row.get('imya_klienta') == "ЗАО 'Лютик'"),
                          None)

        ok_content = False
        if target_row:
            # Убеждаемся, что колонка 'summa_kontrakta' отсутствует, так как значение было пустым
            ok_content = 'summa_kontrakta' not in target_row

        print_status(ok_content,
                     "Содержимое строки с пропущенным значением соответствует ожиданиям (поле отсутствует).")

        return created_table_id

    except Exception as e:
        print_status(False, "Тест импорта провалился на одном из шагов",
                     getattr(e, 'response', 'N/A').text if hasattr(e, 'response') else str(e))
        return created_table_id


def cleanup(headers: Dict[str, str], table_id: Optional[int]):
    """Удаляет временный CSV и созданную таблицу."""
    if os.path.exists(TEST_CSV_FILENAME):
        os.remove(TEST_CSV_FILENAME)
        print_status(True, f"Временный файл '{TEST_CSV_FILENAME}' удален.")

    if table_id:
        try:
            print_header("Очистка: удаление тестовой таблицы")
            url_delete = f"{BASE_URL}/api/meta/entity-types/{table_id}"
            r = requests.delete(url_delete, headers=headers)
            print_status(r.status_code == 204, f"Тестовая таблица '{NEW_TABLE_NAME}' (ID: {table_id}) удалена.")
        except Exception as e:
            print_status(False, "Ошибка на этапе очистки таблицы", getattr(e, 'response', 'N/A').text)


def main():
    """Главная функция для запуска всех тестов."""
    print_header("Авторизация")
    headers = login()
    if not headers:
        sys.exit(1)

    created_table_id = None
    create_test_csv()  # Создаем файл до начала теста
    try:
        created_table_id = run_import_test(headers)
    finally:
        # cleanup(headers, created_table_id)  # Очищаем все в любом случае

        print_header("Итоги тестирования")
        if test_failed:
            print("❌ Тестирование импорта завершилось с ошибками.")
            sys.exit(1)
        else:
            print("✅ Тест импорта прошел успешно!")


if __name__ == "__main__":
    main()