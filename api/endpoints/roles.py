from fastapi import APIRouter, Depends
from typing import List
from db import models, session
from api.deps import get_current_user
from sqlalchemy.orm import Session
from pydantic import BaseModel # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
from api.deps import get_current_admin_user


router = APIRouter()

class RoleSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

@router.get("/tenant/{tenant_id}", response_model=List[RoleSchema])
def get_roles_for_tenant(
    tenant_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Получить список ролей для конкретного тенанта."""
    # В будущем здесь можно добавить проверку, что current_user имеет право
    # видеть данные этого tenant_id (например, если он суперадмин).
    roles = db.query(models.Role).filter(models.Role.tenant_id == tenant_id).all()
    return roles