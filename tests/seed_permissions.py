import os
import sys
from sqlalchemy.orm import Session

# --- Магия для добавления корневой папки проекта в sys.path ---
# Это нужно, чтобы скрипт мог импортировать модули вашего проекта (db, core и т.д.)
# независимо от того, откуда он запущен.
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# -------------------------------------------------------------

from db.session import SessionLocal
from db.models import Permission

# Определяем все разрешения, которые должны быть в системе
ALL_PERMISSIONS = {
    'roles:manage': 'Управление ролями и правами доступа пользователей',
    'leads:view': 'Просмотр списка лидов',
    'leads:create': 'Создание новых лидов',
    'leads:edit': 'Редактирование лидов',
    'leads:delete': 'Удаление лидов',
    'legal_entities:view': 'Просмотр списка юридических лиц',
    'legal_entities:create': 'Создание новых юридических лиц',
    'legal_entities:edit': 'Редактирование юридических лиц',
    'legal_entities:delete': 'Удаление юридических лиц',
    'individuals:view': 'Просмотр списка физических лиц',
    'individuals:create': 'Создание новых физических лиц',
    'individuals:edit': 'Редактирование физических лиц',
    'individuals:delete': 'Удаление физических лиц',
    'meta:view': 'Просмотр структуры кастомных таблиц',
    'meta:manage': 'Создание и удаление кастомных таблиц и колонок',
    'aliases:manage': 'Управление псевдонимами таблиц и колонок',
}

def seed_permissions(db: Session):
    """
    Наполняет базу данных разрешениями из списка ALL_PERMISSIONS.
    Добавляет только те, которых еще нет.
    """
    print("Начинаю проверку и добавление разрешений...")

    # 1. Получаем все имена разрешений, которые уже есть в базе
    existing_permissions = db.query(Permission.name).all()
    # Преобразуем список кортежей в простое множество для быстрой проверки
    existing_permission_names = {name for (name,) in existing_permissions}
    print(f"Найдено существующих разрешений: {len(existing_permission_names)}")

    # 2. Проходимся по нашему списку и добавляем недостающие
    permissions_to_add = []
    for name, description in ALL_PERMISSIONS.items():
        if name not in existing_permission_names:
            permissions_to_add.append(
                Permission(name=name, description=description)
            )
            print(f" -> Готовлю к добавлению: '{name}'")

    # 3. Если есть что добавить, добавляем все одним запросом и коммитим
    if permissions_to_add:
        db.add_all(permissions_to_add)
        db.commit()
        print(f"\nУспешно добавлено {len(permissions_to_add)} новых разрешений.")
    else:
        print("\nВсе необходимые разрешения уже существуют в базе данных. Ничего не добавлено.")

if __name__ == "__main__":
    # Получаем сессию базы данных так же, как это делает FastAPI
    db = SessionLocal()
    try:
        seed_permissions(db)
    finally:
        # Обязательно закрываем сессию
        db.close()