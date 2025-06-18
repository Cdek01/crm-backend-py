# api/endpoints/leads.py
from fastapi import APIRouter, Depends, status
from typing import List

from db import models
from schemas.lead import Lead, LeadCreate, LeadUpdate
from api.deps import get_current_user
from services.lead_service import LeadService # <-- ИМПОРТИРУЕМ СЕРВИС

router = APIRouter()

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

@router.get("/", response_model=List[Lead])
def get_all_leads(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user), # Оставляем для проверки прав
    lead_service: LeadService = Depends(LeadService)
):
    """
    Получить список всех лидов.
    """
    return lead_service.get_all(skip=skip, limit=limit)

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