# api/endpoints/legal_entities.py
from fastapi import APIRouter, Depends, status
from typing import List

from db.models import User
from schemas.legal_entity import LegalEntity, LegalEntityCreate, LegalEntityUpdate
from api.deps import get_current_user
from services.legal_entity_service import LegalEntityService

router = APIRouter()

@router.post("/", response_model=LegalEntity, status_code=status.HTTP_201_CREATED)
def create_legal_entity(
    entity_in: LegalEntityCreate,
    service: LegalEntityService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return service.create(entity_in=entity_in)

@router.get("/", response_model=List[LegalEntity])
def get_all_legal_entities(
    skip: int = 0,
    limit: int = 100,
    service: LegalEntityService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return service.get_all(skip=skip, limit=limit)

@router.get("/{entity_id}", response_model=LegalEntity)
def get_legal_entity_by_id(
    entity_id: int,
    service: LegalEntityService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return service.get_by_id(entity_id=entity_id)

@router.put("/{entity_id}", response_model=LegalEntity)
def update_legal_entity(
    entity_id: int,
    entity_in: LegalEntityUpdate,
    service: LegalEntityService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return service.update(entity_id=entity_id, entity_in=entity_in)

@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_legal_entity(
    entity_id: int,
    service: LegalEntityService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return service.delete(entity_id=entity_id)