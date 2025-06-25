# api/endpoints/meta.py
from fastapi import APIRouter, Depends, status
from typing import List

from db import models
from schemas.eav import EntityType, EntityTypeCreate, Attribute, AttributeCreate
from services.eav_service import EAVService
from api.deps import get_current_user

router = APIRouter()

@router.post("/entity-types", response_model=EntityType, status_code=status.HTTP_201_CREATED)
def create_entity_type(
    entity_type_in: EntityTypeCreate,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый тип сущности (пользовательскую 'таблицу')."""
    return service.create_entity_type(entity_type_in)


@router.post("/entity-types/{entity_type_id}/attributes", response_model=Attribute, status_code=status.HTTP_201_CREATED)
def create_attribute(
    entity_type_id: int,
    attribute_in: AttributeCreate,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый атрибут (пользовательскую 'колонку') для типа сущности."""
    return service.create_attribute_for_type(entity_type_id, attribute_in)