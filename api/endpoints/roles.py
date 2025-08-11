from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from db import models
from api.deps import get_current_user, require_permission
from services.role_service import RoleService

router = APIRouter()

class RoleCreateRequest(BaseModel):
    name: str

@router.post("/", dependencies=[Depends(require_permission("roles:manage"))])
def create_new_role(
    request: RoleCreateRequest,
    service: RoleService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новую роль для текущего клиента (тенанта)"""
    return service.create_role(name=request.name, current_user=current_user)

# Здесь же будут эндпоинты для назначения прав и т.д.