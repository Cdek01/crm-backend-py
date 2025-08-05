# api/endpoints/aliases.py
from fastapi import APIRouter, Depends, Body, status
from typing import Dict, Any

from db import models
from api.deps import get_current_user
from services.alias_service import AliasService
from pydantic import BaseModel

router = APIRouter()

class AliasSetRequest(BaseModel):
    table_name: str
    attribute_name: str
    display_name: str

# --- Эндпоинт для получения ВСЕХ псевдонимов ---
@router.get("/", response_model=Dict[str, Dict[str, str]])
def get_all_aliases(
    service: AliasService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Получить все пользовательские названия колонок для всех таблиц.
    """
    return service.get_aliases_for_tenant(current_user=current_user)

# --- Эндпоинт для установки/обновления одного псевдонима ---
@router.post("/", status_code=status.HTTP_201_CREATED)
def set_alias(
    request: AliasSetRequest,
    service: AliasService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Установить новое отображаемое имя для колонки.
    """
    return service.set_alias(
        table_name=request.table_name,
        attribute_name=request.attribute_name,
        display_name=request.display_name,
        current_user=current_user
    )

# --- Эндпоинт для сброса одного псевдонима ---
@router.delete("/{table_name}/{attribute_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alias(
    table_name: str,
    attribute_name: str,
    service: AliasService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Сбросить пользовательское имя колонки к стандартному.
    """
    return service.delete_alias(
        table_name=table_name,
        attribute_name=attribute_name,
        current_user=current_user
    )