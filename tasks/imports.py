import os
import pandas as pd
from celery_worker import celery_app
from db.session import SessionLocal
from services.eav_service import EAVService
from services.alias_service import AliasService  # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ
from db import models  # <-- УБЕДИТЕСЬ, ЧТО ЭТОТ ИМПОРТ ЕСТЬ
from schemas.eav import EntityTypeCreate, AttributeCreate


@celery_app.task
def process_file_import_task(file_path: str, user_id: int, tenant_id: int, import_config: dict):
    """
    Фоновая задача, которая выполняет всю тяжелую работу по импорту.
    """
    db = None
    try:
        db = SessionLocal()

        # --- НАЧАЛО ИСПРАВЛЕНИЯ: Ручное внедрение зависимостей ---
        # 1. Создаем зависимость (AliasService)
        alias_service = AliasService(db=db)
        # 2. Создаем основной сервис, передавая ему зависимость
        eav_service = EAVService(db=db, alias_service=alias_service)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        current_user = db.query(models.User).get(user_id)
        if not current_user:
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
                    name=col_config['original_header'].lower().replace(' ', '_').replace('"', ''),
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
                # Убираем dtype=str и добавляем parse_dates для колонок, которые пользователь отметил как 'date'
        date_columns = [
            col['original_header'] for col in import_config['columns']
            if col['do_import'] and col['value_type'] == 'date'
        ]

        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, parse_dates=date_columns)
        else:
            df = pd.read_excel(file_path, parse_dates=date_columns)
        df.rename(columns=column_mappings, inplace=True)

        # Заменяем NaN на None во всем DataFrame перед итерацией
        df_cleaned = df.where(pd.notna(df), None)

        for index, row in df_cleaned.iterrows():
            entity_data = {
                sys_name: row[sys_name] for orig_header, sys_name in column_mappings.items()
            }
            # Дополнительная очистка, если после замены остались None
            entity_data_cleaned = {k: v for k, v in entity_data.items() if v is not None}

            # Пропускаем создание пустых строк
            if not entity_data_cleaned:
                continue

            eav_service.create_entity(
                entity_type_name=new_entity_type.name,
                data=entity_data_cleaned,
                current_user=current_user
            )

        print(f"Импорт для таблицы '{new_entity_type.display_name}' успешно завершен.")

    except Exception as e:
        print(f"ОШИБКА в фоновой задаче импорта: {str(e)}")
        # Логируем полный traceback для отладки
        import traceback
        traceback.print_exc()
        raise e
    finally:
        if db:
            db.close()
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Временный файл {file_path} удален.")