import requests
import json
import time
from urllib.parse import quote


class BeelineCloudPBX:
    def __init__(self, base_url, api_token):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'X-MPBX-API-AUTH-TOKEN': api_token,
            'Content-Type': 'application/json'
        }

    def get_abonents(self):
        """Получение списка всех абонентов"""
        url = f"{self.base_url}/abonents"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Ошибка получения абонентов: {response.status_code}")
            print(response.text)
            return None

    def get_abonent_details(self, pattern):
        """Получение детальной информации об абоненте"""
        url = f"{self.base_url}/abonents/{quote(pattern)}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Ошибка получения информации об абоненте: {response.status_code}")
            return None

    def enable_recording(self, pattern):
        """Включение записи разговоров"""
        url = f"{self.base_url}/abonents/{quote(pattern)}/recording"
        response = requests.put(url, headers=self.headers)

        if response.status_code == 200:
            print("✅ Запись разговоров успешно включена")
            return True
        else:
            print(f"❌ Ошибка включения записи: {response.status_code}")
            print(response.text)
            return False

    def make_call(self, pattern, phone_number):
        """
        Совершение вызова через V2 API
        POST /v2/abonents/{pattern}/call
        """
        url = f"{self.base_url}/v2/abonents/{quote(pattern)}/call"
        params = {'phoneNumber': phone_number}

        print(f"📞 Вызов с {pattern} на {phone_number}")

        try:
            response = requests.post(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Вызов успешно инициирован!")
                print(f"   Call ID: {result.get('callId')}")
                print(f"   External Tracking ID: {result.get('externalTrackingId')}")
                return result
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("❌ Таймаут при выполнении запроса")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети: {e}")
            return None

    def check_call_status(self, call_id):
        """
        Попытка проверить статус звонка
        (Этот endpoint нужно уточнить в документации)
        """
        possible_endpoints = [
            f"{self.base_url}/v2/calls/{call_id}",
            f"{self.base_url}/calls/{call_id}",
            f"{self.base_url}/call/{call_id}",
        ]

        for endpoint in possible_endpoints:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Найден endpoint для статуса: {endpoint}")
                    return response.json()
            except:
                continue

        return None


def diagnose_abonent_issue(pbx, pattern):
    """Диагностика проблем с абонентом"""
    print("\n🔍 ДИАГНОСТИКА АБОНЕНТА:")

    # 1. Проверяем детали абонента
    details = pbx.get_abonent_details(pattern)
    if not details:
        print("❌ Не удалось получить детали абонента")
        return False

    print(f"✅ Детали абонента: {details}")

    # 2. Проверяем статус записи
    url = f"{pbx.base_url}/abonents/{quote(pattern)}/recording"
    response = requests.get(url, headers=pbx.headers)
    if response.status_code == 200:
        recording_status = response.json()
        print(f"✅ Статус записи: {recording_status}")
    else:
        print(f"❌ Не удалось получить статус записи: {response.status_code}")

    return True


def test_call_flow(pbx, pattern, phone_number):
    """Тестирование полного цикла звонка"""
    print(f"\n🎯 ТЕСТ ЗВОНКА: {pattern} -> {phone_number}")

    # 1. Включаем запись
    print("\n1. 🔴 Включение записи...")
    if not pbx.enable_recording(pattern):
        print("⚠️  Продолжаем без записи")

    # 2. Совершаем вызов
    print("\n2. 📞 Инициирование вызова...")
    call_result = pbx.make_call(pattern, phone_number)

    if not call_result:
        print("❌ Не удалось инициировать вызов")
        return False

    call_id = call_result.get('callId')
    print(f"✅ Вызов инициирован, Call ID: {call_id}")

    # 3. Мониторинг статуса
    print("\n3. ⏳ Мониторинг статуса...")
    for i in range(1, 31):  # 30 попыток по 2 секунды = 60 секунд
        print(f"   {i}/30 - Прошло {i * 2} секунд...")

        # Пытаемся проверить статус каждые 10 секунд
        if i % 5 == 0:
            status = pbx.check_call_status(call_id)
            if status:
                print(f"   📊 Статус звонка: {status}")

        time.sleep(2)

    print("\n⏰ Время мониторинга истекло")
    return True


def main():
    # Конфигурация
    BASE_URL = "https://cloudpbx.beeline.ru/apis/portal"
    API_TOKEN = "f0744ced-44e3-4d88-9ec7-f7823d83d634"

    # Инициализация клиента
    pbx = BeelineCloudPBX(BASE_URL, API_TOKEN)

    try:
        print("=== Билайн Cloud PBX - Улучшенная диагностика ===\n")

        # 1. Получаем список абонентов
        print("1. 📋 Получение списка абонентов...")
        abonents = pbx.get_abonents()

        if not abonents:
            print("❌ Не удалось получить список абонентов")
            return

        print(f"✅ Найдено абонентов: {len(abonents)}")
        abonent = abonents[0]
        pattern = abonent.get('userId')
        extension = abonent.get('extension', 'N/A')

        print(f"🎯 Основной абонент: {pattern} (добавочный: {extension})")

        # 2. Диагностика абонента
        if not diagnose_abonent_issue(pbx, pattern):
            return

        # 3. Тестируем звонки на разные номера
        test_numbers = [
            "+79952116323",  # Основной тестовый номер
            "9952116323",  # Бесплатный номер Билайн
        ]

        for i, test_number in enumerate(test_numbers, 1):
            print(f"\n{'=' * 60}")
            print(f"🚀 ТЕСТ {i}: {test_number}")
            print(f"{'=' * 60}")

            success = test_call_flow(pbx, pattern, test_number)

            if success:
                print(f"✅ Тест {i} завершен успешно")
            else:
                print(f"❌ Тест {i} завершен с ошибками")

            # Пауза между тестами
            if i < len(test_numbers):
                print("⏳ Ждем 10 секунд перед следующим тестом...")
                time.sleep(10)

        print("\n📊 ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("\n💡 РЕКОМЕНДАЦИИ:")
        print("1. Проверьте, что SIP устройство с добавочным 200 включено и в сети")
        print("2. Убедитесь, что на устройстве настроена регистрация в Cloud PBX")
        print("3. Проверьте баланс и ограничения тарифного плана")
        print("4. Обратитесь в поддержку Билайн для уточнения endpoint'ов статуса звонков")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


def simple_call_test():
    """Простой тест одного звонка"""
    BASE_URL = "https://cloudpbx.beeline.ru/apis/portal"
    API_TOKEN = "f0744ced-44e3-4d88-9ec7-f7823d83d634"

    pbx = BeelineCloudPBX(BASE_URL, API_TOKEN)

    pattern = "SIP0343PU049QK@ip.beeline.ru"
    phone_number = "+79952116323"

    print("🚀 ПРОСТОЙ ТЕСТ ЗВОНКА")
    print("=" * 50)

    # Включаем запись
    pbx.enable_recording(pattern)

    # Совершаем вызов
    result = pbx.make_call(pattern, phone_number)

    if result:
        print("\n✅ Звонок инициирован через API!")
        print("💡 Если звонок не поступает, вероятные причины:")
        print("   - SIP устройство с добавочным 200 не зарегистрировано")
        print("   - Проблемы с сетью или настройками устройства")
        print("   - Ограничения тарифного плана")
    else:
        print("\n❌ Не удалось инициировать звонок")


if __name__ == "__main__":
    # Выберите один из вариантов:

    # Полная диагностика
    main()

    # Или простой тест
    # simple_call_test()