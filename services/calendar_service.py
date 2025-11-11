# services/calendar_service.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db import models, session
from schemas.calendar import CalendarViewConfigCreate, CalendarViewConfigUpdate


class CalendarService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    def create_config(self, config_in: CalendarViewConfigCreate, current_user: models.User):
        # TODO: Добавить логику создания
        raise NotImplementedError("Логика еще не реализована")

    def get_configs_for_entity(self, entity_type_id: int, current_user: models.User):
        # TODO: Добавить логику получения списка
        raise NotImplementedError("Логика еще не реализована")

    def get_config_by_id(self, view_id: int, current_user: models.User):
        # TODO: Добавить логику получения одного
        raise NotImplementedError("Логика еще не реализована")

    def update_config(self, view_id: int, config_in: CalendarViewConfigUpdate, current_user: models.User):
        # TODO: Добавить логику обновления
        raise NotImplementedError("Логика еще не реализована")

    def delete_config(self, view_id: int, current_user: models.User):
        # TODO: Добавить логику удаления
        raise NotImplementedError("Логика еще не реализована")