# crud/lead.py
from sqlalchemy.orm import Session
from .base import CRUDBase
from db.models import Lead
from schemas.lead import LeadCreate, LeadUpdate
from typing import Optional

class CRUDLead(CRUDBase[Lead, LeadCreate, LeadUpdate]):
    # Здесь можно будет добавлять специфичные для лидов методы,
    # например, поиск по INN или по статусу.
    def get_by_inn(self, db: Session, *, inn: str) -> Optional[Lead]:
        return db.query(Lead).filter(Lead.inn == inn).first()

lead = CRUDLead(Lead)