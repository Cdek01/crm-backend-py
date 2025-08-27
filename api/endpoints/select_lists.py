# api/endpoints/select_lists.py
from fastapi import APIRouter, Depends, status
from typing import List

from db import models
from api.deps import get_current_user
from services.select_list_service import SelectListService
from schemas.select_options import (
    SelectOptionList, SelectOptionListCreate, SelectOption, SelectOptionCreate, SelectOptionUpdate
)

router = APIRouter()

# --- Эндпоинты для управления списками ---

@router.post("/", response_model=SelectOptionList, status_code=status.HTTP_201_CREATED)
def create_new_list(
    list_in: SelectOptionListCreate,
    service: SelectListService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый выпадающий список."""
    return service.create_list(list_in=list_in, current_user=current_user)

@router.get("/", response_model=List[SelectOptionList])
def get_all_lists(
    service: SelectListService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Получить все выпадающие списки, созданные пользователем."""
    return service.get_all_lists(current_user=current_user)

@router.get("/{list_id}", response_model=SelectOptionList)
def get_list_details(
    list_id: int,
    service: SelectListService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Получить один список и все его опции."""
    return service.get_list_by_id(list_id=list_id, current_user=current_user)

# --- Эндпоинты для управления опциями внутри списка ---

@router.post("/{list_id}/options", response_model=SelectOption, status_code=status.HTTP_201_CREATED)
def add_option_to_list(
    list_id: int,
    option_in: SelectOptionCreate,
    service: SelectListService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Добавить новую опцию в существующий список."""
    return service.create_option(list_id=list_id, option_in=option_in, current_user=current_user)

@router.put("/{list_id}/options/{option_id}", response_model=SelectOption)
def update_option_in_list(
    list_id: int, # list_id здесь для консистентности URL, но проверка идет по option_id
    option_id: int,
    option_in: SelectOptionUpdate,
    service: SelectListService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Изменить текст существующей опции."""
    return service.update_option(option_id=option_id, option_in=option_in, current_user=current_user)

@router.delete("/{list_id}/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_option_from_list(
    list_id: int,
    option_id: int,
    service: SelectListService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """Удалить опцию из списка."""
    service.delete_option(option_id=option_id, current_user=current_user)
    return None