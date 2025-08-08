# # services/lead_service.py
# from fastapi import Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from sqlalchemy import desc, asc
# from db import models, session
# from crud.lead import lead as lead_crud
# from schemas.lead import Lead, LeadCreate, LeadUpdate
#
#
# class LeadService:
#     def __init__(self, db: Session = Depends(session.get_db)):
#         self.db = db
#
#
#     def get_by_id(self, lead_id: int, current_user: models.User):
#         """
#         Получает лид по ID с проверкой принадлежности к тенанту.
#         """
#         db_lead = self.db.query(models.Lead).filter(
#             models.Lead.id == lead_id,
#             models.Lead.tenant_id == current_user.tenant_id  # <-- Эта строка теперь будет работать
#         ).first()
#
#         if not db_lead:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Лид не найден"
#             )
#         return db_lead
#
#     def create_lead(self, lead_in: LeadCreate, current_user: models.User) -> Lead:
#         """
#         Создать новый лид.
#         Бизнес-логика:
#         1. Создает запись в БД.
#         2. Присваивает ответственного.
#         3. (В будущем) Может отправлять email, создавать задачу и т.д.
#         """
#         # Преобразуем Pydantic схему в словарь для добавления доп. полей
#         lead_data = lead_in.model_dump()
#         # Добавляем бизнес-логику - присваиваем ответственного
#         # ИСПРАВЛЕНИЕ: Используем правильное имя поля из модели
#         lead_data['responsible_manager_id'] = current_user.id
#
#         # Передаем в CRUD уже готовый объект для создания
#         # Мы создаем модель прямо тут, т.к. CRUD-слой должен быть "глупым"
#         new_lead = models.Lead(**lead_data,
#         tenant_id=current_user.tenant_id,)
#
#         self.db.add(new_lead)
#         self.db.commit()
#         self.db.refresh(new_lead)
#
#         # Здесь можно добавить вызов другого сервиса, например:
#         # notification_service.send_new_lead_email(new_lead)
#
#         return new_lead
#
#     def update_lead(self, lead_id: int, lead_in: LeadUpdate, current_user: models.User):  # <-- Добавили current_user
#
#         # Сначала находим лид, УЖЕ с проверкой прав доступа
#         db_lead = self.get_by_id(lead_id=lead_id, current_user=current_user)  # <-- Передали current_user
#
#         # Обновляем поля
#         update_data = lead_in.dict(exclude_unset=True)
#         for key, value in update_data.items():
#             setattr(db_lead, key, value)
#
#         self.db.add(db_lead)
#         self.db.commit()
#         self.db.refresh(db_lead)
#         return db_lead
#
#     def delete_lead(self, lead_id: int):
#         """Удалить лид"""
#         self.get_by_id(lead_id)  # Проверяем, что лид существует
#         lead_crud.remove(self.db, id=lead_id)
#         return None
#
#
#     def __init__(self, db: Session = Depends(session.get_db)):
#         self.db = db
#
#     # ЗАМЕНЯЕМ СТАРЫЙ get_all НА ЭТОТ
#     def get_all(
#         self,
#         *,
#         current_user: models.User,
#         lead_status: Optional[str] = None,
#         organization_name: Optional[str] = None,
#         sort_by: Optional[str] = 'created_at',
#         sort_order: str = 'desc',
#         skip: int = 0,
#         limit: int = 100
#     ) -> List[models.Lead]:
#         """
#         Получить все лиды с динамической фильтрацией и сортировкой.
#         """
#         # 1. Начинаем строить запрос. Обязательно фильтруем по tenant_id!
#         query = self.db.query(models.Lead).filter(
#             models.Lead.tenant_id == current_user.tenant_id
#         )
#
#         # 2. Динамически добавляем фильтры
#         if lead_status:
#             query = query.filter(models.Lead.lead_status == lead_status)
#
#         if organization_name:
#             # Используем ilike для поиска без учета регистра
#             query = query.filter(models.Lead.organization_name.ilike(f"%{organization_name}%"))
#
#         # 3. Динамически добавляем сортировку
#         # Валидация: разрешаем сортировку только по безопасным полям
#         allowed_sort_fields = ['created_at', 'organization_name', 'lead_status', 'rating']
#         if sort_by not in allowed_sort_fields:
#             sort_by = 'created_at' # Возвращаемся к значению по умолчанию
#
#         # Получаем объект колонки из модели по её строковому имени
#         sort_column = getattr(models.Lead, sort_by)
#
#         if sort_order.lower() == 'asc':
#             query = query.order_by(asc(sort_column))
#         else:
#             query = query.order_by(desc(sort_column))
#
#         # 4. Применяем пагинацию и выполняем запрос
#         return query.offset(skip).limit(limit).all()
#
#
#     def get_by_id(self, lead_id: int, current_user: models.User) -> models.Lead: # <- Добавьте current_user
#         """Получить лид по ID"""
#         lead = self.db.query(models.Lead).filter(
#             models.Lead.id == lead_id,
#             models.Lead.tenant_id == current_user.tenant_id # <-- ОБЯЗАТЕЛЬНОЕ УСЛОВИЕ
#         ).first()
#         if not lead:
#             raise HTTPException(status_code=404, detail="Лид не найден")
#         return lead
#
#
#     def delete_multiple(self, ids: List[int], current_user: models.User) -> int:
#         """
#         Удаляет несколько лидов по списку ID с проверкой прав доступа (tenant_id).
#         """
#         # 1. Формируем запрос на удаление
#         query = self.db.query(models.Lead).filter(
#             models.Lead.tenant_id == current_user.tenant_id, # КРАЙНЕ ВАЖНО: проверка прав доступа
#             models.Lead.id.in_(ids)                         # Фильтр по списку ID
#         )
#
#         # 2. Выполняем удаление и получаем количество удаленных строк
#         # synchronize_session=False рекомендуется для массовых операций для лучшей производительности
#         num_deleted = query.delete(synchronize_session=False)
#
#         # 3. Коммитим транзакцию
#         self.db.commit()
#
#         # 4. Возвращаем количество
#         return num_deleted
#
#     def create_multiple(self, leads_in: List[LeadCreate], current_user: models.User) -> int:
#         """
#         Создает несколько лидов из списка.
#         Все операции выполняются в одной транзакции.
#         """
#         new_leads = []
#         for lead_in in leads_in:
#             # Преобразуем Pydantic схему в словарь
#             lead_data = lead_in.model_dump()
#
#             # Применяем ту же бизнес-логику, что и при создании одного лида
#             lead_data['responsible_manager_id'] = current_user.id
#             lead_data['tenant_id'] = current_user.tenant_id
#
#             # Создаем объект модели, но пока не коммитим
#             new_lead = models.Lead(**lead_data)
#             new_leads.append(new_lead)
#
#         # Добавляем все новые объекты в сессию одним разом
#         self.db.add_all(new_leads)
#
#         # Коммитим транзакцию ОДИН раз после добавления всех
#         self.db.commit()
#
#         # Возвращаем количество созданных записей
#         return len(new_leads)


# services/lead_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import desc, asc
from db import models, session
# crud.lead больше не используется напрямую, можно убрать
# from crud.lead import lead as lead_crud
from schemas.lead import Lead, LeadCreate, LeadUpdate


class LeadService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

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
        Получить все лиды.
        Суперадминистратор видит лиды всех клиентов.
        """
        # --- ИЗМЕНЕНИЕ ---
        # 1. Начинаем строить "пустой" запрос.
        query = self.db.query(models.Lead)
        # 2. Если пользователь НЕ суперадминистратор, добавляем фильтр по тенанту.
        if not current_user.is_superuser:
            query = query.filter(models.Lead.tenant_id == current_user.tenant_id)
        # -----------------

        # 3. Дальше все как было - применяем остальные фильтры
        if lead_status:
            query = query.filter(models.Lead.lead_status == lead_status)
        if organization_name:
            query = query.filter(models.Lead.organization_name.ilike(f"%{organization_name}%"))

        # ... и сортировку
        allowed_sort_fields = ['created_at', 'organization_name', 'lead_status', 'rating']
        if sort_by in allowed_sort_fields:
            sort_column = getattr(models.Lead, sort_by)
            query = query.order_by(asc(sort_column) if sort_order.lower() == 'asc' else desc(sort_column))

        return query.offset(skip).limit(limit).all()

    def get_by_id(self, lead_id: int, current_user: models.User) -> models.Lead:
        """
        Получает лид по ID.
        Суперадминистратор может получить любой лид по ID.
        """
        # --- ИЗМЕНЕНИЕ ---
        query = self.db.query(models.Lead).filter(models.Lead.id == lead_id)
        if not current_user.is_superuser:
            query = query.filter(models.Lead.tenant_id == current_user.tenant_id)
        db_lead = query.first()
        # -----------------

        if not db_lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лид не найден")
        return db_lead

    def create_lead(self, lead_in: LeadCreate, current_user: models.User) -> Lead:
        """Создать новый лид (логика не меняется)."""
        lead_data = lead_in.model_dump()
        lead_data['responsible_manager_id'] = current_user.id
        new_lead = models.Lead(**lead_data, tenant_id=current_user.tenant_id)
        self.db.add(new_lead)
        self.db.commit()
        self.db.refresh(new_lead)
        return new_lead

    def update_lead(self, lead_id: int, lead_in: LeadUpdate, current_user: models.User) -> models.Lead:
        """Обновить лид."""
        # Метод get_by_id уже содержит проверку прав
        db_lead = self.get_by_id(lead_id=lead_id, current_user=current_user)
        update_data = lead_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_lead, key, value)
        self.db.add(db_lead)
        self.db.commit()
        self.db.refresh(db_lead)
        return db_lead

    def delete_lead(self, lead_id: int, current_user: models.User) -> None:
        """Удалить лид."""
        # Метод get_by_id уже содержит проверку прав
        db_lead = self.get_by_id(lead_id=lead_id, current_user=current_user)
        self.db.delete(db_lead)
        self.db.commit()
        return None

    def delete_multiple(self, ids: List[int], current_user: models.User) -> int:
        """
        Массовое удаление.
        Суперадминистратор может удалять лиды любого клиента.
        """
        # --- ИЗМЕНЕНИЕ ---
        query = self.db.query(models.Lead).filter(models.Lead.id.in_(ids))
        if not current_user.is_superuser:
            query = query.filter(models.Lead.tenant_id == current_user.tenant_id)
        # -----------------
        num_deleted = query.delete(synchronize_session=False)
        self.db.commit()
        return num_deleted

    def create_multiple(self, leads_in: List[LeadCreate], current_user: models.User) -> int:
        """Массовое создание (логика не меняется)."""
        new_leads = []
        for lead_in in leads_in:
            lead_data = lead_in.model_dump()
            lead_data['responsible_manager_id'] = current_user.id
            lead_data['tenant_id'] = current_user.tenant_id
            new_leads.append(models.Lead(**lead_data))
        self.db.add_all(new_leads)
        self.db.commit()
        return len(new_leads)