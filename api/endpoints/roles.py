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
        query = query.filter(models.Role.tenant_id == current_user.tenant_id)

    roles = query.order_by(models.Role.name).all()
    return roles


@router.get("/simple-list", response_model=List[RoleSchema], summary="Получить простой список ролей")
def get_roles_simple_list(
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает простой список ролей (ID и имя) для текущего клиента.
    Идеально подходит для заполнения выпадающих списков в UI.
    """
    # Суперадминистратору тоже нужно видеть роли в контексте какого-то клиента,
    # поэтому здесь всегда фильтруем по tenant_id текущего пользователя.
    roles = db.query(models.Role).filter(
        models.Role.tenant_id == current_user.tenant_id
    ).order_by(models.Role.name).all()

    if not roles and current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Для текущего пользователя-суперадминистратора не задан tenant. Укажите tenant_id для пользователя в админ-панели.",
        )