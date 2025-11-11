# services/calendar_service.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
import json
from datetime import date, datetime

from db import models, session
from schemas.calendar import CalendarViewConfigCreate, CalendarViewConfigUpdate
from services.eav_service import EAVService


class CalendarService:
    def __init__(self, db: Session = Depends(session.get_db), eav_service: EAVService = Depends()):
        self.db = db
        self.eav_service = eav_service

    # --- CRUD для конфигураций (этот код у вас уже есть и работает) ---

    def create_config(self, config_in: CalendarViewConfigCreate,
                      current_user: models.User) -> models.CalendarViewConfig:
        entity_type = self.db.query(models.EntityType).filter(
            models.EntityType.id == config_in.entity_type_id,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()
        if not entity_type:
            raise HTTPException(status_code=404, detail="Таблица для создания календаря не найдена.")

        config_data = config_in.model_dump()
        config_data['filters'] = json.dumps(config_in.filters)
        config_data['color_settings'] = json.dumps(config_in.color_settings)
        config_data['visible_fields'] = json.dumps(config_in.visible_fields)

        db_config = models.CalendarViewConfig(**config_data, tenant_id=current_user.tenant_id)
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def get_config_by_id(self, view_id: int, current_user: models.User) -> models.CalendarViewConfig:
        config = self.db.query(models.CalendarViewConfig).options(
            # "Жадно" загружаем связанные атрибуты, чтобы не делать лишних запросов
            joinedload(models.CalendarViewConfig.title_attribute),
            joinedload(models.CalendarViewConfig.start_date_attribute),
            joinedload(models.CalendarViewConfig.end_date_attribute),
            joinedload(models.CalendarViewConfig.is_allday_attribute),
            joinedload(models.CalendarViewConfig.color_attribute),
            joinedload(models.CalendarViewConfig.entity_type)
        ).filter(
            models.CalendarViewConfig.id == view_id,
            models.CalendarViewConfig.tenant_id == current_user.tenant_id
        ).first()
        if not config:
            raise HTTPException(status_code=404, detail="Конфигурация календаря не найдена.")
        return config

    def get_configs_for_entity(self, entity_type_id: int, current_user: models.User) -> List[models.CalendarViewConfig]:
        return self.db.query(models.CalendarViewConfig).filter(
            models.CalendarViewConfig.entity_type_id == entity_type_id,
            models.CalendarViewConfig.tenant_id == current_user.tenant_id
        ).order_by(models.CalendarViewConfig.name).all()

    def update_config(self, view_id: int, config_in: CalendarViewConfigUpdate,
                      current_user: models.User) -> models.CalendarViewConfig:
        db_config = self.get_config_by_id(view_id, current_user)
        update_data = config_in.model_dump(exclude_unset=True)
        if 'filters' in update_data: update_data['filters'] = json.dumps(update_data['filters'])
        if 'color_settings' in update_data: update_data['color_settings'] = json.dumps(update_data['color_settings'])
        if 'visible_fields' in update_data: update_data['visible_fields'] = json.dumps(update_data['visible_fields'])
        for key, value in update_data.items():
            setattr(db_config, key, value)
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def delete_config(self, view_id: int, current_user: models.User):
        db_config = self.get_config_by_id(view_id, current_user)
        self.db.delete(db_config)
        self.db.commit()
        return None

    # --- НАЧАЛО НОВОЙ РЕАЛИЗАЦИИ ---
    def get_events_for_view(self, view_id: int, start_date: date, end_date: date, current_user: models.User) -> List[
        Dict[str, Any]]:
        """
        Получает и форматирует события для указанного представления календаря.
        """
        # 1. Загружаем полную конфигурацию
        config = self.get_config_by_id(view_id, current_user)

        # 2. Собираем все фильтры
        all_filters = []
        if config.filters:
            all_filters.extend(json.loads(config.filters))

        # Добавляем главный фильтр по диапазону дат
        all_filters.append({
            "field": config.start_date_attribute.name,
            "op": "is_within",
            "value": [start_date.isoformat(), end_date.isoformat()]
        })

        # 3. Получаем сырые данные, используя мощь EAVService
        result = self.eav_service.get_all_entities_for_type(
            entity_type_name=config.entity_type.name,
            current_user=current_user,
            filters=all_filters,
            limit=1000  # Ограничение, чтобы не загружать слишком много событий
        )
        raw_events = result.get('data', [])

        # 4. Форматируем данные в стандартный вид для календаря
        formatted_events = []
        color_settings = json.loads(config.color_settings) if config.color_settings else {}

        for event_data in raw_events:
            start_val = event_data.get(config.start_date_attribute.name)
            if not start_val:
                continue

            end_val = event_data.get(config.end_date_attribute.name) if config.end_date_attribute else None

            # Определяем, событие на весь день или нет
            is_allday = True
            if config.is_allday_attribute:
                # Если поле "весь день" задано, его значение определяет флаг
                # (считаем False, если поле пустое или False)
                is_allday = bool(event_data.get(config.is_allday_attribute.name))

            # Определяем цвет
            color = None
            if config.color_attribute and color_settings:
                color_key = event_data.get(config.color_attribute.name)
                if color_key in color_settings:
                    color = color_settings[color_key]

            formatted_events.append({
                "id": f"{config.entity_type.name}_{event_data['id']}",
                "title": event_data.get(config.title_attribute.name, "Без названия"),
                "start": start_val,
                "end": end_val,
                "allDay": is_allday,
                "color": color,
                "extendedProps": {
                    "source_table": config.entity_type.name,
                    "source_id": event_data['id']
                }
            })

        return formatted_events
    # --- КОНЕЦ НОВОЙ РЕАЛИЗАЦИИ ---