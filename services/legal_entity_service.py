# # # services/legal_entity_service.py
# # from fastapi import Depends, HTTPException, status
# # from sqlalchemy.orm import Session
# # from sqlalchemy import desc, asc
# # from typing import List, Optional
# #
# # from db import session, models
# # from crud.legal_entity import legal_entity as legal_entity_crud
# # from schemas.legal_entity import LegalEntity, LegalEntityCreate, LegalEntityUpdate
# #
# # class LegalEntityService:
# #     def __init__(self, db: Session = Depends(session.get_db)):
# #         self.db = db
# #
# #         # ЗАМЕНЯЕМ СТАРЫЙ get_all НА ЭТОТ
# #
# #     # УБЕДИТЕСЬ, ЧТО ЭТО ЕДИНСТВЕННЫЙ МЕТОД get_all В КЛАССЕ
# #     def get_all(
# #             self,
# #             *,
# #             current_user: models.User,
# #             skip: int = 0,
# #             limit: int = 100,
# #             inn: Optional[str] = None,
# #             ogrn: Optional[str] = None, # Этот аргумент должен присутствовать
# #             short_name: Optional[str] = None,
# #             status: Optional[str] = None,
# #             sort_by: str = 'created_at',
# #             sort_order: str = 'desc'
# #     ) -> List[models.LegalEntity]:
# #
# #         # 1. Базовый запрос с обязательной фильтрацией по клиенту (tenant)
# #         query = self.db.query(models.LegalEntity).filter(
# #             models.LegalEntity.tenant_id == current_user.tenant_id
# #         )
# #
# #         # 2. Применяем фильтры
# #         if inn:
# #             query = query.filter(models.LegalEntity.inn == inn)
# #         if ogrn: # И он должен использоваться здесь
# #             query = query.filter(models.LegalEntity.ogrn == ogrn)
# #         if status:
# #             query = query.filter(models.LegalEntity.status == status)
# #         if short_name:
# #             query = query.filter(models.LegalEntity.short_name.ilike(f"%{short_name}%"))
# #
# #         # 3. Применяем сортировку
# #         allowed_sort_fields = [
# #             'created_at', 'short_name', 'inn', 'registration_date', 'revenue', 'net_profit'
# #         ]
# #         if sort_by not in allowed_sort_fields:
# #             sort_by = 'created_at'
# #
# #         sort_column = getattr(models.LegalEntity, sort_by)
# #
# #         if sort_order.lower() == 'asc':
# #             query = query.order_by(asc(sort_column))
# #         else:
# #             query = query.order_by(desc(sort_column))
# #
# #         # 4. Применяем пагинацию и возвращаем результат
# #         return query.offset(skip).limit(limit).all()
# #
# #     def get_by_id(self, entity_id: int, current_user: models.User) -> LegalEntity:
# #         entity = self.db.query(models.LegalEntity).filter(
# #             models.LegalEntity.id == entity_id,
# #             models.LegalEntity.tenant_id == current_user.tenant_id
# #         ).first()
# #         if not entity:
# #             raise HTTPException(status_code=404, detail="Юридическое лицо не найдено")
# #         return entity
# #
# #     def create(self, entity_in: LegalEntityCreate, current_user: models.User) -> LegalEntity:
# #         existing_entity = self.db.query(models.LegalEntity).filter(
# #             models.LegalEntity.inn == entity_in.inn,
# #             models.LegalEntity.tenant_id == current_user.tenant_id
# #         ).first()
# #         if existing_entity:
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="Юридическое лицо с таким ИНН уже существует"
# #             )
# #
# #         db_obj = models.LegalEntity(**entity_in.model_dump(), tenant_id=current_user.tenant_id)
# #         self.db.add(db_obj)
# #         self.db.commit()
# #         self.db.refresh(db_obj)
# #         return db_obj
# #
# #     def update(self, entity_id: int, entity_in: LegalEntityUpdate, current_user: models.User) -> LegalEntity:
# #         db_entity = self.get_by_id(entity_id=entity_id, current_user=current_user)
# #         # ИСПРАВЛЕНИЕ: Убедимся, что вызывается правильный CRUD метод
# #         update_data = entity_in.model_dump(exclude_unset=True)
# #         for key, value in update_data.items():
# #             setattr(db_entity, key, value)
# #         self.db.add(db_entity)
# #         self.db.commit()
# #         self.db.refresh(db_entity)
# #         return db_entity
# #
# #     def delete(self, entity_id: int, current_user: models.User):
# #         db_entity = self.get_by_id(entity_id=entity_id, current_user=current_user)
# #         self.db.delete(db_entity)
# #         self.db.commit()
# #         return None
# #
# #
# #
# #     # Добавьте новый метод
# #     def delete_multiple(self, ids: List[int], current_user: models.User) -> int:
# #         query = self.db.query(models.LegalEntity).filter(
# #             models.LegalEntity.tenant_id == current_user.tenant_id,
# #             models.LegalEntity.id.in_(ids)
# #         )
# #         num_deleted = query.delete(synchronize_session=False)
# #         self.db.commit()
# #         return num_deleted
# #
# #
# #
# #     def create_multiple(self, entities_in: List[LegalEntityCreate], current_user: models.User) -> int:
# #         new_entities = []
# #         for entity_in in entities_in:
# #             # Здесь можно добавить проверку на уникальность ИНН в рамках батча, если нужно
# #             entity_data = entity_in.model_dump()
# #             entity_data['tenant_id'] = current_user.tenant_id
# #             new_entity = models.LegalEntity(**entity_data)
# #             new_entities.append(new_entity)
# #
# #         self.db.add_all(new_entities)
# #         self.db.commit()
# #         return len(new_entities)
#
#
# # services/individual_service.py
# from fastapi import Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from sqlalchemy import desc, asc
# from typing import List, Optional
# from db import session, models
# from schemas.individual import Individual, IndividualCreate, IndividualUpdate
#
#
# class IndividualService:
#     def __init__(self, db: Session = Depends(session.get_db)):
#         self.db = db
#
#     def get_all(
#             self,
#             *,
#             current_user: models.User,
#             skip: int = 0,
#             limit: int = 100,
#             full_name: Optional[str] = None,
#             inn: Optional[str] = None,
#             phone_number: Optional[str] = None,
#             email: Optional[str] = None,
#             sort_by: str = 'created_at',
#             sort_order: str = 'desc'
#     ) -> List[models.Individual]:
#         """
#         Получить все физ. лица.
#         Суперадминистратор видит данные всех клиентов.
#         """
#         # --- ИЗМЕНЕНИЕ ---
#         query = self.db.query(models.Individual)
#         if not current_user.is_superuser:
#             query = query.filter(models.Individual.tenant_id == current_user.tenant_id)
#         # -----------------
#
#         # Применяем фильтры
#         if full_name:
#             query = query.filter(models.Individual.full_name.ilike(f"%{full_name}%"))
#         if inn:
#             query = query.filter(models.Individual.inn == inn)
#         # ... и так далее
#
#         # Применяем сортировку
#         # ...
#
#         return query.offset(skip).limit(limit).all()
#
#     def get_by_id(self, individual_id: int, current_user: models.User) -> models.Individual:
#         """
#         Получить физ. лицо по ID.
#         Суперадминистратор может получить любого.
#         """
#         # --- ИЗМЕНЕНИЕ ---
#         query = self.db.query(models.Individual).filter(models.Individual.id == individual_id)
#         if not current_user.is_superuser:
#             query = query.filter(models.Individual.tenant_id == current_user.tenant_id)
#         ind = query.first()
#         # -----------------
#
#         if not ind:
#             raise HTTPException(status_code=404, detail="Физическое лицо не найдено")
#         return ind
#
#     def create(self, individual_in: IndividualCreate, current_user: models.User) -> models.Individual:
#         # Логика не меняется
#         # ...
#         db_obj = models.Individual(**individual_in.model_dump(), tenant_id=current_user.tenant_id)
#         self.db.add(db_obj)
#         self.db.commit()
#         self.db.refresh(db_obj)
#         return db_obj
#
#     def update(self, individual_id: int, individual_in: IndividualUpdate,
#                current_user: models.User) -> models.Individual:
#         db_obj = self.get_by_id(individual_id=individual_id, current_user=current_user)
#         update_data = individual_in.model_dump(exclude_unset=True)
#         for key, value in update_data.items():
#             setattr(db_obj, key, value)
#         self.db.add(db_obj)
#         self.db.commit()
#         self.db.refresh(db_obj)
#         return db_obj
#
#     def delete(self, individual_id: int, current_user: models.User):
#         db_obj = self.get_by_id(individual_id=individual_id, current_user=current_user)
#         self.db.delete(db_obj)
#         self.db.commit()
#         return None
#
#     def delete_multiple(self, ids: List[int], current_user: models.User) -> int:
#         """Массовое удаление. Суперадмин может удалять данные любого клиента."""
#         # --- ИЗМЕНЕНИЕ ---
#         query = self.db.query(models.Individual).filter(models.Individual.id.in_(ids))
#         if not current_user.is_superuser:
#             query = query.filter(models.Individual.tenant_id == current_user.tenant_id)
#         # -----------------
#         num_deleted = query.delete(synchronize_session=False)
#         self.db.commit()
#         return num_deleted
#
#     def create_multiple(self, individuals_in: List[IndividualCreate], current_user: models.User) -> int:
#         # Логика не меняется
#         # ...
#         return len(new_individuals)


# services/legal_entity_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional

from db import session, models
from schemas.legal_entity import LegalEntity, LegalEntityCreate, LegalEntityUpdate

class LegalEntityService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    def get_all(
            self,
            *,
            current_user: models.User,
            skip: int = 0,
            limit: int = 100,
            inn: Optional[str] = None,
            ogrn: Optional[str] = None,
            short_name: Optional[str] = None,
            status: Optional[str] = None,
            sort_by: str = 'created_at',
            sort_order: str = 'desc'
    ) -> List[models.LegalEntity]:
        """
        Получить все юр. лица.
        Суперадминистратор видит данные всех клиентов.
        """
        # --- ИЗМЕНЕНИЕ ---
        query = self.db.query(models.LegalEntity)
        if not current_user.is_superuser:
            query = query.filter(models.LegalEntity.tenant_id == current_user.tenant_id)
        # -----------------

        # Применяем фильтры
        if inn:
            query = query.filter(models.LegalEntity.inn == inn)
        if ogrn:
            query = query.filter(models.LegalEntity.ogrn == ogrn)
        if status:
            query = query.filter(models.LegalEntity.status == status)
        if short_name:
            query = query.filter(models.LegalEntity.short_name.ilike(f"%{short_name}%"))

        # Применяем сортировку
        allowed_sort_fields = ['created_at', 'short_name', 'inn', 'registration_date', 'revenue', 'net_profit']
        if sort_by in allowed_sort_fields:
            sort_column = getattr(models.LegalEntity, sort_by)
            query = query.order_by(asc(sort_column) if sort_order.lower() == 'asc' else desc(sort_column))

        return query.offset(skip).limit(limit).all()

    def get_by_id(self, entity_id: int, current_user: models.User) -> models.LegalEntity:
        """
        Получить юр. лицо по ID.
        Суперадминистратор может получить любое.
        """
        # --- ИЗМЕНЕНИЕ ---
        query = self.db.query(models.LegalEntity).filter(models.LegalEntity.id == entity_id)
        if not current_user.is_superuser:
            query = query.filter(models.LegalEntity.tenant_id == current_user.tenant_id)
        entity = query.first()
        # -----------------

        if not entity:
            raise HTTPException(status_code=404, detail="Юридическое лицо не найдено")
        return entity

    def create(self, entity_in: LegalEntityCreate, current_user: models.User) -> models.LegalEntity:
        """Создание юр. лица (логика не меняется)."""
        existing_entity = self.db.query(models.LegalEntity).filter(
            models.LegalEntity.inn == entity_in.inn,
            models.LegalEntity.tenant_id == current_user.tenant_id
        ).first()
        if existing_entity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Юридическое лицо с таким ИНН уже существует")

        db_obj = models.LegalEntity(**entity_in.model_dump(), tenant_id=current_user.tenant_id)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, entity_id: int, entity_in: LegalEntityUpdate, current_user: models.User) -> models.LegalEntity:
        """Обновление юр. лица."""
        # get_by_id уже содержит проверку прав
        db_entity = self.get_by_id(entity_id=entity_id, current_user=current_user)
        update_data = entity_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_entity, key, value)
        self.db.add(db_entity)
        self.db.commit()
        self.db.refresh(db_entity)
        return db_entity

    def delete(self, entity_id: int, current_user: models.User):
        """Удаление юр. лица."""
        db_entity = self.get_by_id(entity_id=entity_id, current_user=current_user)
        self.db.delete(db_entity)
        self.db.commit()
        return None

    def delete_multiple(self, ids: List[int], current_user: models.User) -> int:
        """Массовое удаление. Суперадмин может удалять данные любого клиента."""
        # --- ИЗМЕНЕНИЕ ---
        query = self.db.query(models.LegalEntity).filter(models.LegalEntity.id.in_(ids))
        if not current_user.is_superuser:
            query = query.filter(models.LegalEntity.tenant_id == current_user.tenant_id)
        # -----------------
        num_deleted = query.delete(synchronize_session=False)
        self.db.commit()
        return num_deleted

    def create_multiple(self, entities_in: List[LegalEntityCreate], current_user: models.User) -> int:
        """Массовое создание (логика не меняется)."""
        new_entities = []
        for entity_in in entities_in:
            entity_data = entity_in.model_dump()
            entity_data['tenant_id'] = current_user.tenant_id
            new_entities.append(models.LegalEntity(**entity_data))
        self.db.add_all(new_entities)
        self.db.commit()
        return len(new_entities)