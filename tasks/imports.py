# tasks/imports.py
import os
import pandas as pd
from celery_worker import celery_app
from db import models
from db.session import SessionLocal
from services.eav_service import EAVService
from schemas.eav import EntityTypeCreate, AttributeCreate


@celery_app.task
def process_file_import_task(file_path: str, user_id: int, tenant_id: int, import_config: dict):
    """
    Фоновая задача, которая выполняет всю тяжелую работу по импорту.
    """
    db = None
    try:
        db = SessionLocal()
        eav_service = EAVService(db=db)

        # "Восстанавливаем" объект пользователя, чтобы передавать его в сервисы
        current_user = db.query(models.User).get(user_id)
        if not current_user:
            # Логируем ошибку, но не прерываем задачу, чтобы удалить файл
            print(f"Критическая ошибка: пользователь с ID {user_id} не найден.")
            return

        # 1. Создаем новую таблицу
        table_schema = EntityTypeCreate(
            name=import_config['new_table_name'],
            display_name=import_config['new_table_display_name']
        )
        new_entity_type = eav_service.create_entity_type(table_schema, current_user)

        # 2. Создаем колонки
        column_mappings = {}
        for col_config in import_config['columns']:
            if col_config['do_import']:
                attr_schema = AttributeCreate(
                    name=col_config['original_header'].lower().replace(' ', '_'),  # Создаем системное имя
                    display_name=col_config['display_name'],
                    value_type=col_config['value_type']
                )
                new_attribute = eav_service.create_attribute_for_type(
                    entity_type_id=new_entity_type.id,
                    attribute_in=attr_schema,
                    current_user=current_user
                )
                column_mappings[col_config['original_header']] = new_attribute.name

        # 3. Читаем весь файл и импортируем данные
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Заменяем заголовки DataFrame на системные имена наших новых колонок
        df.rename(columns=column_mappings, inplace=True)

        for index, row in df.iterrows():
            # Преобразуем строку DataFrame в словарь, пригодный для нашего API
            # Убираем колонки, которые мы решили не импортировать
            entity_data = {
                sys_name: row[sys_name] for orig_header, sys_name in column_mappings.items()
            }
            # Очищаем данные от NaN значений pandas
            entity_data_cleaned = {k: v for k, v in entity_data.items() if pd.notna(v)}

            eav_service.create_entity(
                entity_type_name=new_entity_type.name,
                data=entity_data_cleaned,
                current_user=current_user
            )

        print(f"Импорт для таблицы '{new_entity_type.display_name}' успешно завершен.")

    except Exception as e:
        print(f"ОШИБКА в фоновой задаче импорта: {str(e)}")
        # Здесь можно добавить логику для уведомления пользователя об ошибке
        raise e
    finally:
        if db:
            db.close()
        # 4. Удаляем временный файл в любом случае
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Временный файл {file_path} удален.")