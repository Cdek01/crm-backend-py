# api/endpoints/legal_entities.py
from fastapi import APIRouter, Depends, status
from typing import List, Optional

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
    # ИСПРАВЛЕНИЕ: передаем current_user в сервисный метод
    return service.create(entity_in=entity_in, current_user=current_user)

@router.get("/", response_model=List[LegalEntity])
def get_all_legal_entities(
    # --- ПАРАМЕТРЫ ФИЛЬТРАЦИИ ---
    inn: Optional[str] = None,
    ogrn: Optional[str] = None,
    short_name: Optional[str] = None, # Для поиска по части названия
    status: Optional[str] = None,
    # --- ПАРАМЕТРЫ СОРТИРОВКИ ---
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    # --- ПАРАМЕТРЫ ПАГИНАЦИИ ---
    skip: int = 0,
    limit: int = 100,
    # --- ЗАВИСИМОСТИ ---
    service: LegalEntityService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список всех юридических лиц с фильтрацией и сортировкой.
    """
    # ИСПРАВЛЕНИЕ: Передаем ВСЕ параметры в сервис
    return service.get_all(
        current_user=current_user,
        skip=skip,
        limit=limit,
        inn=inn,
        ogrn=ogrn,
        short_name=short_name,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )

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


@router.get("/", response_model=List[LegalEntity])
def get_all_legal_entities(
    # --- ПАРАМЕТРЫ ФИЛЬТРАЦИИ ---
    inn: Optional[str] = None,
    ogrn: Optional[str] = None,
    short_name: Optional[str] = None, # Для поиска по части названия
    status: Optional[str] = None,
    # --- ПАРАМЕТРЫ СОРТИРОВКИ ---
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    # --- ПАРАМЕТРЫ ПАГИНАЦИИ ---
    skip: int = 0,
    limit: int = 100,
    # --- ЗАВИСИМОСТИ ---
    service: LegalEntityService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список всех юридических лиц с фильтрацией и сортировкой.
    """
    return service.get_all(
        current_user=current_user,
        skip=skip,
        limit=limit,
        inn=inn,
        ogrn=ogrn,
        short_name=short_name,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )



router.post("/bulk-load", status_code=status.HTTP_200_OK)
def create_multiple_legal_entities(
    entities_in: List[LegalEntityCreate],
    current_user: User = Depends(get_current_user),
    service: LegalEntityService = Depends()
):
    created_count = service.create_multiple(
        entities_in=entities_in,
        current_user=current_user
    )
    return {"created_count": created_count}