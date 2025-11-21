# services/tochka_setup_service.py
from sqlalchemy.orm import Session
from db import models
from services.eav_service import EAVService
from schemas.eav import EntityTypeCreate, AttributeCreate

def setup_tochka_table(db: Session, eav_service: EAVService, current_user: models.User):
    """
    Проверяет наличие таблицы 'tochka_operations'.
    Если таблицы нет, создает ее со всеми необходимыми колонками.
    """
    table_name = "tochka_operations" # <-- Уникальное системное имя

    existing_table = db.query(models.EntityType).filter(
        models.EntityType.name == table_name,
        models.EntityType.tenant_id == current_user.tenant_id
    ).first()

    if existing_table:
        return  # Таблица уже есть, ничего не делаем

    # Создаем таблицу с понятным для пользователя названием
    table_schema = EntityTypeCreate(
        name=table_name,
        display_name="Операции (Точка Банк)" # <-- Уникальное отображаемое имя
    )
    new_table = eav_service.create_entity_type(table_schema, current_user)

    # Определяем те же самые колонки, что и для других банков
    attributes_to_create = [
        {"name": "operation_id", "display_name": "ID операции", "value_type": "string"},
        {"name": "amount", "display_name": "Сумма", "value_type": "currency"},
        {"name": "currency", "display_name": "Валюта", "value_type": "string"},
        {"name": "operation_type", "display_name": "Тип операции", "value_type": "string"},
        {"name": "contractor_name", "display_name": "Контрагент", "value_type": "string"},
        {"name": "purpose", "display_name": "Назначение платежа", "value_type": "text"},
        {"name": "operation_date", "display_name": "Дата операции", "value_type": "date"},
    ]

    for attr_data in attributes_to_create:
        attr_schema = AttributeCreate(**attr_data)
        eav_service.create_attribute_for_type(new_table.id, attr_schema, current_user)

    return