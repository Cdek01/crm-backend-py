# api/endpoints/leads.py
from fastapi import APIRouter, Depends, status, Body
from typing import List, Optional
from pydantic import BaseModel # <--- Добавьте BaseModel

from db import models
from schemas.lead import Lead, LeadCreate, LeadUpdate
from api.deps import get_current_user
from services.lead_service import LeadService # <-- ИМПОРТИРУЕМ СЕРВИС

router = APIRouter()



# --- Добавьте эту схему для тела запроса ---
class BulkDeleteRequest(BaseModel):
    ids: List[int]


# Мы используем Depends(LeadService), чтобы FastAPI автоматически
# создавал экземпляр сервиса для каждого запроса.
# В конструкторе LeadService уже есть Depends(get_db),
# так что сессия базы данных будет передана автоматически.

@router.post("/", response_model=Lead, status_code=status.HTTP_201_CREATED)
def create_lead(
    lead_in: LeadCreate,
    current_user: models.User = Depends(get_current_user),
    lead_service: LeadService = Depends(LeadService)
):
    """
    Создать новый лид.
    """
    return lead_service.create_lead(lead_in=lead_in, current_user=current_user)

# api/endpoints/leads.py
# @router.get("/", response_model=List[Lead])
# def get_all_leads(
#     skip: int = 0,
#     limit: int = 100,
#     current_user: models.User = Depends(get_current_user),
#     lead_service: LeadService = Depends(LeadService)
# ):
#     """
#     Получить список всех лидов.
#     """
#     # Передаем current_user в сервисный метод
#     return lead_service.get_all(current_user=current_user, skip=skip, limit=limit)

@router.get("/{lead_id}", response_model=Lead)
def get_lead_by_id(
    lead_id: int,
    current_user: models.User = Depends(get_current_user),
    lead_service: LeadService = Depends(LeadService)
):
    """
    Получить лид по ID.
    """
    return lead_service.get_by_id(lead_id=lead_id)

@router.put("/{lead_id}", response_model=Lead)
def update_lead(
    lead_id: int,
    lead_in: LeadUpdate,
    current_user: models.User = Depends(get_current_user),
    lead_service: LeadService = Depends(LeadService)
):
    """
    Обновить информацию о лиде.
    """
    # Передаем current_user в сервисный метод
    return lead_service.update_lead(
        lead_id=lead_id,
        lead_in=lead_in,
        current_user=current_user
    )
    return lead_service.update_lead(lead_id=lead_id, lead_in=lead_in)

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: int,
    current_user: models.User = Depends(get_current_user),
    lead_service: LeadService = Depends(LeadService)
):
    """
    Удалить лид.
    """
    return lead_service.delete_lead(lead_id=lead_id)


@router.get("/", response_model=List[Lead])
def get_all_leads(
    # --- ПАРАМЕТРЫ ФИЛЬТРАЦИИ ---
    lead_status: Optional[str] = None,
    organization_name: Optional[str] = None, # Для поиска по части названия
    # --- ПАРАМЕТРЫ СОРТИРОВКИ ---
    sort_by: Optional[str] = 'created_at', # Поле для сортировки по умолчанию
    sort_order: str = 'desc', # Порядок сортировки по умолчанию
    # --- ПАРАМЕТРЫ ПАГИНАЦИИ ---
    skip: int = 0,
    limit: int = 100,
    # --- ЗАВИСИМОСТИ ---
    current_user: models.User = Depends(get_current_user),
    lead_service: LeadService = Depends(LeadService)
):
    """
    Получить список всех лидов с фильтрацией и сортировкой.
    """
    # Передаем все новые параметры в сервисный слой
    return lead_service.get_all(
        current_user=current_user,
        skip=skip,
        limit=limit,
        lead_status=lead_status,
        organization_name=organization_name,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.delete("/bulk-delete", status_code=status.HTTP_200_OK)
def delete_multiple_leads(
    delete_request: BulkDeleteRequest = Body(...),
    current_user: models.User = Depends(get_current_user),
    lead_service: LeadService = Depends(LeadService)
):
    """
    Массовое удаление лидов по списку их ID.
    Возвращает количество удаленных записей.
    """
    deleted_count = lead_service.delete_multiple(
        ids=delete_request.ids,
        current_user=current_user
    )
    return {"deleted_count": deleted_count}