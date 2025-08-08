# services/eav_service.py
from datetime import datetime
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import aliased
from db import models, session
from schemas.eav import EntityTypeCreate, AttributeCreate
from schemas.eav import EntityTypeCreate, AttributeCreate, EntityType
from .alias_service import AliasService


# Маппинг строкового типа на имя поля в модели AttributeValue
VALUE_FIELD_MAP = {
    "string": "value_string",
    "integer": "value_integer",
    "float": "value_float",
    "date": "value_date",
    "boolean": "value_boolean",
}


class EAVService:
    def __init__(self, db: Session = Depends(session.get_db), alias_service: AliasService = Depends()):
        self.db = db
        self.alias_service = alias_service

    # --- МЕТОДЫ ДЛЯ МЕТАДАННЫХ ---
    # >>> ДОБАВЬТЕ ЭТИ ДВА МЕТОДА <<<
    #
    def get_all_entities_for_type(
            self,
            entity_type_name: str,
            current_user: models.User,
            filters: List[Dict[str, Any]] = None,
            sort_by: str = 'created_at',
            sort_order: str = 'desc'
    ) -> List[Dict[str, Any]]:

        # 1. Получаем тип сущности и его атрибуты
        entity_type = self.db.query(models.EntityType).options(
            joinedload(models.EntityType.attributes)
        ).filter(
            models.EntityType.name == entity_type_name,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()

        if not entity_type:
            raise HTTPException(status_code=404, detail=f"Тип сущности '{entity_type_name}' не найден")

        attributes_map = {attr.name: attr for attr in entity_type.attributes}

        # 2. Начинаем строить запрос
        query = self.db.query(models.Entity).filter(models.Entity.entity_type_id == entity_type.id)

        # 3. Динамически применяем фильтры
        if filters:
            for f in filters:
                field_name = f.get("field")
                op = f.get("op", "eq")  # eq (равно) по умолчанию
                value = f.get("value")

                if not field_name or field_name not in attributes_map:
                    continue

                attribute = attributes_map[field_name]
                value_column = getattr(models.AttributeValue, VALUE_FIELD_MAP[attribute.value_type])

                # Создаем подзапрос для проверки существования нужного значения
                subquery = self.db.query(models.AttributeValue.id).filter(
                    models.AttributeValue.entity_id == models.Entity.id,
                    models.AttributeValue.attribute_id == attribute.id
                )

                # Применяем оператор сравнения
                if op == "eq":
                    subquery = subquery.filter(value_column == value)
                elif op == "neq":
                    subquery = subquery.filter(value_column != value)
                elif op == "gt":
                    subquery = subquery.filter(value_column > value)
                elif op == "gte":
                    subquery = subquery.filter(value_column >= value)
                elif op == "lt":
                    subquery = subquery.filter(value_column < value)
                elif op == "lte":
                    subquery = subquery.filter(value_column <= value)
                elif op == "contains" and attribute.value_type == 'string':
                    subquery = subquery.filter(value_column.ilike(f"%{value}%"))
                else:
                    continue  # Пропускаем неподдерживаемые операторы

                # Фильтруем основные сущности: должны существовать значения, удовлетворяющие подзапросу
                query = query.filter(subquery.exists())

        # 4. Применяем сортировку
        if sort_by == 'created_at':
            order_expression = desc(models.Entity.created_at) if sort_order == 'desc' else asc(models.Entity.created_at)
            query = query.order_by(order_expression)
        elif sort_by in attributes_map:
            sort_attribute = attributes_map[sort_by]
            sort_value_column_name = VALUE_FIELD_MAP[sort_attribute.value_type]

            # Используем aliased для LEFT JOIN, чтобы не конфликтовать с фильтрами
            SortValue = aliased(models.AttributeValue)

            query = query.outerjoin(
                SortValue,
                and_(
                    SortValue.entity_id == models.Entity.id,
                    SortValue.attribute_id == sort_attribute.id
                )
            )

            sort_value_column = getattr(SortValue, sort_value_column_name)
            order_expression = desc(sort_value_column).nullslast() if sort_order == 'desc' else asc(
                sort_value_column).nullsfirst()
            query = query.order_by(order_expression)

        # 5. Выполняем запрос и получаем ID сущностей
        # (Пагинацию применяем к ID, чтобы избежать проблем с JOIN)
        entity_ids = [e.id for e in query.all()]

        # 6. Загружаем полные данные только для отфильтрованных и отсортированных сущностей
        if not entity_ids:
            return []

        final_query = self.db.query(models.Entity).filter(
            models.Entity.id.in_(entity_ids)
        ).options(
            joinedload(models.Entity.values).joinedload(models.AttributeValue.attribute)
        )

        # Повторно применяем ту же сортировку
        # (Это нужно, т.к. `IN` не гарантирует порядок)
        if sort_by == 'created_at':
            order_expression = desc(models.Entity.created_at) if sort_order == 'desc' else asc(models.Entity.created_at)
            final_query = final_query.order_by(order_expression)
        elif sort_by in attributes_map:
            # ... (логика сортировки, как выше) ...
            sort_attribute = attributes_map[sort_by]
            sort_value_column_name = VALUE_FIELD_MAP[sort_attribute.value_type]
            SortValue = aliased(models.AttributeValue)
            final_query = final_query.outerjoin(
                SortValue, and_(SortValue.entity_id == models.Entity.id, SortValue.attribute_id == sort_attribute.id))
            sort_value_column = getattr(SortValue, sort_value_column_name)
            order_expression = desc(sort_value_column).nullslast() if sort_order == 'desc' else asc(
                sort_value_column).nullsfirst()
            final_query = final_query.order_by(order_expression)

        entities = final_query.all()
        return [self._pivot_data(e) for e in entities]

    def get_entity_type_by_id(self, entity_type_id: int, current_user: models.User) -> EntityType:
        """
        Получить один тип сущности по его ID, с примененными псевдонимами.
        """
        # ШАГ 1: Получаем "чистый" объект из БД
        db_entity_type = self.db.query(models.EntityType).options(
            joinedload(models.EntityType.attributes)  # Загружаем атрибуты сразу
        ).filter(
            models.EntityType.id == entity_type_id,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()

        if not db_entity_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тип сущности не найден"
            )

        # ШАГ 2: Загружаем все псевдонимы для данного пользователя
        # Наш сервис теперь имеет доступ к другому сервису!
        attr_aliases = self.alias_service.get_aliases_for_tenant(current_user=current_user)
        table_aliases = self.alias_service.get_table_aliases_for_tenant(current_user=current_user)

        # ШАГ 3: Создаем Pydantic-схему из объекта SQLAlchemy
        # Это безопасный способ, который не меняет объект сессии БД
        response_entity_type = EntityType.model_validate(db_entity_type)

        # ШАГ 4: "Патчим" данные псевдонимами
        # Сначала для самой таблицы
        table_name = response_entity_type.name
        if table_name in table_aliases:
            response_entity_type.display_name = table_aliases[table_name]

        # Теперь для каждого атрибута (колонки)
        table_attr_aliases = attr_aliases.get(table_name, {})
        for attribute in response_entity_type.attributes:
            if attribute.name in table_attr_aliases:
                attribute.display_name = table_attr_aliases[attribute.name]

        return response_entity_type



    def delete_entity_type(self, entity_type_id: int, current_user: models.User):
        """
        Удалить тип сущности и ВСЕ связанные с ним данные (атрибуты, сущности, значения).
        Это необратимая операция!
        """
        # 1. Находим таблицу, которую нужно удалить.
        # Этот метод уже содержит проверку на tenant_id, что гарантирует безопасность.
        entity_type_to_delete = self.get_entity_type_by_id(
            entity_type_id=entity_type_id,
            current_user=current_user
        )

        # 2. Удаляем объект. Благодаря cascade="all, delete-orphan" в моделях,
        # SQLAlchemy и база данных позаботятся об удалении всех дочерних записей.
        self.db.delete(entity_type_to_delete)
        self.db.commit()

        # Для операции DELETE принято возвращать None или пустой ответ.
        return None

    def delete_attribute_from_type(self, entity_type_id: int, attribute_id: int, current_user: models.User):
        """
        Удалить атрибут ('колонку') из типа сущности и все его значения.
        """
        # 1. Сначала проверяем, что сам тип сущности (таблица) существует
        # и принадлежит текущему пользователю. Это защищает от попытки удалить
        # колонку из чужой таблицы.
        self.get_entity_type_by_id(entity_type_id=entity_type_id, current_user=current_user)

        # 2. Находим сам атрибут, который нужно удалить.
        # Дополнительно проверяем, что он действительно принадлежит указанному типу сущности.
        attribute_to_delete = self.db.query(models.Attribute).filter(
            models.Attribute.id == attribute_id,
            models.Attribute.entity_type_id == entity_type_id
        ).first()

        # 3. Если атрибут не найден, возвращаем ошибку.
        if not attribute_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Атрибут с ID {attribute_id} не найден в типе сущности {entity_type_id}"
            )

        # 4. Проверяем, не является ли атрибут системным. Системные удалять нельзя.
        system_attributes = [
            "send_sms_trigger", "sms_status", "sms_last_error",
            "phone_number", "message_text"
        ]
        if attribute_to_delete.name in system_attributes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нельзя удалить системный атрибут '{attribute_to_delete.name}'"
            )

        # 5. Удаляем объект. Благодаря ondelete="CASCADE", все связанные AttributeValue
        # будут удалены автоматически на уровне базы данных.
        self.db.delete(attribute_to_delete)
        self.db.commit()

        return None


    # ИЗМЕНЕНИЕ: Добавляем current_user в аргументы
    def create_entity_type(self, entity_type_in: EntityTypeCreate, current_user: models.User) -> models.EntityType:
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Проверяем, нет ли у этого клиента уже типа с таким именем
        existing = self.db.query(models.EntityType).filter(
            models.EntityType.name == entity_type_in.name,
            models.EntityType.tenant_id == current_user.tenant_id  # <- Проверяем по паре
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Тип сущности с именем '{entity_type_in.name}' уже существует")

        # ... остальной код метода без изменений ...

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

    def get_all_entity_types(self, current_user: models.User) -> List[EntityType]:
        """
        Получить все типы сущностей ('таблицы') для ТЕКУЩЕГО пользователя,
        с примененными псевдонимами для таблиц И их атрибутов.
        """
        # ШАГ 1: Получаем все "чистые" объекты из БД, но СРАЗУ ЖЕ
        # подгружаем связанные с ними атрибуты (колонки).
        # ВОТ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: options(joinedload(models.EntityType.attributes))
        db_entity_types = self.db.query(models.EntityType).options(
            joinedload(models.EntityType.attributes)
        ).filter(
            models.EntityType.tenant_id == current_user.tenant_id
        ).all()

        # ШАГ 2: Загружаем все псевдонимы ОДНИМ РАЗОМ (это эффективно)
        attr_aliases = self.alias_service.get_aliases_for_tenant(current_user=current_user)
        table_aliases = self.alias_service.get_table_aliases_for_tenant(current_user=current_user)

        # ШАГ 3: Преобразуем и "патчим" каждый объект в списке
        response_list = []
        for db_entity_type in db_entity_types:
            # Создаем Pydantic-схему (используя правильный метод для Pydantic V2)
            response_entity = EntityType.model_validate(db_entity_type)

            # Применяем псевдоним к самой таблице
            if response_entity.name in table_aliases:
                response_entity.display_name = table_aliases[response_entity.name]

            # --- ДОБАВЛЕНА НЕДОСТАЮЩАЯ ЛОГИКА ---
            # Применяем псевдонимы к атрибутам (колонкам) этой таблицы.
            # Теперь response_entity.attributes гарантированно содержит данные.
            table_attr_aliases = attr_aliases.get(response_entity.name, {})
            if table_attr_aliases:  # Проверяем, есть ли вообще псевдонимы для колонок этой таблицы
                for attribute in response_entity.attributes:
                    if attribute.name in table_attr_aliases:
                        attribute.display_name = table_attr_aliases[attribute.name]
            # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

            response_list.append(response_entity)

        return response_list