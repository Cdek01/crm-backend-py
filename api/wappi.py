# api/wappi.py

import requests
import base64
import os

# --- ИМПОРТИРУЕМ НАШ ОБЪЕКТ НАСТРОЕК ---
from core.config import settings


def api(nomer, text):
    # --- ИСПОЛЬЗУЕМ ЗНАЧЕНИЯ ИЗ НАСТРОЕК ---
    API_KEY = settings.API_KEY_WAPPI
    PROFILE_ID = settings.PROFILE_ID_WAPPI

    # URL для отправки ТЕКСТОВОГО сообщения
    url = f'https://wappi.pro/api/async/message/send?profile_id={PROFILE_ID}'

    # Заголовки для запроса
    headers = {
        'Authorization': f'{API_KEY}',
        'Content-Type': 'application/json'
    }

    # Проверка на наличие '7' в начале номера телефона
    if not nomer.startswith('7'):
        nomer = '7' + nomer

    # Тело запроса для текстового сообщения
    data = {
        "recipient": nomer,
        "body": text  # Ключ для текста - 'body'
    }

    # Отправка запроса
    try:
        print(f"Отправка текста '{text}' на номер {nomer}...")
        response = requests.post(url, headers=headers, json=data)

        # Проверяем на ошибки HTTP (4xx, 5xx)
        response.raise_for_status()

        print(f'Успех: {response.status_code}, {response.text}')
        return False  # Ошибки нет

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP ошибка при отправке на {nomer}: {http_err} - {response.text}')
        return True  # Есть ошибка
    except Exception as err:
        print(f'Произошла другая ошибка при отправке на {nomer}: {err}')
        return True  # Есть ошибка