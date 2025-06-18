# api/endpoints/individuals.py
from fastapi import APIRouter, Depends, status
from typing import List

from db.models import User
from schemas.individual import Individual, IndividualCreate, IndividualUpdate
from api.deps import get_current_user
from services.individual_service import IndividualService

router = APIRouter()

@router.post("/", response_model=Individual, status_code=status.HTTP_201_CREATED)
def create_individual(
    individual_in: IndividualCreate,
    service: IndividualService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новое физическое лицо.
    """
    return service.create(individual_in=individual_in)


@router.get("/", response_model=List[Individual])
def get_all_individuals(
    skip: int = 0,
    limit: int = 100,
    service: IndividualService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список всех физических лиц.
    """
    return service.get_all(skip=skip, limit=limit)


@router.get("/{individual_id}", response_model=Individual)
def get_individual_by_id(
    individual_id: int,
    service: IndividualService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Получить информацию о физическом лице по его ID.
    """
    return service.get_by_id(individual_id=individual_id)


@router.put("/{individual_id}", response_model=Individual)
def update_individual(
    individual_id: int,
    individual_in: IndividualUpdate,
    service: IndividualService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить информацию о физическом лице.
    """
    return service.update(individual_id=individual_id, individual_in=individual_in)


@router.delete("/{individual_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_individual(
    individual_id: int,
    service: IndividualService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить физическое лицо.
    """
    return service.delete(individual_id=individual_id)