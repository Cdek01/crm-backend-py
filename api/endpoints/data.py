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
import io # <-- ШАГ 2: Добавьте этот импорт
import pandas as pd # <-- ШАГ 3: Добавьте этот импорт
from enum import Enum # <-- ШАГ 4: Добавьте этот импорт
from datetime import datetime # <-- ШАГ 5: Добавьте этот импорт
from fastapi.responses import StreamingResponse # <-- ШАГ 1: Добавьте этот импорт
from fastapi import HTTPException
from db import models



router = APIRouter()

# --- НОВАЯ СХЕМА ДЛЯ ВАЛИДАЦИИ ФОРМАТА ---
class ExportFormat(str, Enum):
    csv = "csv"
    xlsx = "xlsx"





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



from pydantic import BaseModel
class PaginatedEntityResponse(BaseModel):
    total: int
    data: List[Dict[str, Any]]
# @router.post("/{entity_type_name}", response_model=List[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
@router.post("/{entity_type_name}", response_model=PaginatedEntityResponse, status_code=status.HTTP_201_CREATED)
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
    # return service.create_entity(entity_type_name, data, current_user)
    return service.create_entity_and_get_list(entity_type_name, data, current_user)


# =============================================================================
# === ВАЖНОЕ ИЗМЕНЕНИЕ: Эндпоинт экспорта ПЕРЕМЕЩЕН СЮДА ===
# Он должен быть до любого маршрута, который содержит /.../{entity_id}
# =============================================================================
@router.get("/{entity_type_name}/export")
def export_entities(
        entity_type_name: str,
        format: ExportFormat,
        q: Optional[str] = Query(None),
        tenant_id: Optional[int] = Query(None),
        search_fields: Optional[str] = Query(None),
        filters: Optional[str] = None,
        sort_by: Optional[str] = Query('position'),
        sort_order: str = Query('asc'),
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    entity_type = service._get_entity_type_by_name(entity_type_name, current_user)

    search_fields_list = search_fields.split(',') if search_fields else []

    parsed_filters = []
    if filters:
        try:
            parsed_filters = json.loads(filters)
            if not isinstance(parsed_filters, list):
                parsed_filters = []
        except json.JSONDecodeError:
            pass

    result_data = service.get_all_entities_for_type(
        entity_type_name=entity_type_name,
        current_user=current_user,
        q=q,
        search_fields=search_fields_list,
        tenant_id=tenant_id,
        filters=parsed_filters,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=0,
        limit=100000
    )

    data_to_export = result_data['data']
    if not data_to_export:
        raise HTTPException(status_code=404, detail="Нет данных для экспорта по заданным фильтрам.")

    df = pd.DataFrame(data_to_export)

    column_mapping = {attr.name: attr.display_name for attr in entity_type.attributes}
    column_mapping.update({
        'id': 'ID', 'created_at': 'Дата создания',
        'updated_at': 'Дата изменения', 'position': 'Позиция'
    })

    df = df.rename(columns=column_mapping)

    final_columns = [name for name in column_mapping.values() if name in df.columns]
    df = df[final_columns]

    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)

    stream = io.BytesIO()
    filename = f"{entity_type_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if format == ExportFormat.csv:
        df.to_csv(stream, index=False, encoding='utf-8-sig')
        media_type = "text/csv"
        filename += ".csv"
    else:
        df.to_excel(stream, index=False, engine='openpyxl')
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename += ".xlsx"

    stream.seek(0)

    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(stream, media_type=media_type, headers=headers)

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


@router.get("/{entity_type_name}", response_model=PaginatedEntityResponse)
def get_all_entities(
        entity_type_name: str,
        q: Optional[str] = Query(None, description="Строка для универсального поиска по всем полям таблицы."),
        tenant_id: Optional[int] = Query(
            None,
            description="ID клиента (тенанта). Доступно только для суперадминистраторов."
        ),
        search_fields: Optional[str] = Query(None,
                                             description="Список полей для поиска через запятую (напр. 'name,phone')"),
        filters: Optional[str] = None,
        sort_by: Optional[str] = Query(default='position', description="Поле для сортировки"),
        sort_order: str = Query(default='asc', description="Порядок сортировки: asc или desc"),
        skip: int = Query(0, ge=0, description="Сколько записей пропустить (смещение)"),
        limit: int = Query(100, ge=1, le=100000, description="Максимальное количество записей для возврата"),

        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Получить все записи для указанного типа сущности с фильтрацией, сортировкой и поиском.
    """
    final_tenant_id = tenant_id
    if not current_user.is_superuser:
        final_tenant_id = None
    search_fields_list = search_fields.split(',') if search_fields else []

    parsed_filters = []
    if filters:
        try:
            parsed_filters = json.loads(filters)
            if not isinstance(parsed_filters, list):
                parsed_filters = []
        except json.JSONDecodeError:
            pass

    return service.get_all_entities_for_type(
        entity_type_name=entity_type_name,
        current_user=current_user,
        q=q,
        search_fields=search_fields_list,  # Передаем как список
        tenant_id=final_tenant_id,
        filters=parsed_filters,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
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


@router.get("/{entity_type_name}/group-by/{attribute_name}", response_model=List[Dict[str, Any]])
def group_entities_by_attribute(
        entity_type_name: str,
        attribute_name: str,
        tenant_id: Optional[int] = Query(None,
                                         description="ID клиента (тенанта). Доступно только для суперадминистраторов."),
        service: EAVService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Группирует данные по значению в колонке и возвращает количество записей для каждой группы.
    Например, можно сгруппировать лиды по статусу.
    """
    final_tenant_id = tenant_id
    if not current_user.is_superuser:
        final_tenant_id = None

    return service.group_by_attribute(
        entity_type_name=entity_type_name,
        group_by_attribute_name=attribute_name,
        current_user=current_user,
        tenant_id=final_tenant_id
    )





