# CRM API на FastAPI
Это бэкенд для гибкой, мульти-тенантной CRM-системы, построенной на FastAPI. Ключевыми особенностями являются динамический конструктор таблиц, система ролей и разрешений, а также широкие возможности по кастомизации.
Адрес API: http://89.111.169.47:8005 <br>
Интерактивная документация: http://89.111.169.47:8005/docs <br>
Админ-панель: http://89.111.169.47:8005/admin
🚀 Ключевые возможности
Мульти-тенантность: Полная изоляция данных для разных клиентов (компаний).
Конструктор таблиц: Пользователи могут создавать собственные таблицы с типизированными колонками (string, integer, float, date, time, boolean, select, email, phone, url).
Гибкая система прав (RBAC): Управление доступом через роли и разрешения, включая доступ к "чужим" таблицам.
Кастомизация: Возможность переименовывать таблицы и колонки (псевдонимы).
Пользовательская сортировка: Сохранение уникального порядка строк и колонок для каждого пользователя.
Фоновые задачи: Использование Celery и Redis для выполнения длительных операций (например, SMS-рассылок) без блокировки API.
Продвинутая фильтрация: Поддержка множества операторов (eq, gt, contains, blank, is_within для дат и т.д.).
🛠️ Установка и запуск
1. Локальная разработка
Для запуска проекта локально на Windows, Linux или MacOS.
1.1. Клонирование репозитория:
code
Bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd <ПАПКА_ПРОЕКТА>
1.2. Создание и активация виртуального окружения:
code
Bash
# Создание
python -m venv venv

# Активация (Windows)
venv\Scripts\activate.bat

# Активация (Linux/MacOS)
source venv/bin/activate
1.3. Установка зависимостей:
code
Bash
pip install -r requirements.txt
1.4. Настройка .env файла:
Скопируйте .env.example в .env и заполните необходимые переменные (DATABASE_URL, SECRET_KEY и т.д.).
1.5. Запуск необходимых сервисов:
Redis (для Celery):
code
Bash
docker run -d -p 6379:6379 redis
PostgreSQL (если используется):
code
Bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=your_password --name my-postgres postgres
1.6. Запуск приложения:
Веб-сервер FastAPI (в одном терминале):
code
Bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Воркер Celery (во втором терминале):
code
Bash
celery -A celery_worker.celery_app worker --loglevel=info
2. Развертывание на сервере (Ubuntu)
2.1. Получение кода:
code
Bash
cd /root/projects/crm-backend/crm-backend-py 
git pull origin main
2.2. Управление сервисом (systemd):
code
Bash
# Запустить сервис
sudo systemctl start crm_api.service

# Остановить сервис
sudo systemctl stop crm_api.service

# Перезапустить после изменений в коде
sudo systemctl restart crm_api.service

# Посмотреть статус
sudo systemctl status crm_api.service

# Смотреть логи в реальном времени
tail -f /var/log/crm_api.log      # Логи доступа
tail -f /var/log/crm_api_error.log # Логи ошибок
Datenbank (PostgreSQL)
Подключение к базе
code
Bash
# Подключиться от имени пользователя crm_user к базе crm_db
sudo -u postgres psql -d crm_db -U crm_user
Система запросит пароль для crm_user.
Основные команды psql
Команда	Описание
\dt	Показать список всех таблиц
\d users	Описать структуру таблицы users
SELECT * FROM tenants;	Показать все записи из таблицы tenants
SELECT id, email FROM users;	Показать конкретные колонки из users
\q	Выйти из psql
📖 Справочник по API
Полная интерактивная документация доступна по адресу /docs вашего API.
Основные группы эндпоинтов
/api/auth - Регистрация и авторизация.
/api/users - Работа с пользователями.
/api/leads, /api/legal-entities, /api/individuals - CRUD для стандартных сущностей.
/api/meta - Конструктор: управление структурой кастомных таблиц.
/api/data - Данные: CRUD-операции с записями в кастомных таблицах.
/api/aliases - Управление псевдонимами.
/api/shares - Управление доступом к "общим" таблицам.
/api/roles - Управление ролями.
/api/permissions - Получение списка всех разрешений.
Пример: Создание новой записи в кастомной таблице contracts
Метод: POST
URL: /api/data/contracts
Тело (JSON):
code
JSON
{
  "company_name": "ООО Ромашка",
  "total_sum": 150000.50,
  "doc_date": "2025-08-15T10:00:00",
  "is_archived": false,
  "status": 11 
}
status - это id опции из связанного выпадающего списка.
Пример: Получение списка с фильтрацией и сортировкой
Задача: Получить активные договоры с суммой больше 100 000, отсортированные по дате (новые вверху).
Метод: GET
URL: /api/data/contracts?sort_by=doc_date&sort_order=desc&filters=[{"field":"is_archived","value":false},{"field":"total_sum","op":"gt","value":100000}]
Примечание: значение параметра filters должно быть закодировано для URL.