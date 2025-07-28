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

    # Добавляем current_user: models.User в аргументы
    def get_all(self, current_user: models.User, skip: int = 0, limit: int = 100):
        """
        Получает список лидов для ТЕКУЩЕГО пользователя (его тенанта).
        """
        # Теперь current_user здесь определен и мы можем его использовать
        return self.db.query(models.Lead).filter(
            models.Lead.tenant_id == current_user.tenant_id
        ).offset(skip).limit(limit).all()

    def get_by_id(self, lead_id: int) -> Lead:
        """Получить лид по ID"""
        lead = self.db.query(models.Lead).filter(
            models.Lead.id == lead_id,
            models.Lead.tenant_id == current_user.tenant_id # <-- ОБЯЗАТЕЛЬНОЕ УСЛОВИЕ
        ).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Лид не найден") # Не говорим, что он есть у другого клиента!
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
        new_lead = models.Lead(**lead_data,
        tenant_id=current_user.tenant_id,)

        self.db.add(new_lead)
        self.db.commit()
        self.db.refresh(new_lead)

        # Здесь можно добавить вызов другого сервиса, например:
        # notification_service.send_new_lead_email(new_lead)

        return new_lead

    def update_lead(self, lead_id: int, lead_in: LeadUpdate, current_user: models.User):  # <-- Добавили current_user

        # Сначала находим лид, УЖЕ с проверкой прав доступа
        db_lead = self.get_by_id(lead_id=lead_id, current_user=current_user)  # <-- Передали current_user

        # Обновляем поля
        update_data = lead_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_lead, key, value)

        self.db.add(db_lead)
        self.db.commit()
        self.db.refresh(db_lead)
        return db_lead

    def delete_lead(self, lead_id: int):
        """Удалить лид"""
        self.get_by_id(lead_id)  # Проверяем, что лид существует
        lead_crud.remove(self.db, id=lead_id)
        return None