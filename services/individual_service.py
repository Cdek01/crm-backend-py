# services/individual_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional

from db import session, models
from crud.individual import individual as individual_crud
from schemas.individual import Individual, IndividualCreate, IndividualUpdate

class IndividualService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

        # ЗАМЕНЯЕМ СТАРЫЙ get_all НА ЭТОТ

    # УБЕДИТЕСЬ, ЧТО ЭТО ЕДИНСТВЕННЫЙ МЕТОД get_all В КЛАССЕ
    def get_all(
            self,
            *,
            current_user: models.User,
            skip: int = 0,
            limit: int = 100,
            full_name: Optional[str] = None,
            inn: Optional[str] = None,
            phone_number: Optional[str] = None,
            email: Optional[str] = None,
            sort_by: str = 'created_at',
            sort_order: str = 'desc'
    ) -> List[models.Individual]:

        # 1. Базовый запрос с фильтрацией по tenant_id
        query = self.db.query(models.Individual).filter(
            models.Individual.tenant_id == current_user.tenant_id
        )

        # 2. Применяем фильтры
        if full_name:
            query = query.filter(models.Individual.full_name.ilike(f"%{full_name}%"))
        if inn:
            query = query.filter(models.Individual.inn == inn)
        if phone_number:
            query = query.filter(models.Individual.phone_number.ilike(f"%{phone_number}%"))
        if email:
            query = query.filter(models.Individual.email.ilike(f"%{email}%"))

        # 3. Применяем сортировку
        allowed_sort_fields = ['created_at', 'full_name', 'inn', 'city']
        if sort_by not in allowed_sort_fields:
            sort_by = 'created_at'

        sort_column = getattr(models.Individual, sort_by)

        if sort_order.lower() == 'asc':
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # 4. Пагинация и возврат
        return query.offset(skip).limit(limit).all()

    def get_by_id(self, individual_id: int, current_user: models.User) -> Individual:
        ind = self.db.query(models.Individual).filter(
            models.Individual.id == individual_id,
            models.Individual.tenant_id == current_user.tenant_id
        ).first()
        if not ind:
            raise HTTPException(status_code=404, detail="Физическое лицо не найдено")
        return ind

    def create(self, individual_in: IndividualCreate, current_user: models.User) -> Individual:
        if individual_in.inn:
            existing = self.db.query(models.Individual).filter(
                models.Individual.inn == individual_in.inn,
                models.Individual.tenant_id == current_user.tenant_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Физическое лицо с таким ИНН уже существует"
                )

        db_obj = models.Individual(**individual_in.model_dump(), tenant_id=current_user.tenant_id)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, individual_id: int, individual_in: IndividualUpdate, current_user: models.User) -> Individual:
        db_obj = self.get_by_id(individual_id=individual_id, current_user=current_user)
        # ИСПРАВЛЕНИЕ: Убедимся, что вызывается правильный CRUD метод
        update_data = individual_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, individual_id: int, current_user: models.User):
        db_obj = self.get_by_id(individual_id=individual_id, current_user=current_user)
        self.db.delete(db_obj)
        self.db.commit()
        return None


    # Добавьте новый метод
    def delete_multiple(self, ids: List[int], current_user: models.User) -> int:
        query = self.db.query(models.Individual).filter(
            models.Individual.tenant_id == current_user.tenant_id,
            models.Individual.id.in_(ids)
        )
        num_deleted = query.delete(synchronize_session=False)
        self.db.commit()
        return num_deleted


    def create_multiple(self, individuals_in: List[IndividualCreate], current_user: models.User) -> int:
        new_individuals = []
        for individual_in in individuals_in:
            individual_data = individual_in.model_dump()
            individual_data['tenant_id'] = current_user.tenant_id
            new_individual = models.Individual(**individual_data)
            new_individuals.append(new_individual)

        self.db.add_all(new_individuals)
        self.db.commit()
        return len(new_individuals)