# api/endpoints/data.py
from fastapi import APIRouter, Depends, status, Body, Query
from typing import List, Dict, Any, Optional
import json
from db import models
from services.eav_service import EAVService
from api.deps import get_current_user

router = APIRouter()








# @router.post("/{entity_type_name}", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
# def create_entity(
#         entity_type_name: str,
#         data: Dict[str, Any] = Body(...),
#         service: EAVService = Depends(),
#         current_user: models.User = Depends(get_current_user)
# ):
#     """Создать новую запись."""
#     return service.create_entity(entity_type_name, data, current_user)

# --- ИЗМЕНИТЕ `response_model` ---
@router.post("/{entity_type_name}", response_model=List[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
# ---------------------------------
def create_entity(
        entity_type_name: str,
        data: Dict[str, Any] = Body(...),
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Создать новую запись и вернуть ПОЛНЫЙ, отсортированный список всех записей,
    где новая запись будет в начале.
    """
    return service.create_entity_and_get_list(entity_type_name, data, current_user)
















@router.get("/{entity_type_name}/{entity_id}", response_model=Dict[str, Any])
def get_entity(
        entity_type_name: str,
        entity_id: int,
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Получить одну запись по ID."""
    return service.get_entity_by_id(entity_id, current_user)


@router.put("/{entity_type_name}/{entity_id}", response_model=Dict[str, Any])
def update_entity(
        entity_type_name: str,
        entity_id: int,
        data: Dict[str, Any] = Body(...),
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Обновить запись."""
    return service.update_entity(entity_id, data, current_user)


@router.delete("/{entity_type_name}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(
        entity_type_name: str,
        entity_id: int,
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Удалить запись."""
    return service.delete_entity(entity_id, current_user)


# --- ЕДИНСТВЕННОЕ И ПРАВИЛЬНОЕ ОПРЕДЕЛЕНИЕ ЭНДПОИНТА ДЛЯ ПОЛУЧЕНИЯ СПИСКА ---
@router.get("/{entity_type_name}", response_model=List[Dict[str, Any]])
def get_all_entities(
        entity_type_name: str,

        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Заменяем `Query(...)` на `Query(None, ...)`
        tenant_id: Optional[int] = Query(
            None,  # <-- `None` в качестве первого аргумента делает параметр необязательным
            description="ID клиента (тенанта). Доступно только для суперадминистраторов."
        ),
        filters: Optional[str] = None,
        sort_by: Optional[str] = 'created_at',
        sort_order: str = 'desc',

        # --- ДОБАВЬТЕ ЭТИ ДВА ПАРАМЕТРА ---
        skip: int = Query(0, ge=0, description="Сколько записей пропустить (смещение)"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей для возврата"),
        # ---------------------------------

        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):


    """
    Получить все записи для указанного типа сущности с фильтрацией и сортировкой.
    """
    parsed_filters = []
    if filters:
        try:
            parsed_filters = json.loads(filters)
            if not isinstance(parsed_filters, list):
                parsed_filters = []
        except json.JSONDecodeError:
            pass

    # --- ИСПРАВЛЕНИЕ: Передаем ВСЕ необходимые аргументы в сервис ---
    return service.get_all_entities_for_type(
        entity_type_name=entity_type_name,
        current_user=current_user,
        tenant_id=tenant_id,
        filters=parsed_filters,
        sort_by=sort_by,
        sort_order=sort_order,
        # --- ПЕРЕДАЕМ НОВЫЕ ПАРАМЕТРЫ В СЕРВИС ---
        skip=skip,
        limit=limit
        # -----------------------------------------
    )