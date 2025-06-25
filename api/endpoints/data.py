# api/endpoints/data.py
from fastapi import APIRouter, Depends, status, Body
from typing import List, Dict, Any

from db import models
from services.eav_service import EAVService
from api.deps import get_current_user

router = APIRouter()


@router.get("/{entity_type_name}", response_model=List[Dict[str, Any]])
def get_all_entities(
        entity_type_name: str,
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Получить все записи для указанного типа сущности."""
    return service.get_all_entities_for_type(entity_type_name)


@router.post("/{entity_type_name}", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_entity(
        entity_type_name: str,
        data: Dict[str, Any] = Body(...),
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Создать новую запись."""
    return service.create_entity(entity_type_name, data)


@router.get("/{entity_type_name}/{entity_id}", response_model=Dict[str, Any])
def get_entity(
        entity_type_name: str,  # Пока не используется, но полезно для структуры URL
        entity_id: int,
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Получить одну запись по ID."""
    return service.get_entity_by_id(entity_id)


@router.put("/{entity_type_name}/{entity_id}", response_model=Dict[str, Any])
def update_entity(
        entity_type_name: str,
        entity_id: int,
        data: Dict[str, Any] = Body(...),
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Обновить запись (полностью заменяет все поля)."""
    return service.update_entity(entity_id, data)


@router.delete("/{entity_type_name}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(
        entity_type_name: str,
        entity_id: int,
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Удалить запись."""
    return service.delete_entity(entity_id)