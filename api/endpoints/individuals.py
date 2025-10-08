# api/endpoints/individuals.py
from fastapi import APIRouter, Depends, status
from typing import List, Optional
from fastapi import Body
from pydantic import BaseModel
from typing import List
from db.models import User
from schemas.individual import Individual, IndividualCreate, IndividualUpdate
from api.deps import get_current_user
from services.individual_service import IndividualService

router = APIRouter()


class BulkDeleteRequest(BaseModel):
    ids: List[int]


@router.delete("/bulk-delete", status_code=status.HTTP_200_OK)
def delete_multiple_individuals(
    delete_request: BulkDeleteRequest = Body(...),
    current_user: User = Depends(get_current_user),
    service: IndividualService = Depends()
):
    deleted_count = service.delete_multiple(
        ids=delete_request.ids,
        current_user=current_user
    )
    return {"deleted_count": deleted_count}


@router.post("/", response_model=Individual, status_code=status.HTTP_201_CREATED)
def create_individual(
    individual_in: IndividualCreate,
    service: IndividualService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новое физическое лицо.
    """
    # ИСПРАВЛЕНИЕ: передаем current_user в сервисный метод
    return service.create(individual_in=individual_in, current_user=current_user)

# ... остальной код без изменений

# @router.get("/", response_model=List[Individual])
# def get_all_individuals(
#     # --- ПАРАМЕТРЫ ФИЛЬТРАЦИИ ---
#     full_name: Optional[str] = None,
#     inn: Optional[str] = None,
#     phone_number: Optional[str] = None,
#     email: Optional[str] = None,
#     # --- ПАРАМЕТРЫ СОРТИРОВКИ ---
#     sort_by: Optional[str] = 'created_at',
#     sort_order: str = 'desc',
#     # --- ПАРАМЕТРЫ ПАГИНАЦИИ ---
#     skip: int = 0,
#     limit: int = 100,
#     # --- ЗАВИСИМОСТИ ---
#     service: IndividualService = Depends(),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Получить список всех физических лиц с фильтрацией и сортировкой.
#     """
#     # ИСПРАВЛЕНИЕ: Передаем ВСЕ параметры в сервис
#     return service.get_all(
#         current_user=current_user,
#         skip=skip,
#         limit=limit,
#         full_name=full_name,
#         inn=inn,
#         phone_number=phone_number,
#         email=email,
#         sort_by=sort_by,
#         sort_order=sort_order
#     )


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



@router.get("/", response_model=List[Individual])
def get_all_individuals(
    # --- ПАРАМЕТРЫ ФИЛЬТРАЦИИ ---
    full_name: Optional[str] = None,
    inn: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    # --- ПАРАМЕТРЫ СОРТИРОВКИ ---
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    # --- ПАРАМЕТРЫ ПАГИНАЦИИ ---
    skip: int = 0,
    limit: int = 100,
    # --- ЗАВИСИМОСТИ ---
    service: IndividualService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список всех физических лиц с фильтрацией и сортировкой.
    """
    return service.get_all(
        current_user=current_user,
        skip=skip,
        limit=limit,
        full_name=full_name,
        inn=inn,
        phone_number=phone_number,
        email=email,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.post("/bulk-load", status_code=status.HTTP_200_OK)
def create_multiple_individuals(
    individuals_in: List[IndividualCreate],
    current_user: User = Depends(get_current_user),
    service: IndividualService = Depends()
):
    created_count = service.create_multiple(
        individuals_in=individuals_in,
        current_user=current_user
    )
    return {"created_count": created_count}