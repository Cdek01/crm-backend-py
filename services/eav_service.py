# services/eav_service.py
from datetime import datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any

from db import models, session
from schemas.eav import EntityTypeCreate, AttributeCreate

# Маппинг строкового типа на имя поля в модели AttributeValue
VALUE_FIELD_MAP = {
    "string": "value_string",
    "integer": "value_integer",
    "float": "value_float",
    "date": "value_date",
    "boolean": "value_boolean",
}


class EAVService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    # --- МЕТОДЫ ДЛЯ МЕТАДАННЫХ ---

    def create_entity_type(self, entity_type_in: EntityTypeCreate) -> models.EntityType:
        existing = self.db.query(models.EntityType).filter(models.EntityType.name == entity_type_in.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Тип сущности с именем '{entity_type_in.name}' уже существует")

        db_entity_type = models.EntityType(**entity_type_in.model_dump())
        self.db.add(db_entity_type)
        self.db.commit()
        self.db.refresh(db_entity_type)
        return db_entity_type

    def create_attribute_for_type(self, entity_type_id: int, attribute_in: AttributeCreate) -> models.Attribute:
        entity_type = self.db.query(models.EntityType).get(entity_type_id)
        if not entity_type:
            raise HTTPException(status_code=404, detail="Тип сущности не найден")

        existing_attr = self.db.query(models.Attribute).filter(
            models.Attribute.entity_type_id == entity_type_id,
            models.Attribute.name == attribute_in.name
        ).first()
        if existing_attr:
            raise HTTPException(status_code=400,
                                detail=f"Атрибут с именем '{attribute_in.name}' уже существует для этого типа")

        db_attribute = models.Attribute(**attribute_in.model_dump(), entity_type_id=entity_type_id)
        self.db.add(db_attribute)
        self.db.commit()
        self.db.refresh(db_attribute)
        return db_attribute

    # --- МЕТОДЫ ДЛЯ ДАННЫХ ---

    def _get_entity_type_with_attributes(self, entity_type_name: str) -> models.EntityType:
        entity_type = self.db.query(models.EntityType).options(
            joinedload(models.EntityType.attributes)
        ).filter(models.EntityType.name == entity_type_name).first()

        if not entity_type:
            raise HTTPException(status_code=404, detail=f"Тип сущности '{entity_type_name}' не найден")
        return entity_type

    def _pivot_data(self, entity: models.Entity) -> Dict[str, Any]:
        """Преобразует EAV-записи в один JSON-объект."""
        result = {"id": entity.id, "created_at": entity.created_at, "updated_at": entity.updated_at}
        for value_obj in entity.values:
            attr_name = value_obj.attribute.name
            value_type = value_obj.attribute.value_type
            db_field = VALUE_FIELD_MAP[value_type]
            result[attr_name] = getattr(value_obj, db_field)
        return result

    def get_all_entities_for_type(self, entity_type_name: str) -> List[Dict[str, Any]]:
        entity_type = self._get_entity_type_with_attributes(entity_type_name)

        entities = self.db.query(models.Entity).filter(
            models.Entity.entity_type_id == entity_type.id
        ).options(
            joinedload(models.Entity.values).joinedload(models.AttributeValue.attribute)
        ).all()

        return [self._pivot_data(e) for e in entities]

    def get_entity_by_id(self, entity_id: int) -> Dict[str, Any]:
        entity = self.db.query(models.Entity).options(
            joinedload(models.Entity.values).joinedload(models.AttributeValue.attribute)
        ).get(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        return self._pivot_data(entity)

    def create_entity(self, entity_type_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        entity_type = self._get_entity_type_with_attributes(entity_type_name)
        attributes_map = {attr.name: attr for attr in entity_type.attributes}

        # 1. Создаем саму сущность (строку)
        new_entity = models.Entity(entity_type_id=entity_type.id)
        self.db.add(new_entity)
        self.db.flush()  # Получаем ID до коммита

        # 2. Создаем значения атрибутов
        for key, value in data.items():
            if key not in attributes_map or value is None:
                continue

            attribute = attributes_map[key]
            value_field_name = VALUE_FIELD_MAP[attribute.value_type]

            attr_value = models.AttributeValue(
                entity_id=new_entity.id,
                attribute_id=attribute.id,
            )
            setattr(attr_value, value_field_name, value)
            self.db.add(attr_value)

        self.db.commit()
        self.db.refresh(new_entity)
        return self.get_entity_by_id(new_entity.id)

    def update_entity(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        # ИСПРАВЛЕНИЕ: Загружаем сущность вместе со связанным объектом EntityType
        entity = self.db.query(models.Entity).options(
            joinedload(models.Entity.entity_type).joinedload(models.EntityType.attributes)
        ).get(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        # Удаляем старые значения и записываем новые (простой вариант для PUT)
        # synchronize_session=False часто помогает избежать конфликтов при массовом удалении
        self.db.query(models.AttributeValue).filter(
            models.AttributeValue.entity_id == entity_id
        ).delete(synchronize_session=False)

        # Теперь `entity.entity_type` гарантированно загружен и не будет None
        attributes_map = {attr.name: attr for attr in entity.entity_type.attributes}

        for key, value in data.items():
            if key not in attributes_map or value is None:
                continue

            attribute = attributes_map[key]
            value_field_name = VALUE_FIELD_MAP[attribute.value_type]
            attr_value = models.AttributeValue(entity_id=entity.id, attribute_id=attribute.id)
            setattr(attr_value, value_field_name, value)
            self.db.add(attr_value)

        # ИСПРАВЛЕНИЕ: Обновляем поле updated_at у самой сущности
        entity.updated_at = datetime.utcnow()
        self.db.add(entity)

        self.db.commit()
        return self.get_entity_by_id(entity_id)

    def delete_entity(self, entity_id: int):
        entity = self.db.query(models.Entity).get(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        self.db.delete(entity)
        self.db.commit()
        return None