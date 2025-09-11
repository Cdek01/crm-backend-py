# api/endpoints/data.py
from fastapi import APIRouter, Depends, status, Body, Query
from typing import List, Dict, Any, Optional
import json
from db import models
from services.eav_service import EAVService
from api.deps import get_current_user
from schemas.data import BulkDeleteRequest
from schemas.eav import EntityOrderSetRequest
from schemas.eav import EntityOrderUpdateSmartRequest


router = APIRouter()



@router.post("/{entity_type_name}/bulk-delete", status_code=status.HTTP_200_OK)
def delete_multiple_entities(
    entity_type_name: str,
    delete_request: BulkDeleteRequest = Body(...),
    # --- ДОБАВЛЯЕМ QUERY-ПАРАМЕТР ---
    _source: Optional[str] = None,
    # -------------------------------
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Массовое удаление записей по списку их ID.
    Возвращает JSON с количеством удаленных записей.
    """
    deleted_count = service.delete_multiple_entities(
        entity_type_name=entity_type_name,
        ids=delete_request.ids,
        current_user=current_user,
        source=_source  # <-- Передаем `_source` в сервис
    )
    return {"deleted_count": deleted_count}



@router.post("/{entity_type_name}", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
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
        # --- ДОБАВЛЯЕМ QUERY-ПАРАМЕТР ---
        _source: Optional[str] = None,
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """Удалить запись."""
    return service.delete_entity(entity_id, current_user, source=_source)

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
        # sort_by: Optional[str] = Query('position', ...),  # Устанавливаем 'position' по умолчанию
        # sort_order: str = 'desc',
        sort_by: Optional[str] = Query(default='position', description="Поле для сортировки"),
        sort_order: str = Query(default='asc', description="Порядок сортировки: asc или desc"),
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

    # --- ДОБАВЬТЕ ЭТУ ПРОВЕРКУ ---
    final_tenant_id = tenant_id
    if not current_user.is_superuser:
        # Если пользователь не суперадмин, принудительно обнуляем tenant_id,
        # даже если фронтенд его передал.
        final_tenant_id = None
    # ---------------------------


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
        tenant_id=final_tenant_id,
        filters=parsed_filters,
        sort_by=sort_by,
        sort_order=sort_order,
        # --- ПЕРЕДАЕМ НОВЫЕ ПАРАМЕТРЫ В СЕРВИС ---
        skip=skip,
        limit=limit
        # -----------------------------------------
    )


@router.post("/{entity_type_name}/order", status_code=status.HTTP_200_OK)
def set_entity_order(
    entity_type_name: str,
    order_in: EntityOrderSetRequest,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Установить и сохранить новый порядок отображения строк для таблицы.
    """
    return service.set_entity_order(
        entity_type_name=entity_type_name,
        entity_ids=order_in.entity_ids,
        current_user=current_user
    )




@router.post("/{entity_type_name}/position", status_code=status.HTTP_200_OK)
def update_entity_position(
    entity_type_name: str,
    update_in: EntityOrderUpdateSmartRequest,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Обновить позицию одной строки.
    """
    return service.update_entity_position(
        entity_type_name=entity_type_name,
        entity_id=update_in.entity_id,
        after_pos=update_in.after_position,
        before_pos=update_in.before_position,
        current_user=current_user
    )