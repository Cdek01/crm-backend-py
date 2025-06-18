# crud/individual.py
from sqlalchemy.orm import Session
from .base import CRUDBase
from db.models import Individual
from schemas.individual import IndividualCreate, IndividualUpdate
from typing import Optional


class CRUDIndividual(CRUDBase[Individual, IndividualCreate, IndividualUpdate]):
    def get_by_inn(self, db: Session, *, inn: str) -> Optional[Individual]:
        if not inn:
            return None
        return db.query(self.model).filter(self.model.inn == inn).first()

individual = CRUDIndividual(Individual)