# crud/legal_entity.py
from sqlalchemy.orm import Session
from .base import CRUDBase
from db.models import LegalEntity
from schemas.legal_entity import LegalEntityCreate, LegalEntityUpdate
from typing import Optional  # <--- ДОБАВЬТЕ ЭТОТ ИМПОРТ


class CRUDLegalEntity(CRUDBase[LegalEntity, LegalEntityCreate, LegalEntityUpdate]):
    def get_by_inn(self, db: Session, *, inn: str) -> Optional[LegalEntity]:
        """
        Получить юридическое лицо по ИНН.
        """
        return db.query(self.model).filter(self.model.inn == inn).first()

legal_entity = CRUDLegalEntity(LegalEntity)