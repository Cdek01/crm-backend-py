# services/individual_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db import session
from crud.individual import individual as individual_crud
from schemas.individual import Individual, IndividualCreate, IndividualUpdate

class IndividualService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Individual]:
        return individual_crud.get_multi(self.db, skip=skip, limit=limit)

    def get_by_id(self, individual_id: int) -> Individual:
        ind = individual_crud.get(self.db, id=individual_id)
        if not ind:
            raise HTTPException(status_code=404, detail="Физическое лицо не найдено")
        return ind

    def create(self, individual_in: IndividualCreate) -> Individual:
        if individual_in.inn:
            existing = individual_crud.get_by_inn(self.db, inn=individual_in.inn)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Физическое лицо с таким ИНН уже существует"
                )
        return individual_crud.create(self.db, obj_in=individual_in)

    def update(self, individual_id: int, individual_in: IndividualUpdate) -> Individual:
        db_obj = self.get_by_id(individual_id)
        return individual_crud.update(self.db, db_obj=db_obj, obj_in=individual_in)

    def delete(self, individual_id: int):
        self.get_by_id(individual_id)
        individual_crud.remove(self.db, id=individual_id)
        return None