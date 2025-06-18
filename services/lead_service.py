# services/lead_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db import models, session
from crud.lead import lead as lead_crud
from schemas.lead import Lead, LeadCreate, LeadUpdate


class LeadService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Lead]:
        """Получить все лиды"""
        return lead_crud.get_multi(self.db, skip=skip, limit=limit)

    def get_by_id(self, lead_id: int) -> Lead:
        """Получить лид по ID"""
        lead = lead_crud.get(self.db, id=lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лид не найден")
        return lead

    def create_lead(self, lead_in: LeadCreate, current_user: models.User) -> Lead:
        """
        Создать новый лид.
        Бизнес-логика:
        1. Создает запись в БД.
        2. Присваивает ответственного.
        3. (В будущем) Может отправлять email, создавать задачу и т.д.
        """
        # Преобразуем Pydantic схему в словарь для добавления доп. полей
        lead_data = lead_in.model_dump()
        # Добавляем бизнес-логику - присваиваем ответственного
        # ИСПРАВЛЕНИЕ: Используем правильное имя поля из модели
        lead_data['responsible_manager_id'] = current_user.id

        # Передаем в CRUD уже готовый объект для создания
        # Мы создаем модель прямо тут, т.к. CRUD-слой должен быть "глупым"
        new_lead = models.Lead(**lead_data)

        self.db.add(new_lead)
        self.db.commit()
        self.db.refresh(new_lead)

        # Здесь можно добавить вызов другого сервиса, например:
        # notification_service.send_new_lead_email(new_lead)

        return new_lead

    def update_lead(self, lead_id: int, lead_in: LeadUpdate) -> Lead:
        """Обновить лид"""
        db_lead = self.get_by_id(lead_id)  # Переиспользуем наш метод для поиска и проверки
        return lead_crud.update(self.db, db_obj=db_lead, obj_in=lead_in)

    def delete_lead(self, lead_id: int):
        """Удалить лид"""
        self.get_by_id(lead_id)  # Проверяем, что лид существует
        lead_crud.remove(self.db, id=lead_id)
        return None