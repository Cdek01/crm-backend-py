#services/eav_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, asc, desc, func
from sqlalchemy.orm import aliased
from db import models, session
from schemas.eav import EntityType, EntityTypeCreate, Attribute, AttributeCreate, EntityTypeUpdate, AttributeUpdate
from .alias_service import AliasService
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from email_validator import validate_email, EmailNotValidError
import validators
import time
from . import external_api_client
import re
# from tasks.messaging import send_webhook_task
from sqlalchemy import or_, cast, Text
import logging # <-- ШАГ 1: Добавьте этот импорт
# from tasks.enrichment import enrich_data_by_inn_task # <-- ДОБАВЬТЕ ЭТО


logger = logging.getLogger(__name__)

VALUE_FIELD_MAP = {
    "string": "value_string",
    "integer": "value_integer",
    "float": "value_float",
    "date": "value_date",
    "boolean": "value_boolean",
    "time": "value_time",
    "select": "value_string",
    "email": "value_string",
    "phone": "value_string",
    "url": "value_string",
    "percent": "value_float",
    "currency": "value_float",
    "relation": "value_integer",  # Ключ связи (например, ИНН) будем хранить как строку
    "multiselect": "value_string",  # Multi-select тоже будет хранить строки (например, "Тег1,Тег2")

}


class EAVService:
    def __init__(self, db: Session = Depends(session.get_db), alias_service: AliasService = Depends()):
        self.db = db
        self.alias_service = alias_service

    def _parse_date_filter_value(self, value: Any) -> date:
        """
        Интерпретирует значение из фильтра для дат и возвращает объект date.
        """
        today = date.today()

        if isinstance(value, str):
            if value == 'today': return today
            if value == 'tomorrow': return today + timedelta(days=1)
            if value == 'yesterday': return today - timedelta(days=1)
            if value == 'one_week_ago': return today - timedelta(weeks=1)
            if value == 'one_week_from_now': return today + timedelta(weeks=1)
            if value == 'one_month_ago': return today - relativedelta(months=1)
            if value == 'one_month_from_now': return today + relativedelta(months=1)
            # Если это строка с точной датой
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail=f"Неверный формат точной даты: {value}")

        if isinstance(value, dict):
            amount = value.get('amount', 0)
            # unit пока всегда 'days', но можно расширить
            if 'ago' in value.get('type', ''):  # type будет 'number_of_days_ago'
                return today - timedelta(days=amount)
            if 'from_now' in value.get('type', ''):  # type будет 'number_of_days_from_now'
                return today + timedelta(days=amount)

        raise HTTPException(status_code=400, detail=f"Неподдерживаемый формат значения для фильтра по дате: {value}")



    def _parse_time_filter_value(self, value: Any) -> time:
        """Интерпретирует значение из фильтра для времени и возвращает объект time."""
        if isinstance(value, str):
            try:
                # Ожидаем время в формате "HH:MM:SS" или "HH:MM"
                return time.fromisoformat(value)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail=f"Неверный формат времени: {value}")
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый формат значения для фильтра по времени: {value}")




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




    # def get_all_entity_types(self, current_user: models.User) -> List[EntityType]:
    #     db_user = self.db.query(models.User).options(
    #         joinedload(models.User.roles).joinedload(models.Role.permissions)
    #     ).filter(models.User.id == current_user.id).one()
    #     user_permissions = {perm.name for role in db_user.roles for perm in role.permissions}
    #     accessible_table_names = {p.split(':')[2] for p in user_permissions if
    #                               p.startswith("data:") and len(p.split(':')) == 3}
    #     query = self.db.query(models.EntityType).options(
    #         joinedload(models.EntityType.attributes)
    #     ).order_by(models.EntityType.id)
    #     if not current_user.is_superuser:
    #         query = query.filter(
    #             or_(
    #                 models.EntityType.tenant_id == current_user.tenant_id,
    #                 models.EntityType.name.in_(accessible_table_names)
    #             )
    #         )
    #     db_entity_types = query.all()
    #     attr_aliases = self.alias_service.get_aliases_for_tenant(current_user=current_user)
    #     table_aliases = self.alias_service.get_table_aliases_for_tenant(current_user=current_user)
    #     response_list = []
    #     for db_entity_type in db_entity_types:
    #         sorted_attrs = self._apply_attribute_order(self.db, db_entity_type.id, db_entity_type.attributes,
    #                                                    current_user)
    #         response_entity = EntityType.model_validate(db_entity_type)
    #         response_entity.attributes = sorted_attrs
    #         if response_entity.name in table_aliases:
    #             response_entity.display_name = table_aliases[response_entity.name]
    #         table_attr_aliases = attr_aliases.get(response_entity.name, {})
    #         for attribute in response_entity.attributes:
    #             if attribute.name in table_attr_aliases:
    #                 attribute.display_name = table_attr_aliases[attribute.name]
    #         response_list.append(response_entity)
    #     return response_list
    def get_all_entity_types(self, current_user: models.User) -> List[EntityType]:
        """
        Возвращает список всех типов сущностей, доступных пользователю.
        Включает в себя:
        1. Все таблицы, принадлежащие собственному тенанту пользователя.
        2. Таблицы из других тенантов, к которым пользователю предоставлен доступ через права (permissions).
        Логика разделена на два запроса для обеспечения безопасности и консистентности данных.
        """
        # --- НАЧАЛО ИЗМЕНЕНИЙ ---

        response_list = []
        processed_ids = set()  # Сет для отслеживания уже обработанных таблиц, чтобы избежать дублей

        # 1. ПОТОК А: Загружаем все "свои" таблицы, принадлежащие тенанту пользователя
        own_entity_types_query = self.db.query(models.EntityType).options(
            joinedload(models.EntityType.attributes)
        ).filter(models.EntityType.tenant_id == current_user.tenant_id).order_by(models.EntityType.id)

        own_entity_types = own_entity_types_query.all()

        # Получаем алиасы один раз для всего тенанта
        attr_aliases = self.alias_service.get_aliases_for_tenant(current_user=current_user)
        table_aliases = self.alias_service.get_table_aliases_for_tenant(current_user=current_user)

        for db_entity_type in own_entity_types:
            # Применяем пользовательский порядок сортировки атрибутов
            sorted_attrs = self._apply_attribute_order(self.db, db_entity_type.id, db_entity_type.attributes,
                                                       current_user)

            # Преобразуем в Pydantic-схему и применяем алиасы
            response_entity = EntityType.model_validate(db_entity_type)
            response_entity.attributes = sorted_attrs

            if response_entity.name in table_aliases:
                response_entity.display_name = table_aliases[response_entity.name]

            table_attr_aliases = attr_aliases.get(response_entity.name, {})
            for attribute in response_entity.attributes:
                if attribute.name in table_attr_aliases:
                    attribute.display_name = table_attr_aliases[attribute.name]

            response_list.append(response_entity)
            processed_ids.add(db_entity_type.id)

        # 2. ПОТОК Б: Загружаем "расшаренные" таблицы из других тенантов
        if not current_user.is_superuser:
            # Получаем права пользователя, чтобы найти доступные ему таблицы
            db_user = self.db.query(models.User).options(
                joinedload(models.User.roles).joinedload(models.Role.permissions)
            ).filter(models.User.id == current_user.id).one()
            user_permissions = {perm.name for role in db_user.roles for perm in role.permissions}

            accessible_table_names = {p.split(':')[2] for p in user_permissions if
                                      p.startswith("data:") and len(p.split(':')) == 3}

            if accessible_table_names:
                # Ищем ID таблиц, которые доступны по правам, но НЕ принадлежат текущему тенанту
                shared_entity_type_ids_query = self.db.query(models.EntityType.id).filter(
                    models.EntityType.name.in_(accessible_table_names),
                    models.EntityType.tenant_id != current_user.tenant_id
                )
                shared_entity_type_ids = [id for id, in shared_entity_type_ids_query]

                for entity_type_id in shared_entity_type_ids:
                    if entity_type_id not in processed_ids:
                        try:
                            # Используем уже существующий безопасный метод для получения полной информации о чужой таблице
                            # Важно, чтобы get_entity_type_by_id корректно проверял права доступа
                            shared_entity_type = self.get_entity_type_by_id(entity_type_id, current_user)
                            response_list.append(shared_entity_type)
                            processed_ids.add(entity_type_id)
                        except HTTPException as e:
                            # Если по какой-то причине доступ к метаданным получить не удалось,
                            # логируем ошибку и пропускаем эту таблицу, чтобы не сломать фронтенд.
                            logger.error(
                                f"Could not fetch shared entity type {entity_type_id} for user {current_user.id}: {e.detail}")

        # Финальная сортировка списка по ID, чтобы порядок был консистентным
        response_list.sort(key=lambda x: x.id)

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

        # --- ИЗМЕНЕНИЕ: ЖАДНАЯ ЗАГРУЗКА ДАННЫХ О СВЯЗЯХ ---
        # После того как мы нашли ID и проверили права, делаем полный запрос
        # с загрузкой всех необходимых данных для построения связей.
        full_entity_type = self.db.query(models.EntityType).options(
            joinedload(models.EntityType.attributes).joinedload(models.Attribute.source_attribute),
            joinedload(models.EntityType.attributes).joinedload(models.Attribute.target_attribute),
            joinedload(models.EntityType.attributes).joinedload(models.Attribute.display_attribute)
        ).filter(models.EntityType.id == result.id).one()

        return self.db.query(models.EntityType).options(joinedload(models.EntityType.attributes)).get(result.id)

    def get_entity_type_by_id(self, entity_type_id: int, current_user: models.User) -> EntityType:
        db = session.SessionLocal()
        try:
            query = db.query(models.EntityType).filter(models.EntityType.id == entity_type_id)
            if not current_user.is_superuser:
                query = query.filter(models.EntityType.tenant_id == current_user.tenant_id)
            db_entity_type = query.first()
            if not db_entity_type:
                raise HTTPException(status_code=404, detail="Тип сущности не найден")

            all_attributes = db.query(models.Attribute).filter(
                models.Attribute.entity_type_id == entity_type_id
            ).all()

            sorted_attributes = self._apply_attribute_order(db, entity_type_id, all_attributes, current_user)

            response_entity_type = EntityType.model_validate(db_entity_type)
            response_entity_type.attributes = sorted_attributes

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
        db_entity_type = self.db.query(models.EntityType).filter(
            models.EntityType.id == entity_type_id,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()
        if not db_entity_type:
            raise HTTPException(status_code=404, detail="Тип сущности не найден")
        self.db.delete(db_entity_type)
        self.db.commit()
        return None

    def _pivot_data(self, entity: models.Entity) -> Dict[str, Any]:
        result = {
            "id": entity.id,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "position": entity.position
        }
        if entity.values and entity.values[0].attribute:
            result['tenant_id'] = entity.values[0].attribute.entity_type.tenant_id

        for value_obj in entity.values:
            attr = value_obj.attribute
            attr_name = attr.name
            value_type = attr.value_type

            if value_type == 'relation' and attr.allow_multiple_selection:
                result[attr_name] = [link.id for link in value_obj.many_to_many_links]
            elif value_type == 'multiselect':
                result[attr_name] = [
                    {"id": opt.id, "value": opt.value}
                    for opt in value_obj.multiselect_values
                ]
            elif value_type in VALUE_FIELD_MAP:
                db_field = VALUE_FIELD_MAP[value_type]
                result[attr_name] = getattr(value_obj, db_field)

        for attribute in entity.entity_type.attributes:
            if attribute.value_type == 'formula' and attribute.formula_text:
                formula_value = self._calculate_formula(attribute.formula_text, result)
                result[attribute.name] = formula_value

        return result






    def get_all_entities_for_type(
            self,
            entity_type_name: str,
            current_user: models.User,
            q: Optional[str] = None,
            search_fields: List[str] = None,
            tenant_id: Optional[int] = None,
            filters: List[Dict[str, Any]] = None,
            sort_by: str = 'position',
            sort_order: str = 'desc',
            skip: int = 0,
            limit: int = 100
    ) -> Dict[str, Any]:
        if not current_user.is_superuser:
            tenant_id = None
        entity_type = self._get_entity_type_by_name(entity_type_name, current_user, tenant_id)
        attributes_map = {attr.name: attr for attr in entity_type.attributes}
        query = self.db.query(models.Entity).filter(
            models.Entity.entity_type_id == entity_type.id
        )
        # ----------------------------------------------------

        attributes_map = {attr.name: attr for attr in entity_type.attributes}

        # 4. Строим основной запрос к данным (Entities)
        query = self.db.query(models.Entity).filter(
            models.Entity.entity_type_id == entity_type.id
        )

        # --- НАЧАЛО НОВОГО БЛОКА ДЛЯ УНИВЕРСАЛЬНОГО ПОИСКА ---
        if q and q.strip():
            search_term = f"%{q.strip()}%"

            # Находим ID атрибутов, по которым нужно искать
            target_attribute_ids = []
            if search_fields:
                for attr in entity_type.attributes:
                    if attr.name in search_fields:
                        target_attribute_ids.append(attr.id)

            # Если specific_fields не указан, ищем по всем (как и раньше)

            matching_entity_ids_subquery = self.db.query(models.AttributeValue.entity_id).filter(
                or_(
                    models.AttributeValue.value_string.ilike(search_term),
                    cast(models.AttributeValue.value_integer, Text).like(search_term),
                    cast(models.AttributeValue.value_float, Text).like(search_term)
                )
            )

            # Если указаны конкретные поля, добавляем это условие в подзапрос
            if target_attribute_ids:
                matching_entity_ids_subquery = matching_entity_ids_subquery.filter(
                    models.AttributeValue.attribute_id.in_(target_attribute_ids)
                )

            matching_entity_ids_subquery = matching_entity_ids_subquery.distinct()
            query = query.filter(models.Entity.id.in_(matching_entity_ids_subquery))
        # --- КОНЕЦ НОВОГО БЛОКА ---


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

                # 1. Сначала обрабатываем универсальные операторы
                if op == 'blank':
                    query = query.filter(~subquery.exists())
                    continue
                elif op == 'not_blank':
                    query = query.filter(subquery.exists())
                    continue

                # 2. Теперь обрабатываем по типам
                if attribute.value_type in ['string', 'email', 'phone', 'url'] and isinstance(value, str):
                    if op == "eq":
                        # Для SQLite ilike регистронезависим только для ASCII.
                        # func.lower() - самый надежный способ.
                        subquery = subquery.filter(func.lower(value_column) == value.lower())
                    elif op == "contains":
                        subquery = subquery.filter(func.lower(value_column).contains(value.lower()))
                    elif op == "neq":
                        subquery = subquery.filter(func.lower(value_column) != value.lower())
                    else:
                        continue

                elif attribute.value_type == 'date':
                    if op == 'is_within':
                        start_date = self._parse_date_filter_value(value[0])
                        end_date = self._parse_date_filter_value(value[1])
                        start_dt = datetime.combine(start_date, datetime.time.min)
                        end_dt = datetime.combine(end_date, datetime.time.max)
                        subquery = subquery.filter(value_column.between(start_dt, end_dt))
                    else:
                        target_date = self._parse_date_filter_value(value)
                        start_of_day = datetime.combine(target_date, datetime.time.min)
                        end_of_day = datetime.combine(target_date, datetime.time.max)
                        if op == 'is':
                            subquery = subquery.filter(value_column.between(start_of_day, end_of_day))
                        elif op == 'is_not':
                            subquery = subquery.filter(~value_column.between(start_of_day, end_of_day))
                        elif op == 'is_after':
                            subquery = subquery.filter(value_column > end_of_day)
                        elif op == 'is_before':
                            subquery = subquery.filter(value_column < start_of_day)
                        elif op == 'is_on_or_after':
                            subquery = subquery.filter(value_column >= start_of_day)
                        elif op == 'is_on_or_before':
                            subquery = subquery.filter(value_column <= end_of_day)
                        else:
                            continue

                elif attribute.value_type == 'time':
                    column_as_str = func.strftime('%H:%M:%S', value_column)
                    if op == 'is_within':
                        start_time_str = self._parse_time_filter_value(value[0]).strftime('%H:%M:%S')
                        end_time_str = self._parse_time_filter_value(value[1]).strftime('%H:%M:%S')
                        subquery = subquery.filter(and_(column_as_str >= start_time_str, column_as_str <= end_time_str))
                    else:
                        time_str_value = self._parse_time_filter_value(value).strftime('%H:%M:%S')
                        if op == 'is':
                            subquery = subquery.filter(column_as_str == time_str_value)
                        elif op == 'is_not':
                            subquery = subquery.filter(column_as_str != time_str_value)
                        elif op == 'is_after':
                            subquery = subquery.filter(column_as_str > time_str_value)
                        elif op == 'is_before':
                            subquery = subquery.filter(column_as_str < time_str_value)
                        elif op == 'is_on_or_after':
                            subquery = subquery.filter(column_as_str >= time_str_value)
                        elif op == 'is_on_or_before':
                            subquery = subquery.filter(column_as_str <= time_str_value)
                        else:
                            continue

                else:  # Для integer, float, boolean
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

                query = query.filter(subquery.exists())
        # 4. Применяем сортировку
        sort_func = desc if sort_order.lower() == 'desc' else asc

        if sort_by == 'position':
            # Сортировка по position всегда по возрастанию
            query = query.order_by(asc(models.Entity.position))
        elif sort_by == 'created_at':
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
        total_count = query.count()
        # 5. Применяем пагинацию
        total_count = query.count()

        entities_page = query.offset(skip).limit(limit).all()

        # 6. Если на странице ничего нет, возвращаем пустой список
        if not entities_page:
            return {"total": total_count, "data": []}

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

        # --- НОВАЯ ЛОГИКА "LOOK UP" ПЕРЕД ВОЗВРАТОМ ДАННЫХ ---
        # 9. Преобразуем EAV в "плоский" список словарей
        # --- НОВАЯ, ИСПРАВЛЕННАЯ ЛОГИКА ОТОБРАЖЕНИЯ СВЯЗЕЙ (ID-BASED) ---
        pivoted_results = [self._pivot_data(e) for e in sorted_entities]
        relation_attributes = [attr for attr in entity_type.attributes if attr.value_type == 'relation']

        if relation_attributes and pivoted_results:
            for rel_attr in relation_attributes:
                if not (rel_attr.target_entity_type_id and rel_attr.display_attribute):
                    continue

                display_attr_id = rel_attr.display_attribute.id
                source_ids = set()

                for row in pivoted_results:
                    cell_value = row.get(rel_attr.name)
                    if isinstance(cell_value, list):
                        source_ids.update(
                            item if isinstance(item, int) else item.get('id') for item in cell_value if item)
                    elif isinstance(cell_value, int):
                        source_ids.add(cell_value)

                if not source_ids:
                    continue

                display_values_query = self.db.query(
                    models.AttributeValue.entity_id,
                    models.AttributeValue.value_string,
                    models.AttributeValue.value_integer,
                    models.AttributeValue.value_float
                ).filter(
                    models.AttributeValue.entity_id.in_(source_ids),
                    models.AttributeValue.attribute_id == display_attr_id
                ).all()

                lookup_map = {
                    entity_id: str(val_str or val_int or val_float or '')
                    for entity_id, val_str, val_int, val_float in display_values_query
                }

                # --- НАЧАЛО ФИНАЛЬНОГО ИСПРАВЛЕНИЯ ---
                for row in pivoted_results:
                    cell_value = row.get(rel_attr.name)

                    if rel_attr.allow_multiple_selection:
                        # Для множественной связи, как и раньше, формируем массив объектов
                        if isinstance(cell_value, list):
                            row[rel_attr.name] = [
                                {"id": sid, "value": lookup_map.get(sid)}
                                for sid in cell_value if sid in lookup_map
                            ]
                        else:
                            row[rel_attr.name] = []  # Если не список, возвращаем пустой массив
                    else:
                        # Для одиночной связи ТЕПЕРЬ ТОЖЕ формируем массив, но с одним элементом
                        if isinstance(cell_value, int) and cell_value in lookup_map:
                            row[rel_attr.name] = [{"id": cell_value, "value": lookup_map.get(cell_value)}]
                        else:
                            row[rel_attr.name] = []  # Если ID нет или он не найден, возвращаем пустой массив
                # --- КОНЕЦ ФИНАЛЬНОГО ИСПРАВЛЕНИЯ ---

        return {"total": total_count, "data": pivoted_results}





    def update_attribute(
            self, attribute_id: int, attr_in: AttributeUpdate, current_user: models.User
    ) -> models.Attribute:
        db_attr = self.db.query(models.Attribute).get(attribute_id)
        if not db_attr or db_attr.entity_type.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Атрибут не найден")
        update_data = attr_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_attr, key, value)
        self.db.commit()
        return db_attr


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

    def create_attribute_for_type(
            self,
            entity_type_id: int,
            attribute_in: AttributeCreate,
            current_user: models.User
    ) -> models.Attribute:
        logger.info(f"--- [DEBUG] Начало create_attribute_for_type для таблицы ID: {entity_type_id} ---")
        logger.info(f"--- [DEBUG] Входящие данные: {attribute_in.model_dump_json(indent=2)}")

        source_entity_type_obj = self.get_entity_type_by_id(entity_type_id=entity_type_id, current_user=current_user)

        if attribute_in.value_type == 'relation':
            if not attribute_in.target_entity_type_id:
                raise HTTPException(status_code=400, detail="Необходимо указать 'target_entity_type_id'.")

            target_entity_type_obj = self.get_entity_type_by_id(entity_type_id=attribute_in.target_entity_type_id,
                                                                current_user=current_user)

            # 1. Определяем `display_attribute_id` для ПРЯМОЙ связи
            display_attr_id_for_main = attribute_in.display_attribute_id
            if not display_attr_id_for_main:
                logger.info(f"--- [DEBUG] ПРЯМАЯ СВЯЗЬ: display_attribute_id не передан, ищем автоматически.")
                primary_attr = self._find_primary_display_attribute(target_entity_type_obj.id)
                if not primary_attr:
                    raise HTTPException(status_code=400,
                                        detail=f"Не удалось найти главную колонку в '{target_entity_type_obj.display_name}'.")
                display_attr_id_for_main = primary_attr.id
                logger.info(
                    f"--- [DEBUG] ПРЯМАЯ СВЯЗЬ: display_attribute_id определен автоматически = {display_attr_id_for_main}")
            else:
                logger.info(f"--- [DEBUG] ПРЯМАЯ СВЯЗЬ: display_attribute_id передан явно = {display_attr_id_for_main}")

            main_attr_data = {
                "name": attribute_in.name, "display_name": attribute_in.display_name,
                "value_type": attribute_in.value_type.value, "entity_type_id": entity_type_id,
                "target_entity_type_id": target_entity_type_obj.id,
                "display_attribute_id": display_attr_id_for_main,
                "allow_multiple_selection": attribute_in.allow_multiple_selection
            }
            main_attr = models.Attribute(**main_attr_data)
            self.db.add(main_attr)

            # 2. Обрабатываем ОБРАТНУЮ связь
            if attribute_in.create_back_relation:

                base_back_name = attribute_in.back_relation_name or f"link_from_{source_entity_type_obj.name.lower()}"
                base_back_display_name = attribute_in.back_relation_display_name or f"Связь из '{source_entity_type_obj.display_name}'"

                final_back_name = base_back_name
                final_back_display_name = base_back_display_name
                counter = 1

                # Проверяем, существует ли уже колонка с таким системным именем в целевой таблице
                while self.db.query(models.Attribute).filter(
                        models.Attribute.entity_type_id == target_entity_type_obj.id,
                        models.Attribute.name == final_back_name
                ).first():
                    # Если имя занято, добавляем суффикс
                    final_back_name = f"{base_back_name}_{counter}"
                    final_back_display_name = f"{base_back_display_name} ({counter})"
                    counter += 1

                logger.info(f"--- [DEBUG] ОБРАТНАЯ СВЯЗЬ: Финальное системное имя = {final_back_name}")

                back_display_attr_id = attribute_in.back_relation_display_attribute_id

                if not back_display_attr_id:
                    logger.info(
                        f"--- [DEBUG] ОБРАТНАЯ СВЯЗЬ: back_relation_display_attribute_id не передан, ищем автоматически.")
                    primary_attr_for_back_relation = self._find_primary_display_attribute(source_entity_type_obj.id)
                    if not primary_attr_for_back_relation:
                        raise HTTPException(status_code=400,
                                            detail=f"Не удалось найти главную колонку в исходной таблице '{source_entity_type_obj.display_name}' для создания обратной связи.")
                    back_display_attr_id = primary_attr_for_back_relation.id
                    logger.info(
                        f"--- [DEBUG] ОБРАТНАЯ СВЯЗЬ: back_relation_display_attribute_id определен автоматически = {back_display_attr_id}")
                else:
                    logger.info(
                        f"--- [DEBUG] ОБРАТНАЯ СВЯЗЬ: back_relation_display_attribute_id передан явно = {back_display_attr_id}")


                back_relation_attr_data = {
                    "name": final_back_name,
                    "display_name": final_back_display_name,
                    "value_type": "relation",
                    "entity_type_id": target_entity_type_obj.id,
                    "target_entity_type_id": source_entity_type_obj.id,
                    "display_attribute_id": back_display_attr_id,
                    "allow_multiple_selection": attribute_in.allow_multiple_selection
                }
                back_relation_attr = models.Attribute(**back_relation_attr_data)
                self.db.add(back_relation_attr)
                self.db.flush()

                main_attr.reciprocal_attribute_id = back_relation_attr.id
                back_relation_attr.reciprocal_attribute_id = main_attr.id

            self.db.commit()
            self.db.refresh(main_attr)
            return main_attr

        # --- СЦЕНАРИЙ 2: Создание любой другой обычной колонки ---
        else:
            attr_data_for_db = {
                "name": attribute_in.name,
                "display_name": attribute_in.display_name,
                "value_type": attribute_in.value_type.value,
                "entity_type_id": entity_type_id
            }
            if attribute_in.formula_text is not None:
                attr_data_for_db["formula_text"] = attribute_in.formula_text
            if attribute_in.currency_symbol is not None:
                attr_data_for_db["currency_symbol"] = attribute_in.currency_symbol
            if attribute_in.value_type == 'select' and attribute_in.list_items:
                unique_name = f"Список для '{attribute_in.display_name}' ({int(time.time())})"
                new_list = models.SelectOptionList(name=unique_name, tenant_id=current_user.tenant_id)
                self.db.add(new_list)
                for item_value in attribute_in.list_items:
                    if item_value:
                        self.db.add(models.SelectOption(value=item_value, option_list=new_list))
                self.db.flush()
                attr_data_for_db['select_list_id'] = new_list.id
            db_attribute = models.Attribute(**attr_data_for_db)
            self.db.add(db_attribute)
            self.db.commit()
            # --- НАЧАЛО ИЗМЕНЕНИЯ: Автоматическое заполнение значения по умолчанию для чекбоксов ---
            if db_attribute.value_type == 'boolean':
                logger.info(f"Создана новая колонка типа 'boolean' (ID: {db_attribute.id}). Запускаем заполнение по умолчанию (False)...")

                # 1. Находим все ID существующих строк в этой таблице.
                entity_ids_in_table = [
                    id for (id,) in self.db.query(models.Entity.id).filter(
                        models.Entity.entity_type_id == entity_type_id
                    )
                ]

                if entity_ids_in_table:
                    # 2. Находим строки, у которых УЖЕ есть значение для этой новой колонки (защита от дублей).
                    entities_with_value = [
                        id for (id,) in self.db.query(models.AttributeValue.entity_id).filter(
                            models.AttributeValue.attribute_id == db_attribute.id,
                            models.AttributeValue.entity_id.in_(entity_ids_in_table)
                        )
                    ]

                    # 3. Вычисляем ID строк, которым нужно добавить значение по умолчанию.
                    entities_to_update_ids = list(set(entity_ids_in_table) - set(entities_with_value))

                    # 4. Готовим новые объекты AttributeValue для массовой вставки.
                    new_values = [
                        models.AttributeValue(
                            entity_id=entity_id,
                            attribute_id=db_attribute.id,
                            value_boolean=False  # Значение по умолчанию
                        )
                        for entity_id in entities_to_update_ids
                    ]

                    # 5. Если есть что добавлять, делаем это одной транзакцией.
                    if new_values:
                        self.db.bulk_save_objects(new_values)
                        self.db.commit()
                        logger.info(f"Успешно заполнено {len(new_values)} строк значением 'False' для колонки ID {db_attribute.id}.")
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---

            self.db.refresh(db_attribute)
            return db_attribute

    def get_entity_by_id(self, entity_id: int, current_user: models.User) -> Dict[str, Any]:
        entity = self.db.query(models.Entity).options(
            joinedload(models.Entity.values).joinedload(models.AttributeValue.attribute),
            joinedload(models.Entity.values).joinedload(models.AttributeValue.many_to_many_links),  # <-- Добавлено
            joinedload(models.Entity.entity_type).joinedload(models.EntityType.attributes).joinedload(
                models.Attribute.display_attribute)
        ).filter(models.Entity.id == entity_id).first()

        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")
        if not current_user.is_superuser and entity.entity_type.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        pivoted_result = self._pivot_data(entity)

        relation_attributes = [attr for attr in entity.entity_type.attributes if attr.value_type == 'relation']
        if relation_attributes:
            for rel_attr in relation_attributes:
                if not (rel_attr.target_entity_type_id and rel_attr.display_attribute):
                    continue

                display_attr_id = rel_attr.display_attribute.id

                source_ids = set()
                cell_value = pivoted_result.get(rel_attr.name)
                if isinstance(cell_value, list):
                    source_ids.update(item if isinstance(item, int) else item.get('id') for item in cell_value if item)
                elif isinstance(cell_value, int):
                    source_ids.add(cell_value)

                if not source_ids:
                    if rel_attr.name in pivoted_result:
                        pivoted_result[rel_attr.name] = []
                    continue

                display_values_query = self.db.query(
                    models.AttributeValue.entity_id,
                    models.AttributeValue.value_string,
                    models.AttributeValue.value_integer,
                    models.AttributeValue.value_float
                ).filter(
                    models.AttributeValue.entity_id.in_(source_ids),
                    models.AttributeValue.attribute_id == display_attr_id
                ).all()

                lookup_map = {
                    entity_id: str(val_str or val_int or val_float or '')
                    for entity_id, val_str, val_int, val_float in display_values_query
                }

                # --- ПРИМЕНЯЕМ ТУ ЖЕ САМУЮ ЛОГИКУ УНИФИКАЦИИ ---
                if rel_attr.allow_multiple_selection:
                    if isinstance(cell_value, list):
                        pivoted_result[rel_attr.name] = [
                            {"id": sid, "value": lookup_map.get(sid)}
                            for sid in cell_value if sid in lookup_map
                        ]
                    else:
                        pivoted_result[rel_attr.name] = []
                else:
                    if isinstance(cell_value, int) and cell_value in lookup_map:
                        pivoted_result[rel_attr.name] = [{"id": cell_value, "value": lookup_map.get(cell_value)}]
                    else:
                        pivoted_result[rel_attr.name] = []
                # --- КОНЕЦ ЛОГИКИ УНИФИКАЦИИ ---

        return pivoted_result

    def update_entity(self, entity_id: int, data: Dict[str, Any], current_user: models.User) -> Dict[str, Any]:
        from tasks.messaging import send_webhook_task, send_sms_for_entity_task
        logger.info(f"--- Начало update_entity для ID: {entity_id} ---")
        logger.debug(f"Входящие данные (data): {data}")

        is_external_update = data.pop("_source", None) is not None

        entity = self.db.query(models.Entity).options(
            joinedload(models.Entity.entity_type).joinedload(models.EntityType.attributes)
        ).get(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail="Сущность не найдена")
        if not current_user.is_superuser and entity.entity_type.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        attributes_map = {attr.name: attr for attr in entity.entity_type.attributes}

        if 'modification_date' in attributes_map:
            data['modification_date'] = datetime.utcnow().isoformat()

        if data.get("send_sms_trigger"):
            data["sms_status"] = "pending"
            data["send_sms_trigger"] = False
            send_sms_for_entity_task.delay(entity_id=entity_id, user_id=current_user.id)

        for key, value in data.items():
            if key not in attributes_map:
                continue

            attribute = attributes_map[key]

            is_relation_operation = (
                    attribute.value_type == 'relation' or
                    (attribute.value_type == 'integer' and isinstance(value, list))
            )

            if is_relation_operation:
                existing_value_container = self.db.query(models.AttributeValue).options(
                    joinedload(models.AttributeValue.many_to_many_links)
                ).filter_by(entity_id=entity_id, attribute_id=attribute.id).first()

                if not existing_value_container:
                    existing_value_container = models.AttributeValue(entity_id=entity_id, attribute_id=attribute.id)
                    self.db.add(existing_value_container)

                if attribute.allow_multiple_selection:
                    old_linked_ids = {link.id for link in existing_value_container.many_to_many_links}
                    existing_value_container.value_integer = None

                    new_linked_ids = set()
                    if isinstance(value, list):
                        new_linked_ids = set(
                            filter(None, [item.get('id') if isinstance(item, dict) else item for item in value]))
                        if new_linked_ids:
                            linked_entities = self.db.query(models.Entity).filter(
                                models.Entity.id.in_(new_linked_ids)).all()
                            existing_value_container.many_to_many_links = linked_entities
                        else:
                            existing_value_container.many_to_many_links = []
                    else:
                        existing_value_container.many_to_many_links.clear()

                    if attribute.reciprocal_attribute_id:
                        reciprocal_attr_id = attribute.reciprocal_attribute_id
                        ids_to_add = new_linked_ids - old_linked_ids
                        ids_to_remove = old_linked_ids - new_linked_ids

                        for target_id in ids_to_remove:
                            reciprocal_container = self.db.query(models.AttributeValue).filter_by(entity_id=target_id,
                                                                                                  attribute_id=reciprocal_attr_id).first()
                            if reciprocal_container:
                                target_entity_to_remove = self.db.query(models.Entity).get(entity_id)
                                if target_entity_to_remove in reciprocal_container.many_to_many_links:
                                    reciprocal_container.many_to_many_links.remove(target_entity_to_remove)

                        for target_id in ids_to_add:
                            reciprocal_container = self.db.query(models.AttributeValue).filter_by(entity_id=target_id,
                                                                                                  attribute_id=reciprocal_attr_id).first()
                            if not reciprocal_container:
                                reciprocal_container = models.AttributeValue(entity_id=target_id,
                                                                             attribute_id=reciprocal_attr_id)
                                self.db.add(reciprocal_container)
                            target_entity_to_add = self.db.query(models.Entity).get(entity_id)
                            if target_entity_to_add not in reciprocal_container.many_to_many_links:
                                reciprocal_container.many_to_many_links.append(target_entity_to_add)

                else:
                    old_linked_id = existing_value_container.value_integer
                    existing_value_container.many_to_many_links.clear()

                    if isinstance(value, dict) and 'id' in value:
                        new_linked_id_raw = value.get('id')
                    elif isinstance(value, list) and len(value) > 0:
                        new_linked_id_raw = value[0]
                    elif isinstance(value, list) and len(value) == 0:
                        new_linked_id_raw = None
                    else:
                        new_linked_id_raw = value

                    new_linked_id = self._process_value(new_linked_id_raw, attribute)

                    existing_value_container.value_integer = new_linked_id

                    if attribute.reciprocal_attribute_id and old_linked_id != new_linked_id:
                        reciprocal_attr_id = attribute.reciprocal_attribute_id

                        if old_linked_id and isinstance(old_linked_id, int):
                            reciprocal_value_to_remove = self.db.query(models.AttributeValue).filter_by(
                                entity_id=old_linked_id, attribute_id=reciprocal_attr_id).first()
                            if reciprocal_value_to_remove:
                                reciprocal_value_to_remove.value_integer = None

                        if new_linked_id and isinstance(new_linked_id, int):
                            reciprocal_value_to_add = self.db.query(models.AttributeValue).filter_by(
                                entity_id=new_linked_id, attribute_id=reciprocal_attr_id).first()
                            if not reciprocal_value_to_add:
                                reciprocal_value_to_add = models.AttributeValue(entity_id=new_linked_id,
                                                                                attribute_id=reciprocal_attr_id)
                                self.db.add(reciprocal_value_to_add)
                            reciprocal_value_to_add.value_integer = entity_id
            # --- Сценарий 2: Обработка Multiselect (без изменений) ---
            elif attribute.value_type == 'multiselect':
                existing_value_container = self.db.query(models.AttributeValue).options(
                    joinedload(models.AttributeValue.multiselect_values)
                ).filter_by(entity_id=entity_id, attribute_id=attribute.id).first()
                if not isinstance(value, list) or not value:
                    if existing_value_container:
                        existing_value_container.multiselect_values.clear()
                    continue
                if not existing_value_container:
                    existing_value_container = models.AttributeValue(entity_id=entity_id, attribute_id=attribute.id)
                    self.db.add(existing_value_container)

                # Извлекаем ID из списка словарей или просто чисел
                option_ids = [item.get('id') if isinstance(item, dict) else item for item in value]
                options = self.db.query(models.SelectOption).filter(models.SelectOption.id.in_(option_ids)).all()
                existing_value_container.multiselect_values = options

            # --- Сценарий 3: Обработка всех остальных типов полей ---
            elif attribute.value_type in VALUE_FIELD_MAP:
                processed_value = self._process_value(value, attribute)
                value_field_name = VALUE_FIELD_MAP[attribute.value_type]
                existing_value = self.db.query(models.AttributeValue).filter_by(
                    entity_id=entity_id, attribute_id=attribute.id
                ).first()

                if existing_value:
                    if processed_value is None:
                        self.db.delete(existing_value)
                    else:
                        for field in VALUE_FIELD_MAP.values():
                            setattr(existing_value, field, None)
                        setattr(existing_value, value_field_name, processed_value)
                elif processed_value is not None:
                    new_value = models.AttributeValue(entity_id=entity_id, attribute_id=attribute.id,
                                                      **{value_field_name: processed_value})
                    self.db.add(new_value)

        # 4. Сохраняем все изменения и отправляем уведомления
        entity.updated_at = datetime.utcnow()
        self.db.commit()

        # # --- ЗАПУСК ТРИГГЕРА ОБОГАЩЕНИЯ ---
        # # Запускаем, только если поле 'inn' было в запросе на обновление и оно не пустое
        # if 'inn' in data and data['inn']:
        #     from tasks.enrichment import enrich_data_by_inn_task  # <-- И СЮДА ТОЖЕ
        #     enrich_data_by_inn_task.delay(
        #         entity_id=entity_id,
        #         inn=str(data['inn']),
        #         user_id=current_user.id
        #     )
        # # --- КОНЕЦ ТРИГГЕРА ---



        if not is_external_update:
            send_webhook_task.delay(
                event_type="update",
                table_name=entity.entity_type.name,
                entity_id=entity_id,
                data=data,
                tenant_id=current_user.tenant_id
            )

        logger.info(f"--- Завершение update_entity для ID: {entity_id} ---")
        return self.get_entity_by_id(entity_id, current_user)






    # --- ИМПОРТ ЗАДАЧИ ВНУТРИ МЕТОДА ---

    def _process_value(self, value, attribute: models.Attribute):
        """Вспомогательная функция для обработки и конвертации значений."""
        # 1. Сразу отсекаем None
        value_type = attribute.value_type # Получаем тип из атрибута

        if value is None or (isinstance(value, str) and value.strip() == ''):
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
                from datetime import time
                return time.fromisoformat(value)
            if value_type == 'integer' and not isinstance(value, int):
                return int(value)
            if value_type == 'float' and not isinstance(value, float):
                return float(value)
            # --- НОВАЯ ЛОГИКА ВАЛИДАЦИИ ---
            if value_type == 'email':
                # Проверяем, что это валидный email. Если нет, email_validator выбросит исключение.
                validate_email(value, check_deliverability=False)  # check_deliverability=False для скорости
                return value  # Возвращаем исходную строку, если она валидна
            # --- НАЧАЛО ИСПРАВЛЕНИЯ ---
            if value_type == 'boolean':
                # Если уже пришел boolean, просто возвращаем его
                if isinstance(value, bool):
                    return value
                # Если пришла строка, пытаемся ее распознать
                if isinstance(value, str):
                    val_lower = value.lower().strip()
                    if val_lower in ('true', 'yes', '1', 'да', 'on'):
                        return True
                    if val_lower in ('false', 'no', '0', 'нет', 'off'):
                        return False
                # Если пришло число 1 или 0
                if isinstance(value, int) and value in (0, 1):
                    return bool(value)

                # Если не смогли распознать, считаем значение некорректным/пустым
                return None
            # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
            if value_type == 'phone':
                # Здесь может быть более сложная валидация, но пока просто оставляем как есть.
                # Можно использовать, например, библиотеку phonenumbers.
                return value

            if value_type == 'url':
                # Проверяем, что это валидный URL. Если нет, validators.url вернет False.
                if not validators.url(value):
                    raise ValueError("Некорректный URL")
                return value

            # Для аудио мы просто проверяем, что это строка (путь к файлу)
            if value_type == 'audio':
                if isinstance(value, str) and value.startswith('/static/uploads/audio/'):
                    return value
                return None  # Если пришло что-то другое, считаем значение некорректным
            # -----------------------------

            # --- НОВАЯ ЛОГИКА ДЛЯ SELECT ---
            if value_type == 'select':
                if not attribute.select_list_id:
                    raise HTTPException(status_code=500,
                                        detail=f"Для колонки '{attribute.name}' не настроен справочник (select_list_id)")

                # Загружаем все допустимые опции для этого списка
                valid_options = self.db.query(models.SelectOption.value).filter(
                    models.SelectOption.option_list_id == attribute.select_list_id
                ).all()
                # Превращаем список кортежей [('Новая',), ('В работе',)] в простой set {'Новая', 'В работе'}
                valid_options_set = {opt[0] for opt in valid_options}

                # Проверяем, есть ли пришедшее значение в списке разрешенных
                if value not in valid_options_set:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Недопустимое значение '{value}' для поля '{attribute.name}'. Разрешенные значения: {list(valid_options_set)}"
                    )

                # Если все в порядке, возвращаем саму строку
                return value





        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Некорректное значение для поля типа '{value_type}': {value}"
            )

        return value






    def create_entity(self, entity_type_name: str, data: Dict[str, Any], current_user: models.User) -> Dict[str, Any]:
        from tasks.messaging import send_webhook_task

        # --- ПРОВЕРКА ФЛАГА ---
        # Извлекаем флаг из данных. `pop` удаляет его, чтобы он не записался в атрибуты.
        is_external_update = data.pop("_source", None) is not None
        # ---------------------
        """Создать новую запись с корректным преобразованием типов."""
        entity_type = self._get_entity_type_by_name(entity_type_name, current_user)
        attributes_map = {attr.name: attr for attr in entity_type.attributes}

        # --- ДОБАВЬТЕ ЭТУ СТРОКУ ПЕРЕД СОЗДАНИЕМ ЗАПИСИ ---
        # Внедряем текущую дату, если колонка "Дата создания" существует
        if 'creation_date' in attributes_map:
            data['creation_date'] = datetime.utcnow().isoformat()

        # --- ИЗМЕНЕННАЯ ЛОГИКА ОПРЕДЕЛЕНИЯ ПОЗИЦИИ ---
        # 1. Находим минимальную (самую верхнюю) позицию в этой таблице.
        min_pos_result = self.db.query(func.min(models.Entity.position)).filter(
            models.Entity.entity_type_id == entity_type.id
        ).scalar()

        # 2. Вычисляем новую позицию.
        # Если в таблице уже есть записи, новая будет на одну позицию "выше" (меньше).
        # Если таблица пуста, позиция будет 0.
        new_position = (min_pos_result - 1.0) if min_pos_result is not None else 0.0
        # -----------------------------------------------

        new_entity = models.Entity(entity_type_id=entity_type.id, position=new_position)
        self.db.add(new_entity)
        self.db.flush()

        for key, value in data.items():
            if key not in attributes_map:
                continue

            attribute = attributes_map[key]

            if attribute.value_type == 'relation':
                attr_value = models.AttributeValue(entity_id=new_entity.id, attribute_id=attribute.id)
                self.db.add(attr_value)

                if attribute.allow_multiple_selection:
                    # Множественная связь: value - это список ID
                    if isinstance(value, list) and value:
                        linked_entities = self.db.query(models.Entity).filter(models.Entity.id.in_(value)).all()
                        attr_value.many_to_many_links.extend(linked_entities)
                else:
                    # Одиночная связь: value - это один ID
                    processed_value = self._process_value(value, attribute)
                    if processed_value is not None:
                        attr_value.value_integer = processed_value


            # --- ИЗМЕНЕННАЯ ЛОГИКА ---
            elif attribute.value_type == 'multiselect':
                # Создаем "пустой" AttributeValue, который будет контейнером
                attr_value = models.AttributeValue(entity_id=new_entity.id, attribute_id=attribute.id)
                if isinstance(value, list) and value:
                    # Находим объекты SelectOption по списку ID
                    options = self.db.query(models.SelectOption).filter(models.SelectOption.id.in_(value)).all()
                    attr_value.multiselect_values.extend(options)
                self.db.add(attr_value)

            elif attribute.value_type in VALUE_FIELD_MAP:
                # Старая логика для всех остальных типов
                processed_value = self._process_value(value, attribute)  # Передаем весь `attribute`
                if processed_value is None:
                    continue

                value_field_name = VALUE_FIELD_MAP[attribute.value_type]
                attr_value = models.AttributeValue(
                    entity_id=new_entity.id,
                    attribute_id=attribute.id
                )
                setattr(attr_value, value_field_name, processed_value)
                self.db.add(attr_value)
            # ---------------------------

        self.db.commit()

        # # --- ЗАПУСК ТРИГГЕРА ОБОГАЩЕНИЯ ---
        # if 'inn' in data and data['inn']:
        #     from tasks.enrichment import enrich_data_by_inn_task  # <-- ПЕРЕНЕСИТЕ ИМПОРТ СЮДА
        #     enrich_data_by_inn_task.delay(
        #         entity_id=new_entity.id,
        #         inn=str(data['inn']),
        #         user_id=current_user.id
        #     )
        # # --- КОНЕЦ ТРИГГЕРА ---


        # --- ЛОГИКА ОТПРАВКИ УВЕДОМЛЕНИЯ ---
        if not is_external_update:
            # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
            # Добавляем `tenant_id=current_user.tenant_id`
            send_webhook_task.delay(
                event_type="create",
                table_name=entity_type_name,
                entity_id=new_entity.id,
                data=data,
                tenant_id=current_user.tenant_id
            )
        # -----------------------------------
        return self.get_entity_by_id(new_entity.id, current_user)







    def delete_entity(self, entity_id: int, current_user: models.User, source: Optional[str] = None):
        from tasks.messaging import send_webhook_task  # <--- ИМПОРТ ВНУТРИ ФУНКЦИИ

        """Удалить запись."""
        is_external_update = source is not None

        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # 1. Сначала загружаем SQLAlchemy объект Entity вместе с его EntityType
        entity_to_delete = self.db.query(models.Entity).options(
            joinedload(models.Entity.entity_type)
        ).get(entity_id)

        # 2. Проверяем, существует ли запись
        if not entity_to_delete:
            raise HTTPException(status_code=404, detail="Сущность не найдена")

        # 3. Проверяем права доступа
        if not current_user.is_superuser:
            # Проверяем, принадлежит ли запись тенанту пользователя,
            # ИЛИ есть ли у него права на эту "общую" таблицу
            is_own_entity = (entity_to_delete.entity_type.tenant_id == current_user.tenant_id)
            if not is_own_entity:
                user_permissions = {perm.name for role in current_user.roles for perm in role.permissions}
                table_name = entity_to_delete.entity_type.name
                has_access = any(p == f"data:delete:{table_name}" for p in user_permissions)

                if not has_access:
                    raise HTTPException(status_code=404,
                                        detail="Сущность не найдена или недостаточно прав для удаления")

        # 4. Если все проверки пройдены, удаляем
        entity_type_name = entity_to_delete.entity_type.name
        tenant_id_for_webhook = entity_to_delete.entity_type.tenant_id
        self.db.delete(entity_to_delete)
        self.db.commit()
        # ---------------------------

        if not is_external_update:
            send_webhook_task.delay(
                event_type="delete",
                table_name=entity_type_name,
                entity_id=entity_id,
                data={"id": entity_id},
                tenant_id=tenant_id_for_webhook
            )

        return None

    def delete_attribute_from_type(self, entity_type_id: int, attribute_id: int, current_user: models.User):
        """
        Удалить атрибут ('колонку') из типа сущности.
        Если у атрибута есть "зеркальная" пара (reciprocal_attribute), удаляет и ее тоже.
        """
        # 1. Проверяем доступ к родительской таблице
        self.get_entity_type_by_id(entity_type_id=entity_type_id, current_user=current_user)

        # 2. Находим сам атрибут, который нужно удалить, "жадно" загружая его зеркальную пару
        attribute_to_delete = self.db.query(models.Attribute).options(
            joinedload(models.Attribute.reciprocal_attribute)
        ).filter(
            models.Attribute.id == attribute_id,
            models.Attribute.entity_type_id == entity_type_id
        ).first()

        if not attribute_to_delete:
            raise HTTPException(
                status_code=404,
                detail=f"Атрибут с ID {attribute_id} не найден в типе сущности {entity_type_id}"
            )

        # 3. Проверяем, не является ли атрибут системным
        system_attributes = [
            "send_sms_trigger", "sms_status", "sms_last_error",
            "phone_number", "message_text", "creation_date", "modification_date"
        ]
        if attribute_to_delete.name in system_attributes:
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя удалить системный атрибут '{attribute_to_delete.name}'"
            )

        # --- НАЧАЛО НОВОЙ ЛОГИКИ ---

        # 4. Проверяем, есть ли у этого атрибута зеркальная пара
        reciprocal_attr = attribute_to_delete.reciprocal_attribute
        if reciprocal_attr:
            logger.info(
                f"Обнаружена зеркальная колонка '{reciprocal_attr.name}' (ID: {reciprocal_attr.id}). Разрываем цикл.")
            # Обнуляем ссылки друг на друга
            attribute_to_delete.reciprocal_attribute_id = None
            reciprocal_attr.reciprocal_attribute_id = None
            # Коммитим эти изменения в отдельной транзакции
            self.db.commit()

            # Перезагружаем объекты из сессии, чтобы SQLAlchemy "увидел" изменения
            self.db.refresh(attribute_to_delete)
            self.db.refresh(reciprocal_attr)

            # 5. ШАГ ВТОРОЙ: ТЕПЕРЬ БЕЗОПАСНО УДАЛЯЕМ
            # Сначала удаляем основной атрибут
        self.db.delete(attribute_to_delete)
        logger.info(f"Удаляется основная колонка '{attribute_to_delete.name}' (ID: {attribute_to_delete.id})")

        # Затем удаляем "зеркальный" атрибут, если он был
        if reciprocal_attr:
            self.db.delete(reciprocal_attr)
            logger.info(f"Удаляется зеркальная колонка '{reciprocal_attr.name}' (ID: {reciprocal_attr.id})")

        # Коммитим удаление
        self.db.commit()
        return None
    # def delete_attribute_from_type(self, entity_type_id: int, attribute_id: int, current_user: models.User):
    #     """
    #     Удалить атрибут ('колонку') из типа сущности и все его значения.
    #     """
    #     # 1. Сначала проверяем, что сам тип сущности (таблица) существует
    #     # и принадлежит текущему пользователю. Это защищает от попытки удалить
    #     # колонку из чужой таблицы.
    #     self.get_entity_type_by_id(entity_type_id=entity_type_id, current_user=current_user)
    #
    #     # 2. Находим сам атрибут, который нужно удалить.
    #     # Дополнительно проверяем, что он действительно принадлежит указанному типу сущности.
    #     attribute_to_delete = self.db.query(models.Attribute).filter(
    #         models.Attribute.id == attribute_id,
    #         models.Attribute.entity_type_id == entity_type_id
    #     ).first()
    #
    #     # 3. Если атрибут не найден, возвращаем ошибку.
    #     if not attribute_to_delete:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail=f"Атрибут с ID {attribute_id} не найден в типе сущности {entity_type_id}"
    #         )
    #
    #     # 4. Проверяем, не является ли атрибут системным. Системные удалять нельзя.
    #     system_attributes = [
    #         "send_sms_trigger", "sms_status", "sms_last_error",
    #         "phone_number", "message_text"
    #     ]
    #     if attribute_to_delete.name in system_attributes:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"Нельзя удалить системный атрибут '{attribute_to_delete.name}'"
    #         )
    #
    #     # 5. Удаляем объект. Благодаря ondelete="CASCADE", все связанные AttributeValue
    #     # будут удалены автоматически на уровне базы данных.
    #     self.db.delete(attribute_to_delete)
    #     self.db.commit()
    #
    #     return None





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


    def create_entity_and_get_list(
            self,
            entity_type_name: str,
            data: Dict[str, Any],
            current_user: models.User
    ) -> List[Dict[str, Any]]:
        """
        Создает сущность (включая отправку уведомления), а затем
        возвращает полный отсортированный список.
        """
        # 1. Просто создаем новую запись. Метод `create_entity` уже умеет
        # отправлять уведомления, поэтому здесь это делать не нужно.
        self.create_entity(entity_type_name, data, current_user)

        # 2. Теперь, после коммита, запрашиваем полный список
        full_sorted_list = self.get_all_entities_for_type(
            entity_type_name=entity_type_name,
            current_user=current_user
        )

        return full_sorted_list



    def delete_multiple_entities(
            self,
            entity_type_name: str,
            ids: List[int],
            current_user: models.User,
            source: Optional[str] = None
    ) -> int:
        """
        Удаляет несколько записей (сущностей) по списку их ID.
        Возвращает количество удаленных записей.
        """
        is_external_update = source is not None
        entity_type = self._get_entity_type_by_name(entity_type_name, current_user)

        """Удаляет несколько записей."""
        # 1. Строим запрос на ВЫБОРКУ объектов, которые нужно удалить
        query = self.db.query(models.Entity).filter(
            models.Entity.entity_type_id == entity_type.id,
            models.Entity.id.in_(ids)
        )

        if not current_user.is_superuser:
            query = query.filter(models.Entity.entity_type.has(tenant_id=current_user.tenant_id))

        # 2. Получаем эти объекты из базы
        entities_to_delete = query.all()

        if not entities_to_delete:
            return 0

        # 3. Удаляем каждый объект через сессию, что активирует cascade="all, delete-orphan"
        for entity in entities_to_delete:
            self.db.delete(entity)

        num_deleted = len(entities_to_delete)

        # 4. Коммитим транзакцию
        self.db.commit()

        if not is_external_update and num_deleted > 0:
            external_api_client.send_update_to_colleague(
                event_type="bulk_delete",  # <-- Тип события 'bulk_delete'
                table_name=entity_type_name,  # <-- Имя таблицы у нас уже есть
                entity_id=None,  # <-- ID одной записи не актуален
                data={"ids": ids}  # <-- В `data` передаем список удаленных ID
            )
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

    def set_entity_order(
            self,
            entity_type_name: str,
            entity_ids: List[int],
            current_user: models.User
    ):
        """Сохраняет новый порядок строк для таблицы."""
        # Проверяем доступ к таблице
        entity_type = self._get_entity_type_by_name(entity_type_name, current_user)

        # Используем "bulk update", чтобы обновить все записи одним запросом.
        # Это очень эффективно.
        update_mappings = [
            {"id": entity_id, "position": position}
            for position, entity_id in enumerate(entity_ids)
        ]

        if update_mappings:
            self.db.bulk_update_mappings(models.Entity, update_mappings)
            self.db.commit()

        return {"status": "ok", "ordered_ids": entity_ids}

    def update_entity_position(
            self,
            entity_type_name: str,
            entity_id: int,
            after_pos: Optional[float],
            before_pos: Optional[float],
            current_user: models.User
    ):
        """Обновляет позицию одной строки на основе ее новых соседей."""
        entity_type = self._get_entity_type_by_name(entity_type_name, current_user)

        # Находим запись, которую переместили
        entity_to_move = self.db.query(models.Entity).filter(
            models.Entity.id == entity_id,
            models.Entity.entity_type_id == entity_type.id
        ).first()

        if not entity_to_move:
            raise HTTPException(status_code=404, detail="Перемещаемая запись не найдена")

        new_position = 0.0

        if after_pos is not None and before_pos is not None:
            # Случай 1: Вставили между двумя строками
            new_position = (after_pos + before_pos) / 2.0
        elif after_pos is not None:
            # Случай 2: Вставили после последней строки
            new_position = after_pos + 1.0
        elif before_pos is not None:
            # Случай 3: Вставили перед первой строкой
            new_position = before_pos / 2.0
        else:
            # Случай 4: Вставили в пустую таблицу (маловероятно)
            new_position = time.time()

        entity_to_move.position = new_position
        self.db.commit()

        return {"id": entity_id, "new_position": new_position}




    def _calculate_formula(self, formula_text: str, row_data: Dict[str, Any]) -> Optional[float]:
        """
        Безопасно вычисляет значение формулы для одной строки данных.
        Поддерживает только числа и базовые операторы: +, -, *, /.
        """
        try:
            # 1. Находим все {переменные} в тексте формулы
            variables = re.findall(r'\{([a-zA-Z0-9_]+)\}', formula_text)

            expression = formula_text

            # 2. Подставляем реальные значения из строки
            for var in variables:
                value = row_data.get(var)
                # Если в строке нет такого значения или оно не число, вычисление невозможно
                if not isinstance(value, (int, float)):
                    return None
                expression = expression.replace(f'{{{var}}}', str(value))

            # 3. Безопасное вычисление: проверяем, что в выражении нет ничего лишнего
            # Этот whitelist - наша главная защита от `eval()`
            allowed_chars = "0123456789.+-*/() "
            if not all(char in allowed_chars for char in expression):
                # Если есть что-то кроме цифр и операторов - не вычисляем
                return None

            # 4. Вычисляем
            # Используем eval(), но только после строгой проверки на разрешенные символы
            result = eval(expression)
            return float(result)

        except (TypeError, ZeroDivisionError, Exception):
            # В случае любой ошибки (деление на ноль, синтаксическая ошибка)
            # просто возвращаем None
            return None
    # ------------------------------------

    def _find_primary_display_attribute(self, entity_type_id: int) -> Optional[models.Attribute]:
        """
        Находит "главную" отображаемую колонку в таблице.
        ИГНОРИРУЕТ системные колонки.
        """
        logger.info(f"--- [DEBUG] Запущен поиск главной колонки для таблицы ID: {entity_type_id} ---")

        # --- НАЧАЛО ИЗМЕНЕНИЙ ---

        SYSTEM_ATTRIBUTE_NAMES = {
            "send_sms_trigger", "sms_status", "sms_last_error",
            "phone_number", "message_text", "creation_date", "modification_date"
        }

        # Загружаем все атрибуты, КРОМЕ системных
        attributes = self.db.query(models.Attribute).filter(
            models.Attribute.entity_type_id == entity_type_id,
            ~models.Attribute.name.in_(SYSTEM_ATTRIBUTE_NAMES)  # Знак ~ означает NOT IN
        ).order_by(models.Attribute.id).all()

        # --- КОНЕЦ ИЗМЕНЕНИЙ ---

        if not attributes:
            logger.warning(
                f"--- [DEBUG] Для таблицы ID: {entity_type_id} не найдено ни одной ПОЛЬЗОВАТЕЛЬСКОЙ колонки.")
            # Если пользовательских нет, попробуем найти хоть что-то среди всех
            all_attributes = self.db.query(models.Attribute).filter_by(entity_type_id=entity_type_id).order_by(
                models.Attribute.id).all()
            return all_attributes[0] if all_attributes else None

        # Ищем по приоритетным именам (этот код без изменений)
        for name in ['name', 'title', 'display_name', 'company_name', 'full_name', 'contact_name', 'project_name']:
            for attr in attributes:
                if attr.name == name:
                    logger.info(f"--- [DEBUG] Найдена колонка по приоритетному имени '{name}' (ID: {attr.id})")
                    return attr

        # Ищем первую строковую
        for attr in attributes:
            if attr.value_type == 'string':
                logger.info(f"--- [DEBUG] Найдена первая строковая колонка '{attr.name}' (ID: {attr.id})")
                return attr

        # Возвращаем первую попавшуюся пользовательскую колонку
        first_attr = attributes[0]
        logger.info(
            f"--- [DEBUG] Возвращаем самую первую пользовательскую колонку '{first_attr.name}' (ID: {first_attr.id})")
        return first_attr
