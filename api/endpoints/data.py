# # api/endpoints/data.py
# from fastapi import APIRouter, Depends, status, Body, Query
# from typing import List, Dict, Any, Optional
# import json
# from db import models
# from services.eav_service import EAVService
# from api.deps import get_current_user, require_permission
#
# router = APIRouter()
#
#
# @router.get("/{entity_type_name}", response_model=List[Dict[str, Any]])
# def get_all_entities(
#         entity_type_name: str,
#         has_permission: bool = Depends(lambda entity_type_name: require_permission(f"data:view:{entity_type_name}")),
#         service: EAVService = Depends(),
#         current_user: models.User = Depends(get_current_user)
# ):
#     """Получить все записи для указанного типа сущности."""
#     return service.get_all_entities_for_type(entity_type_name)
#
#
# @router.post("/{entity_type_name}", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
# def create_entity(
#         entity_type_name: str,
#         data: Dict[str, Any] = Body(...),
#         service: EAVService = Depends(),
#         current_user: models.User = Depends(get_current_user),
#         has_permission: bool = Depends(lambda entity_type_name: require_permission(f"data:create:{entity_type_name}"))
# ):
#     """Создать новую запись."""
#     return service.create_entity(entity_type_name, data, current_user)
#
#
# @router.get("/{entity_type_name}/{entity_id}", response_model=Dict[str, Any])
# def get_entity(
#         entity_type_name: str,  # Пока не используется, но полезно для структуры URL
#         entity_id: int,
#         has_permission: bool = Depends(lambda entity_type_name: require_permission(f"data:view:{entity_type_name}")),
#         service: EAVService = Depends(),
#         current_user: models.User = Depends(get_current_user)
# ):
#     """Получить одну запись по ID."""
#     return service.get_entity_by_id(entity_id, current_user)
#
#
# @router.put("/{entity_type_name}/{entity_id}", response_model=Dict[str, Any])
# def update_entity(
#         entity_type_name: str,
#         entity_id: int,
#         has_permission: bool = Depends(lambda entity_type_name: require_permission(f"data:edit:{entity_type_name}")),
#         data: Dict[str, Any] = Body(...),
#         service: EAVService = Depends(),
#         current_user: models.User = Depends(get_current_user)
# ):
#     """Обновить запись (полностью заменяет все поля)."""
#     return service.update_entity(entity_id, data)
#
#
# @router.delete("/{entity_type_name}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_entity(
#         entity_type_name: str,
#         entity_id: int,
#         service: EAVService = Depends(),
#         current_user: models.User = Depends(get_current_user)
# ):
#     """Удалить запись."""
#     return service.delete_entity(entity_id)
#
#
# router.get("/{entity_type_name}", response_model=List[Dict[str, Any]])
#
#
# def get_all_entities(
#         entity_type_name: str,
#
#         # --- НОВЫЙ ПАРАМЕТР ---
#         # Добавляем опциональный query-параметр tenant_id
#         tenant_id: Optional[int] = Query(
#             None,
#             description="ID клиента (тенанта), чьи данные нужно получить. Доступно только для суперадминистраторов."
#         ),
#         # ----------------------
#
#         filters: Optional[str] = None,
#         sort_by: Optional[str] = 'created_at',
#         sort_order: str = 'desc',
#         service: EAVService = Depends(),
#         current_user: models.User = Depends(get_current_user)
# ):
#     """
#     Получить все записи для указанного типа сущности с фильтрацией и сортировкой.
#     Суперадминистратор может использовать параметр 'tenant_id' для просмотра данных конкретного клиента.
#     """
#     parsed_filters = []
#     if filters:
#         try:
#             parsed_filters = json.loads(filters)
#             if not isinstance(parsed_filters, list):
#                 parsed_filters = []
#         except json.JSONDecodeError:
#             pass
#
#     # --- ИЗМЕНЕНИЕ В ВЫЗОВЕ СЕРВИСА ---
#     # Просто передаем новый параметр tenant_id в сервисный метод,
#     # который мы уже подготовили для его обработки.
#     return service.get_all_entities_for_type(
#         entity_type_name=entity_type_name,
#         current_user=current_user,
#         tenant_id=tenant_id,  # <--- Передаем ID тенанта
#         filters=parsed_filters,
#         sort_by=sort_by,
#         sort_order=sort_order
#     )


# api/endpoints/data.py
from fastapi import APIRouter, Depends, status, Body, Query
from typing import List, Dict, Any, Optional
import json
from db import models
from services.eav_service import EAVService
from api.deps import get_current_user

router = APIRouter()

@router.post("/{entity_type_name}", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_entity(
        entity_type_name: str,
        data: Dict[str, Any] = Body(...),
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Создать новую запись."""
    return service.create_entity(entity_type_name, data, current_user)


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
        tenant_id: Optional[int] = Query(
            None,
            description="ID клиента (тенанта). Доступно только для суперадминистраторов."
        ),
        filters: Optional[str] = None,
        sort_by: Optional[str] = 'created_at',
        sort_order: str = 'desc',
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
        current_user=current_user,  # <-- Передаем текущего пользователя
        tenant_id=tenant_id,
        filters=parsed_filters,
        sort_by=sort_by,
        sort_order=sort_order
    )