# schemas/lead.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# --- Базовая схема с ОБЯЗАТЕЛЬНЫМИ полями для СОЗДАНИЯ ---
class LeadBase(BaseModel):
    organization_name: str
    inn: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    lead_status: Optional[str] = "New"
    rating: Optional[int] = None
    rejection_reason: Optional[str] = None
    # notes: Optional[str] = None
    last_contact_date: Optional[date] = None

# --- Схема для СОЗДАНИЯ ---
class LeadCreate(LeadBase):
    pass # Наследует обязательное поле organization_name

# --- Схема для ОБНОВЛЕНИЯ (ИСПРАВЛЕНИЕ) ---
class LeadUpdate(BaseModel):
    # Здесь мы перечисляем ВСЕ поля из LeadBase, но делаем их ВСЕ Optional
    organization_name: Optional[str] = None
    inn: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    lead_status: Optional[str] = None
    rating: Optional[int] = None
    rejection_reason: Optional[str] = None
    # notes: Optional[str] = None
    last_contact_date: Optional[date] = None


# --- Схема для ОТОБРАЖЕНИЯ ---
class Lead(LeadBase):
    id: int
    responsible_manager_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True