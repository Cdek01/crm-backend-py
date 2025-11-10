from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from db import models, session
from api.deps import get_current_user
from sqlalchemy.orm import Session
from pydantic import BaseModel # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
from api.deps import get_current_admin_user
from sqlalchemy.orm import Session, joinedload # <-- Добавьте joinedload


router = APIRouter()

# --- Схемы для ответа ---

class PermissionInfo(BaseModel):
    name: str
    class Config:
        from_attributes = True

class RoleSchema(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class RoleDetailSchema(RoleSchema):
    permissions: List[PermissionInfo]

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


# --- Новый эндпоинт для получения всех ролей ---

@router.get("/", response_model=List[RoleDetailSchema], summary="Получить все роли с их разрешениями")
def get_all_roles(
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает список всех ролей, доступных для текущего пользователя.
    Суперадминистратор видит роли всех клиентов (tenants).
    Обычный пользователь видит только роли своего клиента.
    """
    query = db.query(models.Role).options(joinedload(models.Role.permissions))

    if not current_user.is_superuser:
        # Убедимся, что у пользователя есть tenant_id
        if not current_user.tenant_id:
            # Если у пользователя нет tenant, он не может иметь ролей
            return []
        query = query.filter(models.Role.tenant_id == current_user.tenant_id)

    roles = query.order_by(models.Role.name).all()
    return roles


@router.get("/simple-list", response_model=List[RoleSchema], summary="Получить простой список ролей")
def get_roles_simple_list(
        # Добавляем опциональный query-параметр tenant_id
        tenant_id: Optional[int] = None,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает простой список ролей (ID и имя).
    - Обычный пользователь получает роли только для своего tenant.
    - Суперадминистратор может запросить роли для любого tenant, передав ?tenant_id=...
      Если tenant_id не передан, он получает роли для своего собственного tenant.
    """
    target_tenant_id = current_user.tenant_id

    # Если запрос от суперадминистратора и он указал конкретный tenant_id, используем его
    if current_user.is_superuser and tenant_id is not None:
        target_tenant_id = tenant_id

    if target_tenant_id is None:
        # Если ни у пользователя нет tenant_id, ни он не передан в параметрах,
        # то ролей быть не может. Возвращаем пустой список.
        return []

    roles = db.query(models.Role).filter(
        models.Role.tenant_id == target_tenant_id
    ).order_by(models.Role.name).all()

    return roles