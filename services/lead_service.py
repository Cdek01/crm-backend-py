# services/lead_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import desc, asc
from db import models, session
from crud.lead import lead as lead_crud
from schemas.lead import Lead, LeadCreate, LeadUpdate


class LeadService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    # Добавляем current_user: models.User в аргументы
    # def get_all(self, current_user: models.User, skip: int = 0, limit: int = 100):
    #     """
    #     Получает список лидов для ТЕКУЩЕГО пользователя (его тенанта).
    #     """
    #     # Теперь current_user здесь определен и мы можем его использовать
    #     return self.db.query(models.Lead).filter(
    #         models.Lead.tenant_id == current_user.tenant_id
    #     ).offset(skip).limit(limit).all()

    def get_by_id(self, lead_id: int, current_user: models.User):
        """
        Получает лид по ID с проверкой принадлежности к тенанту.
        """
        db_lead = self.db.query(models.Lead).filter(
            models.Lead.id == lead_id,
            models.Lead.tenant_id == current_user.tenant_id  # <-- Эта строка теперь будет работать
        ).first()

        if not db_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Лид не найден"
            )
        return db_lead

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


    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    # ЗАМЕНЯЕМ СТАРЫЙ get_all НА ЭТОТ
    def get_all(
        self,
        *,
        current_user: models.User,
        lead_status: Optional[str] = None,
        organization_name: Optional[str] = None,
        sort_by: Optional[str] = 'created_at',
        sort_order: str = 'desc',
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Lead]:
        """
        Получить все лиды с динамической фильтрацией и сортировкой.
        """
        # 1. Начинаем строить запрос. Обязательно фильтруем по tenant_id!
        query = self.db.query(models.Lead).filter(
            models.Lead.tenant_id == current_user.tenant_id
        )

        # 2. Динамически добавляем фильтры
        if lead_status:
            query = query.filter(models.Lead.lead_status == lead_status)

        if organization_name:
            # Используем ilike для поиска без учета регистра
            query = query.filter(models.Lead.organization_name.ilike(f"%{organization_name}%"))

        # 3. Динамически добавляем сортировку
        # Валидация: разрешаем сортировку только по безопасным полям
        allowed_sort_fields = ['created_at', 'organization_name', 'lead_status', 'rating']
        if sort_by not in allowed_sort_fields:
            sort_by = 'created_at' # Возвращаемся к значению по умолчанию

        # Получаем объект колонки из модели по её строковому имени
        sort_column = getattr(models.Lead, sort_by)

        if sort_order.lower() == 'asc':
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # 4. Применяем пагинацию и выполняем запрос
        return query.offset(skip).limit(limit).all()


    def get_by_id(self, lead_id: int, current_user: models.User) -> models.Lead: # <- Добавьте current_user
        """Получить лид по ID"""
        lead = self.db.query(models.Lead).filter(
            models.Lead.id == lead_id,
            models.Lead.tenant_id == current_user.tenant_id # <-- ОБЯЗАТЕЛЬНОЕ УСЛОВИЕ
        ).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Лид не найден")
        return lead


    def delete_multiple(self, ids: List[int], current_user: models.User) -> int:
        """
        Удаляет несколько лидов по списку ID с проверкой прав доступа (tenant_id).
        """
        # 1. Формируем запрос на удаление
        query = self.db.query(models.Lead).filter(
            models.Lead.tenant_id == current_user.tenant_id, # КРАЙНЕ ВАЖНО: проверка прав доступа
            models.Lead.id.in_(ids)                         # Фильтр по списку ID
        )

        # 2. Выполняем удаление и получаем количество удаленных строк
        # synchronize_session=False рекомендуется для массовых операций для лучшей производительности
        num_deleted = query.delete(synchronize_session=False)

        # 3. Коммитим транзакцию
        self.db.commit()

        # 4. Возвращаем количество
        return num_deleted