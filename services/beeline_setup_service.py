# services/beeline_setup_service.py
from sqlalchemy.orm import Session
from db import models
from services.eav_service import EAVService
from schemas.eav import EntityTypeCreate, AttributeCreate

def setup_beeline_table(db: Session, eav_service: EAVService, current_user: models.User):
    """
    Проверяет наличие таблицы 'beeline_calls' у пользователя.
    Если таблицы нет, создает ее со всеми необходимыми колонками.
    """
    table_name = "beeline_calls"

    # 1. Проверяем, существует ли уже такая таблица у клиента
    existing_table = db.query(models.EntityType).filter(
        models.EntityType.name == table_name,
        models.EntityType.tenant_id == current_user.tenant_id
    ).first()

    if existing_table:
        return  # Таблица уже есть, ничего не делаем

    # 2. Если таблицы нет, создаем ее
    table_schema = EntityTypeCreate(
        name=table_name,
        display_name="История звонков (Билайн)"
    )
    new_table = eav_service.create_entity_type(table_schema, current_user)

    # 3. Определяем колонки, которые нужно создать
    attributes_to_create = [
        {"name": "call_id", "display_name": "ID звонка", "value_type": "string"},
        {"name": "external_phone", "display_name": "Номер клиента", "value_type": "phone"},
        {"name": "direction", "display_name": "Направление", "value_type": "string"},
        {"name": "call_date", "display_name": "Дата и время звонка", "value_type": "date"}, # Используем date, так как он поддерживает и время
        {"name": "duration_seconds", "display_name": "Длительность (сек)", "value_type": "integer"},
        {"name": "internal_user", "display_name": "Сотрудник", "value_type": "string"},
        {"name": "record_link", "display_name": "Запись разговора", "value_type": "url"},
        {"name": "audio_record", "display_name": "Файл записи", "value_type": "audio"},
    ]

    # 4. Создаем каждую колонку
    for attr_data in attributes_to_create:
        attr_schema = AttributeCreate(**attr_data)
        eav_service.create_attribute_for_type(new_table.id, attr_schema, current_user)

    return