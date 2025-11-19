# services/banking_setup_service.py

from sqlalchemy.orm import Session
from db import models
from services.eav_service import EAVService
from schemas.eav import EntityTypeCreate, AttributeCreate


def setup_banking_table(db: Session, eav_service: EAVService, current_user: models.User):
    """
    Проверяет наличие таблицы 'banking_operations' у пользователя.
    Если таблицы нет, создает ее со всеми необходимыми колонками.
    """
    table_name = "banking_operations"

    # Проверяем, существует ли уже такая таблица у клиента
    existing_table = db.query(models.EntityType).filter(
        models.EntityType.name == table_name,
        models.EntityType.tenant_id == current_user.tenant_id
    ).first()

    if existing_table:
        return  # Таблица уже есть, ничего не делаем

    # Если таблицы нет, создаем ее
    table_schema = EntityTypeCreate(
        name=table_name,
        display_name="Банковские операции"
    )
    new_table = eav_service.create_entity_type(table_schema, current_user)

    # Определяем колонки, которые нужно создать
    attributes_to_create = [
        {"name": "operation_id", "display_name": "ID операции", "value_type": "string"},
        {"name": "amount", "display_name": "Сумма", "value_type": "currency"},
        {"name": "currency", "display_name": "Валюта", "value_type": "string"},
        {"name": "operation_type", "display_name": "Тип операции", "value_type": "string"},
        {"name": "contractor_name", "display_name": "Контрагент", "value_type": "string"},
        {"name": "purpose", "display_name": "Назначение платежа", "value_type": "text"},
        # Используем text для длинных назначений
        {"name": "operation_date", "display_name": "Дата операции", "value_type": "date"},
    ]

    # Создаем каждую колонку
    for attr_data in attributes_to_create:
        attr_schema = AttributeCreate(**attr_data)
        eav_service.create_attribute_for_type(new_table.id, attr_schema, current_user)

    return