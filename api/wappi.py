# api/wappi.py

import requests
import base64
import os

# --- ИМПОРТИРУЕМ НАШ ОБЪЕКТ НАСТРОЕК ---
from core.config import settings


def api(nomer, text, folder_path):
    # --- ИСПОЛЬЗУЕМ ЗНАЧЕНИЯ ИЗ НАСТРОЕК ---
    API_KEY = settings.API_KEY_WAPPI
    PROFILE_ID = settings.PROFILE_ID_WAPPI

    url = f'https://wappi.pro/api/async/message/document/send?profile_id={PROFILE_ID}'

    # Заголовки для запроса
    headers = {
        'Authorization': f'{API_KEY}',
        'Content-Type': 'application/json'
    }

    # Проверка на наличие '7' в начале номера телефона
    if not nomer.startswith('7'):
        nomer = '7' + nomer  # Добавляем '7' в начало номера

    # Параметры для отправки
    recipient = nomer  # Номер получателя
    caption = text  # Заголовок документа
    file_name = folder_path  # Имя файла (без пути)

    # --- УЛУЧШЕНИЕ: Сделаем путь к папке загрузок настраиваемым ---
    # Допустим, мы хотим, чтобы путь был не жестко прописан,
    # а брался из настроек или передавался как аргумент.
    # Пока оставим ваш вариант для простоты.
    full_file_path = os.path.join("C:/Users/mikfo/Downloads/", file_name)

    # Проверка существования файла
    if not os.path.exists(full_file_path):
        print(f"Файл не найден: {full_file_path}")
        # Возвращаем ошибку, если файла нет
        return True

    # Чтение файла и его кодирование в base64
    with open(full_file_path, "rb") as file:
        b64_file = base64.b64encode(file.read()).decode('utf-8')

    # Тело запроса
    data = {
        "recipient": recipient,
        "caption": caption,
        "file_name": file_name,
        "b64_file": b64_file
    }

    # Отправка запроса
    try:
        response = requests.post(url, headers=headers, json=data)
        # Проверяем на ошибки HTTP
        response.raise_for_status()

        print(nomer, text, folder_path)
        print(f'Успех: {response.status_code}, {response.text}')
        return False

    except requests.exceptions.HTTPError as http_err:
        print(nomer, text, folder_path)
        print(f'HTTP ошибка: {http_err} - {response.text}')
        return True
    except Exception as err:
        print(nomer, text, folder_path)
        print(f'Произошла другая ошибка: {err}')
        return True