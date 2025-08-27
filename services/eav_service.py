#services/eav_service.py

from datetime import datetime
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, asc, desc, func
from sqlalchemy.orm import aliased
from db import models, session
from schemas.eav import EntityType, EntityTypeCreate, Attribute, AttributeCreate, EntityTypeUpdate
from .alias_service import AliasService
from sqlalchemy import or_
from datetime import datetime, time


VALUE_FIELD_MAP = {
    "string": "value_string",
    "integer": "value_integer",
    "float": "value_float",
    "date": "value_date",
    "boolean": "value_boolean",
    "time": "value_time",
}


class EAVService:
    def __init__(self, db: Session = Depends(session.get_db), alias_service: AliasService = Depends()):
        self.db = db
        self.alias_service = alias_service

    # --- Внутренний метод для безопасного получения типа сущности по имени ---



    # def get_all_entity_types(self, current_user: models.User) -> List[EntityType]:
    #     """
    #     Получить список всех кастомных таблиц, доступных пользователю:
    #     - Его собственные таблицы.
    #     - Чужие таблицы, на которые у него есть права.
    #     """
    #     db_user = self.db.query(models.User).options(
    #         joinedload(models.User.roles).joinedload(models.Role.permissions)
    #     ).filter(models.User.id == current_user.id).one()
    #     user_permissions = {perm.name for role in db_user.roles for perm in role.permissions}
    #
    #     accessible_table_names = {p.split(':')[2] for p in user_permissions if p.startswith("data:") and len(p.split(':')) == 3}
    #
    #     query = self.db.query(models.EntityType).options(
    #         joinedload(models.EntityType.attributes)
    #     ).order_by(models.EntityType.id)
    #
    #     if not current_user.is_superuser:
    #         query = query.filter(
    #             or_(
    #                 models.EntityType.tenant_id == current_user.tenant_id,
    #                 models.EntityType.name.in_(accessible_table_names)
    #             )
    #         )
    #
    #     db_entity_types = query.all()
    #
    #     attr_aliases = self.alias_service.get_aliases_for_tenant(current_user=current_user)
    #     table_aliases = self.alias_service.get_table_aliases_for_tenant(current_user=current_user)
    #
    #     response_list = []
    #     for db_entity_type in db_entity_types:
    #         response_entity = EntityType.model_validate(db_entity_type)
    #         if response_entity.name in table_aliases:
    #             response_entity.display_name = table_aliases[response_entity.name]
    #
    #         table_attr_aliases = attr_aliases.get(response_entity.name, {})
    #         if table_attr_aliases:
    #             for attribute in response_entity.attributes:
    #                 if attribute.name in table_attr_aliases:
    #                     attribute.display_name = table_attr_aliases[attribute.name]
    #         response_list.append(response_entity)
    #     return response_list
    # 👉 вставь этот метод в класс
    def _apply_attribute_order(
        self,
        db: Session,
        entity_type_id: int,
        attributes: List[models.Attribute],
        current_user: models.User
    ) -> List[models.Attribute]:
        """Применяет сохранённый пользователем порядок к списку атрибутов"""
        saved_order_ids = [
            item_id for (item_id,) in db.query(models.AttributeOrder.attribute_id)
            .filter(
                models.AttributeOrder.user_id == current_user.id,
                models.AttributeOrder.entity_type_id == entity_type_id
            )
            .order_by(models.AttributeOrder.position)
        ]

        if not saved_order_ids:
            return sorted(attributes, key=lambda a: a.id)

        attr_map = {a.id: a for a in attributes}
        sorted_attrs = [attr_map[i] for i in saved_order_ids if i in attr_map]
        sorted_attrs.extend(
            sorted([a for a in attributes if a.id not in saved_order_ids], key=lambda a: a.id)
        )
        return sorted_attrs
    def get_all_entity_types(self, current_user: models.User) -> List[EntityType]:
        """
        Получить список всех кастомных таблиц, доступных пользователю:
        - Его собственные таблицы.
        - Чужие таблицы, на которые у него есть права.
        """
        db_user = self.db.query(models.User).options(
            joinedload(models.User.roles).joinedload(models.Role.permissions)
        ).filter(models.User.id == current_user.id).one()
        user_permissions = {perm.name for role in db_user.roles for perm in role.permissions}

        accessible_table_names = {p.split(':')[2] for p in user_permissions if
                                  p.startswith("data:") and len(p.split(':')) == 3}

        query = self.db.query(models.EntityType).options(
            joinedload(models.EntityType.attributes)
        ).order_by(models.EntityType.id)

        if not current_user.is_superuser:
            query = query.filter(
                or_(
                    models.EntityType.tenant_id == current_user.tenant_id,
                    models.EntityType.name.in_(accessible_table_names)
                )
            )

        db_entity_types = query.all()

        attr_aliases = self.alias_service.get_aliases_for_tenant(current_user=current_user)
        table_aliases = self.alias_service.get_table_aliases_for_tenant(current_user=current_user)

        response_list = []
        for db_entity_type in db_entity_types:
            # применяем порядок
            sorted_attrs = self._apply_attribute_order(self.db, db_entity_type.id, db_entity_type.attributes,
                                                       current_user)

            response_entity = EntityType.model_validate(db_entity_type)
            response_entity.attributes = sorted_attrs

            # применяем алиасы
            if response_entity.name in table_aliases:
                response_entity.display_name = table_aliases[response_entity.name]

            table_attr_aliases = attr_aliases.get(response_entity.name, {})
            for attribute in response_entity.attributes:
                if attribute.name in table_attr_aliases:
                    attribute.display_name = table_attr_aliases[attribute.name]

            response_list.append(response_entity)

        return response_list







    def _get_entity_type_by_name(
            self,
            entity_type_name: str,
            current_user: models.User,
            tenant_id: Optional[int] = None  # tenant_id теперь используется только суперадмином
    ) -> models.EntityType:
        """
        Ищет таблицу по имени с учетом прав доступа.
        """
        # 1. Получаем права пользователя
        user_permissions = {perm.name for role in current_user.roles for perm in role.permissions}

        # 2. Строим базовый запрос
        query = self.db.query(models.EntityType).filter(models.EntityType.name == entity_type_name)

        if not current_user.is_superuser:
            # 3. Проверяем, есть ли у пользователя право на эту таблицу
            has_access_via_permission = any(
                p.startswith(f"data:") and p.endswith(f":{entity_type_name}") for p in user_permissions)

            # 4. Пользователь может найти таблицу, если:
            #    - она принадлежит его тенанту
            #    - ИЛИ у него есть явное право на доступ к ней
            query = query.filter(
                or_(
                    models.EntityType.tenant_id == current_user.tenant_id,
                    has_access_via_permission  # Если True, это условие не будет фильтровать по tenant_id
                )
            )
            # ВАЖНО: Этот фильтр не совсем корректен, так как `has_access_via_permission` - это Python boolean.
            # Правильная реализация ниже.

        # --- ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ ---
        if not current_user.is_superuser:
            query = query.filter(
                or_(
                    models.EntityType.tenant_id == current_user.tenant_id,
                    models.EntityType.name.in_(
                        # Получаем имена всех таблиц, к которым есть хоть какой-то доступ
                        {p.split(':')[2] for p in user_permissions if p.startswith("data:") and len(p.split(':')) == 3}
                    )
                )
            )
        elif tenant_id:
            query = query.filter(models.EntityType.tenant_id == tenant_id)

        result = query.first()

        if not result:
            raise HTTPException(status_code=404,
                                detail=f"Тип сущности '{entity_type_name}' не найден или к нему нет доступа")

        return self.db.query(models.EntityType).options(joinedload(models.EntityType.attributes)).get(result.id)

    def get_entity_type_by_id(self, entity_type_id: int, current_user: models.User) -> EntityType:
        """
        Получает один тип сущности по ID и возвращает его атрибуты
        в сохраненном для пользователя порядке.
        """
        # 1. Открываем новую, чистую сессию, чтобы избежать кэширования
        db = session.SessionLocal()
        try:
            # 2. Находим основной объект EntityType с проверкой прав
            query = db.query(models.EntityType).filter(models.EntityType.id == entity_type_id)
            if not current_user.is_superuser:
                query = query.filter(models.EntityType.tenant_id == current_user.tenant_id)
            db_entity_type = query.first()

            if not db_entity_type:
                raise HTTPException(status_code=404, detail="Тип сущности не найден")

            # 3. Загружаем ВСЕ его атрибуты
            all_attributes = db.query(models.Attribute).filter(
                models.Attribute.entity_type_id == entity_type_id
            ).all()

            # 4. Загружаем сохраненный порядок для этого пользователя
            saved_order_query = db.query(models.AttributeOrder.attribute_id).filter(
                models.AttributeOrder.user_id == current_user.id,
                models.AttributeOrder.entity_type_id == entity_type_id
            ).order_by(models.AttributeOrder.position)

            saved_order_ids = [item_id for item_id, in saved_order_query]

            # 5. Применяем сортировку в Python
            sorted_attributes = []
            if saved_order_ids:
                attributes_map = {attr.id: attr for attr in all_attributes}
                for attr_id in saved_order_ids:
                    if attr_id in attributes_map:
                        sorted_attributes.append(attributes_map.pop(attr_id))

                # Добавляем оставшиеся (новые) атрибуты, отсортировав их по ID
                sorted_attributes.extend(sorted(attributes_map.values(), key=lambda attr: attr.id))
            else:
                # Сортировка по умолчанию
                sorted_attributes = sorted(all_attributes, key=lambda attr: attr.id)

            # 6. Создаем Pydantic-модель, подставляя в нее уже отсортированные атрибуты
            response_entity_type = EntityType.model_validate(db_entity_type)
            response_entity_type.attributes = sorted_attributes

            # 7. Применяем псевдонимы
            attr_aliases = self.alias_service.get_aliases_for_tenant(current_user=current_user)
            table_aliases = self.alias_service.get_table_aliases_for_tenant(current_user=current_user)
            table_name = response_entity_type.name
            if table_name in table_aliases:
                response_entity_type.display_name = table_aliases[table_name]

            table_attr_aliases = attr_aliases.get(table_name, {})
            for attribute in response_entity_type.attributes:
                if attribute.name in table_attr_aliases:
                    attribute.display_name = table_attr_aliases[attribute.name]

            return response_entity_type

        finally:
            db.close()

    def set_attribute_order(
            self,
            entity_type_id: int,
            attribute_ids: List[int],
            current_user: models.User
    ):
        """Сохраняет новый порядок колонок для пользователя."""
        # Открываем новую сессию для чистоты операции
        db = session.SessionLocal()
        try:
            # 1. Проверяем, что таблица существует и доступна пользователю
            # Важно! Вызываем get_entity_type_by_id с той же сессией `db`
            # (Для этого его нужно немного доработать или просто проверить существование)
            entity_type = db.query(models.EntityType).filter(models.EntityType.id == entity_type_id).first()
            if not entity_type or (not current_user.is_superuser and entity_type.tenant_id != current_user.tenant_id):
                raise HTTPException(status_code=404, detail="Тип сущности не найден")

            # 2. Удаляем старый порядок для этого пользователя и этой таблицы
            db.query(models.AttributeOrder).filter(
                models.AttributeOrder.user_id == current_user.id,
                models.AttributeOrder.entity_type_id == entity_type_id
            ).delete(synchronize_session=False)

            # 3. Создаем новые записи с новым порядком
            new_order_entries = []
            for position, attr_id in enumerate(attribute_ids):
                new_order_entries.append(
                    models.AttributeOrder(
                        user_id=current_user.id,
                        entity_type_id=entity_type_id,
                        attribute_id=attr_id,
                        position=position
                    )
                )

            if new_order_entries:
                db.add_all(new_order_entries)

            db.commit()
        finally:
            db.close()

        return {"status": "ok", "ordered_ids": attribute_ids}

    # Методы create/delete для метаданных остаются без изменений,
    # так как они либо создают сущность в текущем тенанте,
    # либо используют get_entity_type_by_id, который уже содержит проверки.





    def delete_entity_type(self, entity_type_id: int, current_user: models.User):
        """
        Удалить тип сущности и ВСЕ связанные с ним данные (атрибуты, сущности, значения).
        Это необратимая операция!
        """
        # 1. Находим таблицу, которую нужно удалить.
        # Метод get_entity_type_by_id уже содержит проверку прав (tenant_id).
        entity_type_to_delete = self.get_entity_type_by_id(
            entity_type_id=entity_type_id,
            current_user=current_user
        )

        # SQLAlchemy объект, возвращенный из get_entity_type_by_id, - это Pydantic модель.
        # Нам нужен оригинальный объект SQLAlchemy для удаления.
        db_entity_type = self.db.query(models.EntityType).filter(
            models.EntityType.id == entity_type_id
        ).first()

        # 2. Удаляем объект. Благодаря cascade="all, delete-orphan" в моделях,
        # SQLAlchemy и база данных позаботятся об удалении всех дочерних записей.
        if db_entity_type:
            self.db.delete(db_entity_type)
            self.db.commit()

        # Для операции DELETE принято возвращать None.
        return None
    # --- МЕТОДЫ ДЛЯ ДАННЫХ (Строки в таблицах) ---

    def _pivot_data(self, entity: models.Entity) -> Dict[str, Any]:
        result = {"id": entity.id, "created_at": entity.created_at, "updated_at": entity.updated_at}
        # --- ИСПРАВЛЕНИЕ: Добавляем проверку, что атрибуты существуют ---
        if entity.values and entity.values[0].attribute:
            result['tenant_id'] = entity.values[0].attribute.entity_type.tenant_id
        # -------------------------------------------------------------
        for value_obj in entity.values:
            attr_name = value_obj.attribute.name
            value_type = value_obj.attribute.value_type
            db_field = VALUE_FIELD_MAP[value_type]
            result[attr_name] = getattr(value_obj, db_field)
        return result

    def get_all_entities_for_type(
            self,
            entity_type_name: str,
            current_user: models.User,
            tenant_id: Optional[int] = None,
            filters: List[Dict[str, Any]] = None,
            sort_by: str = 'created_at',
            sort_order: str = 'desc',
            skip: int = 0,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получить все записи для указанного типа сущности с фильтрацией, сортировкой и пагинацией.
        """
        # 1. Получаем метаданные таблицы (проверка прав происходит внутри этого метода)
        # 1. Если запрос от обычного пользователя, игнорируем tenant_id из запроса.
        # Это "защита от дурака" на случай, если фронтенд пришлет неверный ID.
        if not current_user.is_superuser:
            tenant_id = None

        entity_type = self._get_entity_type_by_name(entity_type_name, current_user, tenant_id)
        attributes_map = {attr.name: attr for attr in entity_type.attributes}

        # 2. Начинаем строить основной запрос к "строкам" (Entities)
        query = self.db.query(models.Entity).filter(
            models.Entity.entity_type_id == entity_type.id
        )
        # 3. Динамически применяем фильтры
        if filters:
            for f in filters:
                field_name = f.get("field")
                op = f.get("op", "eq")
                value = f.get("value")

                if not field_name or field_name not in attributes_map:
                    continue

                attribute = attributes_map[field_name]
                value_column = getattr(models.AttributeValue, VALUE_FIELD_MAP[attribute.value_type])

                subquery = self.db.query(models.AttributeValue.id).filter(
                    models.AttributeValue.entity_id == models.Entity.id,
                    models.AttributeValue.attribute_id == attribute.id
                )

                # --- ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ДЛЯ КИРИЛЛИЦЫ ---
                if attribute.value_type == 'string' and isinstance(value, str):
                    # Для строковых полей используем ILIKE, который должен быть
                    # регистронезависимым благодаря настройке в db/session.py.
                    if op == "eq":
                        # Точное совпадение без учета регистра
                        subquery = subquery.filter(value_column.ilike(value))
                    elif op == "contains":
                        # Поиск подстроки без учета регистра
                        subquery = subquery.filter(value_column.ilike(f"%{value}%"))
                    elif op == "neq":
                        # НЕ равно без учета регистра
                        # Используем func.lower для надежности
                        subquery = subquery.filter(func.lower(value_column) != value.lower())
                    else:
                        continue
                else:
                    # Для не-строковых типов данных (числа, даты) оставляем старую логику
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
                    else:
                        continue
                # -----------------------------------------------

                query = query.filter(subquery.exists())

        # 4. Применяем сортировку
        sort_func = desc if sort_order.lower() == 'desc' else asc

        if sort_by == 'created_at':
            query = query.order_by(sort_func(models.Entity.created_at))
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

            # nullslast()/nullsfirst() важны, чтобы записи без значения были в конце/начале
            order_expression = sort_func(sort_value_column).nullslast() if sort_order.lower() == 'desc' else sort_func(
                sort_value_column).nullsfirst()
            query = query.order_by(order_expression)

        # 5. Применяем пагинацию
        entities_page = query.offset(skip).limit(limit).all()

        # 6. Если на странице ничего нет, возвращаем пустой список
        if not entities_page:
            return []

        # 7. Загружаем полные данные (со значениями) только для записей на этой странице
        entity_ids_on_page = [e.id for e in entities_page]

        # Создаем запрос для получения полных данных
        final_query = self.db.query(models.Entity).filter(
            models.Entity.id.in_(entity_ids_on_page)
        ).options(
            joinedload(models.Entity.values).joinedload(models.AttributeValue.attribute)
        )

        # Получаем полные данные
        full_entities = final_query.all()

        # 8. Финальная сортировка в Python, так как `IN` не гарантирует порядок
        # Создаем словарь {id: entity} для быстрой сортировки
        entities_map = {entity.id: entity for entity in full_entities}
        sorted_entities = [entities_map[id] for id in entity_ids_on_page if id in entities_map]

        return [self._pivot_data(e) for e in sorted_entities]




    def create_entity_type(self, entity_type_in: EntityTypeCreate, current_user: models.User) -> models.EntityType:
        """
        Создает новый тип сущности ('таблицу') и автоматически генерирует
        для него набор разрешений (permissions).
        """
        # Проверка на существование таблицы у этого клиента
        existing = self.db.query(models.EntityType).filter(
            models.EntityType.name == entity_type_in.name,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Тип сущности с именем '{entity_type_in.name}' уже существует")

        # 1. Создаем саму таблицу (EntityType)
        db_entity_type = models.EntityType(
            **entity_type_in.model_dump(),
            tenant_id=current_user.tenant_id
        )
        self.db.add(db_entity_type)

        # 2. Готовим разрешения для создания
        table_name = entity_type_in.name
        permission_templates = {
            f"data:view:{table_name}": f"Просмотр данных в таблице '{entity_type_in.display_name}'",
            f"data:edit:{table_name}": f"Редактирование данных в таблице '{entity_type_in.display_name}'",
            f"data:create:{table_name}": f"Создание записей в таблице '{entity_type_in.display_name}'",
            f"data:delete:{table_name}": f"Удаление записей из таблицы '{entity_type_in.display_name}'",
        }

        # Получаем имена уже существующих разрешений, чтобы не создавать дубликаты
        existing_perms_query = self.db.query(models.Permission.name).filter(
            models.Permission.name.in_(permission_templates.keys())
        )
        existing_perms = {name for name, in existing_perms_query}

        permissions_to_create = []
        for name, description in permission_templates.items():
            if name not in existing_perms:
                permissions_to_create.append(
                    models.Permission(name=name, description=description)
                )

        if permissions_to_create:
            self.db.add_all(permissions_to_create)

        # 3. Коммитим все изменения (и таблицу, и разрешения)
        self.db.commit()
        self.db.refresh(db_entity_type)

        # 4. Создаем системные атрибуты
        system_attributes = [
            {"name": "send_sms_trigger", "display_name": "Отправить SMS", "value_type": "boolean"},
            {"name": "sms_status", "display_name": "Статус отправки", "value_type": "string"},
            {"name": "sms_last_error", "display_name": "Ошибка отправки", "value_type": "string"},
            {"name": "phone_number", "display_name": "Номер телефона", "value_type": "string"},
            {"name": "message_text", "display_name": "Текст сообщения", "value_type": "string"},
            # --- ДОБАВЬТЕ ЭТИ ДВЕ СТРОКИ ---
            {"name": "creation_date", "display_name": "Дата создания", "value_type": "date"},
            {"name": "modification_date", "display_name": "Дата изменения", "value_type": "date"},
            #
        ]

        for attr_data in system_attributes:
            attr_exists = self.db.query(models.Attribute).filter_by(
                name=attr_data['name'],
                entity_type_id=db_entity_type.id
            ).first()
            if not attr_exists:
                attr = models.Attribute(**attr_data, entity_type_id=db_entity_type.id)
                self.db.add(attr)

        self.db.commit()
        self.db.refresh(db_entity_type)

        return db_entity_type

    # --- ДОБАВЬТЕ ЭТОТ МЕТОД ---
    def create_attribute_for_type(
            self,
            entity_type_id: int,
            attribute_in: AttributeCreate,
            current_user: models.User
    ) -> models.Attribute:
        """
        Создает новый атрибут ('колонку') для указанного типа сущности.
        """
        # 1. Проверяем, существует ли тип сущности и имеет ли пользователь к нему доступ.
        # Метод get_entity_type_by_id уже содержит все нужные проверки.
        entity_type = self.get_entity_type_by_id(entity_type_id, current_user)

        # 2. Проверяем, не существует ли уже атрибут с таким системным именем в этой таблице.
        existing_attr = self.db.query(models.Attribute).filter(
            models.Attribute.entity_type_id == entity_type_id,
            models.Attribute.name == attribute_in.name
        ).first()
        if existing_attr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Атрибут с системным именем '{attribute_in.name}' уже существует для этого типа сущности"
            )

        # 3. Создаем новый атрибут.
        db_attribute = models.Attribute(
            **attribute_in.model_dump(),
            entity_type_id=entity_type_id
        )
        self.db.add(db_attribute)
        self.db.commit()
        self.db.refresh(db_attribute)

        return db_attribute





    def get_entity_by_id(self, entity_id: int, current_user: models.User) -> Dict[str, Any]:
        """Получить одну запись по ID с проверкой прав."""
        entity = self.db.query(models.Entity).options(
            joinedload(models.Entity.values).joinedload(models.AttributeValue.attribute).joinedload(
                models.Attribute.entity_type)
        ).get(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        # --- ИСПРАВЛЕНИЕ: Проверка прав доступа ---
        if not current_user.is_superuser:
            if entity.entity_type.tenant_id != current_user.tenant_id:
                raise HTTPException(status_code=404, detail="Сущность не найдена")

        return self._pivot_data(entity)






    def update_entity(self, entity_id: int, data: Dict[str, Any], current_user: models.User) -> Dict[str, Any]:
        """Обновить запись с корректным преобразованием типов."""
        from tasks.messaging import send_sms_for_entity_task

        # 1. Сначала получаем сущность с проверкой прав, чтобы убедиться в доступе.
        self.get_entity_by_id(entity_id, current_user)

        # 2. Загружаем сам SQLAlchemy объект для работы
        entity = self.db.query(models.Entity).options(
            joinedload(models.Entity.entity_type).joinedload(models.EntityType.attributes)
        ).get(entity_id)

        if not entity:  # Дополнительная проверка на случай, если сущность удалили
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        attributes_map = {attr.name: attr for attr in entity.entity_type.attributes}

        # --- ДОБАВЬТЕ ЭТУ СТРОКУ ПЕРЕД ОБНОВЛЕНИЕМ ---
        # Внедряем текущую дату, если колонка "Дата изменения" существует
        if 'modification_date' in attributes_map:
            data['modification_date'] = datetime.utcnow().isoformat()
        # -------------------------------------------------

        # 3. Проверяем триггер SMS и модифицируем входящие данные
        if data.get("send_sms_trigger") is True:
            data["sms_status"] = "pending"
            data["send_sms_trigger"] = False  # Сбрасываем триггер
            send_sms_for_entity_task.delay(entity_id=entity_id, user_id=current_user.id)

        # 4. Обновляем значения атрибутов
        for key, value in data.items():
            if key not in attributes_map:
                continue

            attribute = attributes_map[key]
            # Используем нашу вспомогательную функцию для очистки и конвертации
            processed_value = self._process_value(value, attribute.value_type)
            value_field_name = VALUE_FIELD_MAP[attribute.value_type]

            # Ищем, существует ли уже значение для этого атрибута
            existing_value = self.db.query(models.AttributeValue).filter_by(
                entity_id=entity_id, attribute_id=attribute.id
            ).first()

            if existing_value:
                if processed_value is None:
                    # Если новое значение пустое, удаляем старое
                    self.db.delete(existing_value)
                else:
                    # Иначе обновляем.
                    # Сначала обнуляем все value_* поля на случай смены типа
                    for field in VALUE_FIELD_MAP.values():
                        setattr(existing_value, field, None)
                    # Затем устанавливаем новое значение в правильное поле
                    setattr(existing_value, value_field_name, processed_value)

            elif processed_value is not None:
                # Если значения не было, а новое не пустое, создаем его
                new_value_data = {
                    "entity_id": entity_id,
                    "attribute_id": attribute.id,
                    value_field_name: processed_value
                }
                new_value = models.AttributeValue(**new_value_data)
                self.db.add(new_value)

        # 5. Обновляем `updated_at` у самой сущности
        entity.updated_at = datetime.utcnow()
        self.db.add(entity)

        # 6. Сохраняем все изменения
        self.db.commit()

        # 7. Возвращаем ПОЛНЫЙ и ОБНОВЛЕННЫЙ объект
        return self.get_entity_by_id(entity_id, current_user)






    # --- ИМПОРТ ЗАДАЧИ ВНУТРИ МЕТОДА ---

    def _process_value(self, value, value_type):
        """Вспомогательная функция для обработки и конвертации значений."""
        # 1. Сразу отсекаем None
        if value is None:
            return None

        # 2. Пустые строки для всех типов считаем как None
        if isinstance(value, str) and value.strip() == '':
            return None

        # 3. Конвертируем типы, если значение не None
        try:
            if value_type == 'date' and isinstance(value, str):
                return datetime.fromisoformat(value)
            if value_type == 'time' and isinstance(value, str):
                # Преобразуем строку "HH:MM:SS" в объект time
                return time.fromisoformat(value)
            if value_type == 'integer' and not isinstance(value, int):
                return int(value)
            if value_type == 'float' and not isinstance(value, float):
                return float(value)
        except (ValueError, TypeError):
            # Если конвертация не удалась, считаем значение невалидным (None)
            return None

        return value

    def create_entity(self, entity_type_name: str, data: Dict[str, Any], current_user: models.User) -> Dict[str, Any]:
        """Создать новую запись с корректным преобразованием типов."""
        entity_type = self._get_entity_type_by_name(entity_type_name, current_user)
        attributes_map = {attr.name: attr for attr in entity_type.attributes}

        # --- ДОБАВЬТЕ ЭТУ СТРОКУ ПЕРЕД СОЗДАНИЕМ ЗАПИСИ ---
        # Внедряем текущую дату, если колонка "Дата создания" существует
        if 'creation_date' in attributes_map:
            data['creation_date'] = datetime.utcnow().isoformat()

        new_entity = models.Entity(entity_type_id=entity_type.id)
        self.db.add(new_entity)
        self.db.flush()

        for key, value in data.items():
            if key not in attributes_map:
                continue

            attribute = attributes_map[key]
            processed_value = self._process_value(value, attribute.value_type)

            if processed_value is None:
                continue

            value_field_name = VALUE_FIELD_MAP[attribute.value_type]
            attr_value = models.AttributeValue(
                entity_id=new_entity.id, attribute_id=attribute.id
            )
            setattr(attr_value, value_field_name, processed_value)
            self.db.add(attr_value)

        self.db.commit()
        return self.get_entity_by_id(new_entity.id, current_user)










    def delete_entity(self, entity_id: int, current_user: models.User):
        """Удалить запись."""
        # --- ИСПРАВЛЕНИЕ: Сначала получаем сущность с проверкой прав ---
        db_entity = self.get_entity_by_id(entity_id, current_user)
        # SQLAlchemy объект нужно получить снова для удаления
        entity_to_delete = self.db.query(models.Entity).get(db_entity['id'])
        self.db.delete(entity_to_delete)
        self.db.commit()
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





    def update_entity_type(
            self,
            entity_type_id: int,
            entity_type_in: EntityTypeUpdate,
            current_user: models.User
    ) -> models.EntityType:
        """
        Обновить отображаемое имя для типа сущности.
        """
        # 1. Находим объект SQLAlchemy для обновления, используя метод,
        # который уже содержит проверку прав.
        # Нам нужен именно объект БД, а не Pydantic-схема.
        db_entity_type = self.db.query(models.EntityType).filter(
            models.EntityType.id == entity_type_id
        ).first()

        # Проверяем, что объект найден и принадлежит пользователю
        if not db_entity_type or (not current_user.is_superuser and db_entity_type.tenant_id != current_user.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тип сущности не найден"
            )

        # 2. Обновляем поле
        db_entity_type.display_name = entity_type_in.display_name

        # 3. Сохраняем изменения
        self.db.add(db_entity_type)
        self.db.commit()
        self.db.refresh(db_entity_type)

        return db_entity_type






    # --- ДОБАВЬТЕ ЭТОТ НОВЫЙ МЕТОД ---
    def create_entity_and_get_list(
            self,
            entity_type_name: str,
            data: Dict[str, Any],
            current_user: models.User
    ) -> List[Dict[str, Any]]:
        """
        Создает новую сущность, а затем возвращает полный список всех сущностей
        для этого типа, отсортированный по умолчанию (новые вверху).
        """
        # 1. Сначала просто создаем новую запись, используя уже существующий метод
        self.create_entity(entity_type_name, data, current_user)

        # 2. Теперь вызываем метод для получения полного списка
        # Он уже умеет сортировать по умолчанию (created_at desc)
        full_sorted_list = self.get_all_entities_for_type(
            entity_type_name=entity_type_name,
            current_user=current_user
            # Мы не передаем другие параметры, чтобы использовались значения по умолчанию
        )

        return full_sorted_list








    def delete_multiple_entities(
            self,
            entity_type_name: str,
            ids: List[int],
            current_user: models.User
    ) -> int:
        """
        Удаляет несколько записей (сущностей) по списку их ID.
        Возвращает количество удаленных записей.
        """
        # 1. Сначала получаем метаданные таблицы, чтобы убедиться, что она
        # существует и принадлежит текущему пользователю (проверка прав).
        entity_type = self._get_entity_type_by_name(entity_type_name, current_user)

        # 2. Строим запрос на удаление.
        query = self.db.query(models.Entity).filter(
            models.Entity.entity_type_id == entity_type.id,
            models.Entity.id.in_(ids)
        )

        # Для суперадминистратора эта проверка не нужна, но для обычного пользователя
        # она гарантирует, что он не сможет удалить записи из чужой таблицы,
        # даже если она имеет то же имя.
        if not current_user.is_superuser:
            query = query.filter(models.Entity.entity_type.has(tenant_id=current_user.tenant_id))

        # 3. Выполняем удаление и получаем количество удаленных строк.
        # synchronize_session=False рекомендуется для массовых операций.
        num_deleted = query.delete(synchronize_session=False)

        # 4. Коммитим транзакцию.
        self.db.commit()

        return num_deleted

    def set_attribute_order(
            self,
            entity_type_id: int,
            attribute_ids: List[int],
            current_user: models.User
    ):
        """Сохраняет новый порядок колонок для пользователя."""
        # Проверяем, что таблица существует и доступна пользователю
        self.get_entity_type_by_id(entity_type_id, current_user)

        # 1. Удаляем старый порядок для этого пользователя и этой таблицы
        self.db.query(models.AttributeOrder).filter(
            models.AttributeOrder.user_id == current_user.id,
            models.AttributeOrder.entity_type_id == entity_type_id
        ).delete(synchronize_session=False)

        # 2. Создаем новые записи с новым порядком
        new_order_entries = []
        for position, attr_id in enumerate(attribute_ids):
            new_order_entries.append(
                models.AttributeOrder(
                    user_id=current_user.id,
                    entity_type_id=entity_type_id,
                    attribute_id=attr_id,
                    position=position
                )
            )

        if new_order_entries:
            self.db.add_all(new_order_entries)

        self.db.commit()
        return {"status": "ok", "ordered_ids": attribute_ids}