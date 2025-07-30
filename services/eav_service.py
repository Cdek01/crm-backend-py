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
    # >>> ДОБАВЬТЕ ЭТИ ДВА МЕТОДА <<<
    #
    def get_all_entity_types(self, current_user: models.User) -> List[models.EntityType]:
        """
        Получить все типы сущностей ('таблицы'), созданные текущим клиентом.
        """
        # Важнейшее условие для multi-tenancy!
        # Показываем только те типы, которые принадлежат клиенту (tenant) текущего пользователя.
        return self.db.query(models.EntityType).filter(
            models.EntityType.tenant_id == current_user.tenant_id
        ).order_by(models.EntityType.display_name).all()

    def get_entity_type_by_id(self, entity_type_id: int, current_user: models.User) -> models.EntityType:
        """
        Получить один тип сущности по его ID.
        """
        # Ищем по ID, но СТРОГО в рамках текущего tenant_id.
        # Это не позволяет одному клиенту "подсмотреть" структуру таблиц другого.
        entity_type = self.db.query(models.EntityType).filter(
            models.EntityType.id == entity_type_id,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()

        if not entity_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тип сущности не найден"
            )
        return entity_type

    # ИЗМЕНЕНИЕ: Добавляем current_user в аргументы
    def create_entity_type(self, entity_type_in: EntityTypeCreate, current_user: models.User) -> models.EntityType:
        # Проверяем, нет ли у этого клиента уже типа с таким именем
        existing = self.db.query(models.EntityType).filter(
            models.EntityType.name == entity_type_in.name,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Тип сущности с именем '{entity_type_in.name}' уже существует")

        # --- ИЗМЕНЕНИЕ ЛОГИКИ ---

        # 1. Создаем и коммитим ТОЛЬКО сам EntityType
        db_entity_type = models.EntityType(
            **entity_type_in.model_dump(),
            tenant_id=current_user.tenant_id
        )
        self.db.add(db_entity_type)
        self.db.commit()
        self.db.refresh(db_entity_type)

        # 2. Теперь, когда EntityType сохранен, создаем для него атрибуты
        system_attributes = [
            {"name": "send_sms_trigger", "display_name": "Отправить SMS", "value_type": "boolean"},
            {"name": "sms_status", "display_name": "Статус отправки", "value_type": "string"},
            {"name": "sms_last_error", "display_name": "Ошибка отправки", "value_type": "string"},
            {"name": "phone_number", "display_name": "Номер телефона", "value_type": "string"},
            {"name": "message_text", "display_name": "Текст сообщения", "value_type": "string"},
        ]

        for attr_data in system_attributes:
            # Проверяем, нет ли уже такого атрибута (на всякий случай)
            attr_exists = self.db.query(models.Attribute).filter_by(
                name=attr_data['name'],
                entity_type_id=db_entity_type.id
            ).first()
            if not attr_exists:
                attr = models.Attribute(**attr_data, entity_type_id=db_entity_type.id)
                self.db.add(attr)

        # 3. Коммитим добавление атрибутов
        self.db.commit()
        # Обновляем объект, чтобы он содержал новые атрибуты
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
        # --- ИМПОРТ ЗАДАЧИ ВНУТРИ МЕТОДА ---
        from tasks.messaging import send_sms_for_entity_task

        # Загружаем сущность со связанным типом и его атрибутами
        entity = self.db.query(models.Entity).options(
            joinedload(models.Entity.entity_type).joinedload(models.EntityType.attributes)
        ).get(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        # --- НОВАЯ ЛОГИКА ОБНОВЛЕНИЯ (PATCH) ---

        attributes_map = {attr.name: attr for attr in entity.entity_type.attributes}

        # 1. Проверяем триггер и модифицируем входящие данные
        if data.get("send_sms_trigger") is True:
            data["sms_status"] = "pending"
            data["send_sms_trigger"] = False
            # Запускаем фоновую задачу
            send_sms_for_entity_task.delay(entity_id=entity_id)

        # 2. Обновляем значения атрибутов
        for key, value in data.items():
            if key not in attributes_map:
                continue

            attribute = attributes_map[key]
            value_field_name = VALUE_FIELD_MAP[attribute.value_type]

            # Ищем существующее значение для этого атрибута
            existing_value = self.db.query(models.AttributeValue).filter_by(
                entity_id=entity_id,
                attribute_id=attribute.id
            ).first()

            if existing_value:
                # Если значение уже есть, обновляем его
                setattr(existing_value, value_field_name, value)
            else:
                # Если значения нет, создаем новое
                new_value = models.AttributeValue(
                    entity_id=entity_id,
                    attribute_id=attribute.id
                )
                setattr(new_value, value_field_name, value)
                self.db.add(new_value)

        # 3. Обновляем `updated_at` у самой сущности
        entity.updated_at = datetime.utcnow()
        self.db.add(entity)

        self.db.commit()

        # 4. Возвращаем ПОЛНЫЙ и ОБНОВЛЕННЫЙ объект
        return self.get_entity_by_id(entity_id)

    def delete_entity(self, entity_id: int):
        entity = self.db.query(models.Entity).get(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        self.db.delete(entity)
        self.db.commit()
        return None