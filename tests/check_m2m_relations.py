import requests
import time
import sys
import json
from typing import Set

# --- НАСТРОЙКИ ---
BASE_URL = "http://89.111.169.47:8005"
EMAIL = "1@example.com"
PASSWORD = "string"
# -----------------

# --- Вспомогательные функции ---
test_failed = False


def print_status(ok, message):
    global test_failed
    if ok:
        print(f"✅ [OK] {message}")
    else:
        print(f"❌ [FAIL] {message}\n"); test_failed = True


def print_header(title):
    print("\n" + "=" * 60);
    print(f" {title} ".center(60, "="));
    print("=" * 60)


def login():
    try:
        r = requests.post(f"{BASE_URL}/api/auth/token", data={'username': EMAIL, 'password': PASSWORD})
        r.raise_for_status()
        return {'Authorization': f'Bearer {r.json()["access_token"]}'}
    except Exception as e:
        print(f"Критическая ошибка при авторизации: {e}"); return None


# --- Основная функция демонстрации ---
def run_m2m_test():
    headers = login()
    if not headers: return

    ids = {}

    try:
        # --- ШАГ 1: ПОДГОТОВКА ---
        print_header("Шаг 1: Создание таблиц 'Студенты' и 'Курсы'")
        students_name = f"students_m2m_{int(time.time())}"
        courses_name = f"courses_m2m_{int(time.time())}"
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": students_name, "display_name": "Студенты (M2M)"})
        resp.raise_for_status();
        ids['students_table'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types", headers=headers,
                             json={"name": courses_name, "display_name": "Курсы (M2M)"})
        resp.raise_for_status();
        ids['courses_table'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['students_table']['id']}/attributes",
                             headers=headers,
                             json={"name": "student_name", "display_name": "Имя студента", "value_type": "string"})
        resp.raise_for_status();
        ids['student_name_attr'] = resp.json()
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['courses_table']['id']}/attributes",
                             headers=headers,
                             json={"name": "course_title", "display_name": "Название курса", "value_type": "string"})
        resp.raise_for_status();
        ids['course_title_attr'] = resp.json()
        print_status(True, "Подготовительный этап завершен.")

        # --- ШАГ 2: СОЗДАНИЕ M2M СВЯЗИ ---
        print_header("Шаг 2: Создание двусторонней M2M связи")
        payload = {
            "name": "student_courses", "display_name": "Курсы студента", "value_type": "relation",
            "relation_type": "many-to-many",  # <--- Указываем новый тип
            "target_entity_type_id": ids['courses_table']['id'],
            "display_attribute_id": ids['course_title_attr']['id'],
            "create_back_relation": True,
            "back_relation_name": "course_students", "back_relation_display_name": "Студенты на курсе",
            "back_relation_display_attribute_id": ids['student_name_attr']['id']
        }
        resp = requests.post(f"{BASE_URL}/api/meta/entity-types/{ids['students_table']['id']}/attributes",
                             headers=headers, json=payload)
        resp.raise_for_status();
        ids['student_courses_attr'] = resp.json()
        print_status(True, "Запрос на создание M2M связи успешно выполнен.")

        # --- ШАГ 3: НАПОЛНЕНИЕ ДАННЫМИ ---
        print_header("Шаг 3: Наполнение таблиц данными")
        resp = requests.post(f"{BASE_URL}/api/data/{students_name}", headers=headers, json={"student_name": "Иван"});
        resp.raise_for_status();
        ids['ivan'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{students_name}", headers=headers, json={"student_name": "Мария"});
        resp.raise_for_status();
        ids['maria'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{courses_name}", headers=headers,
                             json={"course_title": "Математика"});
        resp.raise_for_status();
        ids['math'] = resp.json()['data'][0]
        resp = requests.post(f"{BASE_URL}/api/data/{courses_name}", headers=headers, json={"course_title": "История"});
        resp.raise_for_status();
        ids['history'] = resp.json()['data'][0]
        print_status(True, "Созданы 2 студента и 2 курса.")

        # --- ШАГ 4: УСТАНОВКА СВЯЗЕЙ ---
        print_header("Шаг 4: Установка M2M связей")
        # Записываем Ивана на Математику и Историю
        ivan_courses_ids = [ids['math']['id'], ids['history']['id']]
        resp = requests.put(f"{BASE_URL}/api/data/{students_name}/{ids['ivan']['id']}", headers=headers,
                            json={"student_courses": ivan_courses_ids})
        resp.raise_for_status();
        print_status(True, "Иван записан на 2 курса.")
        # Записываем Марию только на Математику
        maria_courses_ids = [ids['math']['id']]
        resp = requests.put(f"{BASE_URL}/api/data/{students_name}/{ids['maria']['id']}", headers=headers,
                            json={"student_courses": maria_courses_ids})
        resp.raise_for_status();
        print_status(True, "Мария записана на 1 курс.")

        # --- ШАГ 5: ФИНАЛЬНАЯ ПРОВЕРКА ---
        print_header("Шаг 5: Проверка отображения M2M связей")

        # Проверяем Ивана
        resp = requests.get(f"{BASE_URL}/api/data/{students_name}/{ids['ivan']['id']}", headers=headers);
        ivan_details = resp.json()
        ivan_courses: Set[str] = set(ivan_details.get('student_courses', []))
        print(f" -> Курсы Ивана: {ivan_courses}")
        print_status(ivan_courses == {"Математика", "История"}, "У Ивана корректно отображаются 2 курса.")

        # Проверяем Марию
        resp = requests.get(f"{BASE_URL}/api/data/{students_name}/{ids['maria']['id']}", headers=headers);
        maria_details = resp.json()
        maria_courses: Set[str] = set(maria_details.get('student_courses', []))
        print(f" -> Курсы Марии: {maria_courses}")
        print_status(maria_courses == {"Математика"}, "У Марии корректно отображается 1 курс.")

        # Проверяем курс Математики (обратная связь)
        resp = requests.get(f"{BASE_URL}/api/data/{courses_name}/{ids['math']['id']}", headers=headers);
        math_details = resp.json()
        math_students: Set[str] = set(math_details.get('course_students', []))
        print(f" -> Студенты на Математике: {math_students}")
        print_status(math_students == {"Иван", "Мария"}, "На Математике корректно отображаются 2 студента.")

        # Проверяем курс Истории (обратная связь)
        resp = requests.get(f"{BASE_URL}/api/data/{courses_name}/{ids['history']['id']}", headers=headers);
        history_details = resp.json()
        history_students: Set[str] = set(history_details.get('course_students', []))
        print(f" -> Студенты на Истории: {history_students}")
        print_status(history_students == {"Иван"}, "На Истории корректно отображается 1 студент.")

    except requests.exceptions.HTTPError as e:
        print_status(False, f"Критическая ошибка HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_status(False, f"Произошла непредвиденная ошибка: {e}")
    finally:
        # --- ОЧИСТКА ---
        print_header("Очистка (удаление тестовых таблиц)")
        if 'students_table' in ids:
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['students_table']['id']}", headers=headers)
            print(f" -> Таблица 'Студенты (M2M)' удалена.")
        if 'courses_table' in ids:
            requests.delete(f"{BASE_URL}/api/meta/entity-types/{ids['courses_table']['id']}", headers=headers)
            print(f" -> Таблица 'Курсы (M2M)' удалена.")

        if not test_failed:
            print("\n" + "🎉" * 20 + "\n Все тесты Many-to-Many связей успешно пройдены! \n" + "🎉" * 20)
        else:
            sys.exit(1)


if __name__ == "__main__":
    run_m2m_test()