# services/calendar_service.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import date

from db import models, session
from schemas.calendar import CalendarViewConfigCreate, CalendarViewConfigUpdate
from services.eav_service import EAVService


class CalendarService:
    def __init__(self, db: Session = Depends(session.get_db), eav_service: EAVService = Depends()):
        self.db = db
        self.eav_service = eav_service

    # --- CRUD для конфигураций ---

    def create_config(self, config_in: CalendarViewConfigCreate,
                      current_user: models.User) -> models.CalendarViewConfig:
        """Создает новую конфигурацию представления-календаря."""
        # Проверка, что родительская таблица принадлежит пользователю
        entity_type = self.db.query(models.EntityType).filter(
            models.EntityType.id == config_in.entity_type_id,
            models.EntityType.tenant_id == current_user.tenant_id
        ).first()
        if not entity_type:
            raise HTTPException(status_code=404, detail="Таблица для создания календаря не найдена.")

        # Преобразуем словари и списки в JSON-строки для сохранения в БД
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
        """Получает одну конфигурацию по ID с проверкой прав."""
        config = self.db.query(models.CalendarViewConfig).filter(
            models.CalendarViewConfig.id == view_id,
            models.CalendarViewConfig.tenant_id == current_user.tenant_id
        ).first()
        if not config:
            raise HTTPException(status_code=404, detail="Конфигурация календаря не найдена.")
        return config

    def get_configs_for_entity(self, entity_type_id: int, current_user: models.User) -> List[models.CalendarViewConfig]:
        """Получает все конфигурации календарей для одной EAV-таблицы."""
        return self.db.query(models.CalendarViewConfig).filter(
            models.CalendarViewConfig.entity_type_id == entity_type_id,
            models.CalendarViewConfig.tenant_id == current_user.tenant_id
        ).order_by(models.CalendarViewConfig.name).all()

    def update_config(self, view_id: int, config_in: CalendarViewConfigUpdate,
                      current_user: models.User) -> models.CalendarViewConfig:
        """Обновляет существующую конфигурацию."""
        db_config = self.get_config_by_id(view_id, current_user)

        update_data = config_in.model_dump(exclude_unset=True)

        # Обрабатываем поля, которые должны быть JSON
        if 'filters' in update_data:
            update_data['filters'] = json.dumps(update_data['filters'])
        if 'color_settings' in update_data:
            update_data['color_settings'] = json.dumps(update_data['color_settings'])
        if 'visible_fields' in update_data:
            update_data['visible_fields'] = json.dumps(update_data['visible_fields'])

        for key, value in update_data.items():
            setattr(db_config, key, value)

        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def delete_config(self, view_id: int, current_user: models.User):
        """Удаляет конфигурацию."""
        db_config = self.get_config_by_id(view_id, current_user)
        self.db.delete(db_config)
        self.db.commit()
        return None

    # --- Логика получения событий (пока заглушка) ---

    def get_events_for_view(self, view_id: int, start_date: date, end_date: date, current_user: models.User) -> List[
        Dict[str, Any]]:
        """
        Получает события для календаря.
        (Основную логику мы реализуем на следующем шаге).
        """
        # Просто проверяем, что конфигурация существует
        self.get_config_by_id(view_id, current_user)

        # Пока возвращаем пустой список, чтобы не было ошибки
        return []