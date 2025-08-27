# services/select_list_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db import models, session
from schemas.select_options import (
    SelectOptionListCreate, SelectOptionListUpdate,
    SelectOptionCreate, SelectOptionUpdate
)


class SelectListService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    # --- Методы для Списков ---

    def get_all_lists(self, current_user: models.User) -> List[models.SelectOptionList]:
        """Получить все списки для текущего тенанта."""
        return self.db.query(models.SelectOptionList).filter(
            models.SelectOptionList.tenant_id == current_user.tenant_id
        ).all()

    def get_list_by_id(self, list_id: int, current_user: models.User) -> models.SelectOptionList:
        """Получить один список по ID с проверкой прав."""
        db_list = self.db.query(models.SelectOptionList).filter(
            models.SelectOptionList.id == list_id,
            models.SelectOptionList.tenant_id == current_user.tenant_id
        ).first()
        if not db_list:
            raise HTTPException(status_code=404, detail="Список не найден")
        return db_list

    def create_list(self, list_in: SelectOptionListCreate, current_user: models.User) -> models.SelectOptionList:
        """Создать новый список."""
        db_list = models.SelectOptionList(**list_in.dict(), tenant_id=current_user.tenant_id)
        self.db.add(db_list)
        self.db.commit()
        return db_list

    # --- Методы для Опций (вариантов выбора) ---

    def create_option(self, list_id: int, option_in: SelectOptionCreate,
                      current_user: models.User) -> models.SelectOption:
        """Добавить новую опцию в список."""
        # Проверяем, что сам список существует и принадлежит пользователю
        self.get_list_by_id(list_id, current_user)

        db_option = models.SelectOption(**option_in.dict(), option_list_id=list_id)
        self.db.add(db_option)
        self.db.commit()
        return db_option

    def update_option(self, option_id: int, option_in: SelectOptionUpdate,
                      current_user: models.User) -> models.SelectOption:
        """Обновить текст опции."""
        db_option = self.db.query(models.SelectOption).get(option_id)

        if not db_option or db_option.option_list.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Опция не найдена")

        db_option.value = option_in.value
        self.db.commit()
        return db_option

    def delete_option(self, option_id: int, current_user: models.User):
        """Удалить опцию."""
        db_option = self.db.query(models.SelectOption).get(option_id)

        if not db_option or db_option.option_list.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Опция не найдена")

        self.db.delete(db_option)
        self.db.commit()
        return None