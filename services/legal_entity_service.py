# services/legal_entity_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db import session
from crud.legal_entity import legal_entity as legal_entity_crud
from schemas.legal_entity import LegalEntity, LegalEntityCreate, LegalEntityUpdate

class LegalEntityService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[LegalEntity]:
        return legal_entity_crud.get_multi(self.db, skip=skip, limit=limit)

    def get_by_id(self, entity_id: int) -> LegalEntity:
        entity = legal_entity_crud.get(self.db, id=entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Юридическое лицо не найдено")
        return entity

    def create(self, entity_in: LegalEntityCreate) -> LegalEntity:
        # Бизнес-логика: проверка на уникальность по ИНН
        existing_entity = legal_entity_crud.get_by_inn(self.db, inn=entity_in.inn)
        if existing_entity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Юридическое лицо с таким ИНН уже существует"
            )
        return legal_entity_crud.create(self.db, obj_in=entity_in)

    def update(self, entity_id: int, entity_in: LegalEntityUpdate) -> LegalEntity:
        db_entity = self.get_by_id(entity_id) # Проверка на существование
        return legal_entity_crud.update(self.db, db_obj=db_entity, obj_in=entity_in)

    def delete(self, entity_id: int):
        self.get_by_id(entity_id) # Проверка на существование
        legal_entity_crud.remove(self.db, id=entity_id)
        return None