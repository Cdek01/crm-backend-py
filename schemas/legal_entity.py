# schemas/legal_entity.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

# --- Базовая схема для СОЗДАНИЯ (с обязательным ИНН) ---
class LegalEntityBase(BaseModel):
    inn: str = Field(..., max_length=12, description="ИНН юридического лица")
    ogrn: Optional[str] = Field(None, max_length=15, description="ОГРН")
    short_name: Optional[str] = None
    full_name: Optional[str] = None
    kpp: Optional[str] = Field(None, max_length=9)
    status: Optional[str] = None
    registration_date: Optional[date] = None
    address: Optional[str] = None
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    notes: Optional[str] = None

# --- Схема для СОЗДАНИЯ ---
class LegalEntityCreate(LegalEntityBase):
    pass

# --- Схема для ОБНОВЛЕНИЯ (ИСПРАВЛЕНИЕ) ---
class LegalEntityUpdate(BaseModel):
    # Здесь мы перечисляем все поля, но делаем их ВСЕ опциональными.
    # Это позволяет обновлять любое подмножество полей.
    inn: Optional[str] = Field(None, max_length=12, description="ИНН юридического лица")
    ogrn: Optional[str] = Field(None, max_length=15, description="ОГРН")
    short_name: Optional[str] = None
    full_name: Optional[str] = None
    kpp: Optional[str] = Field(None, max_length=9)
    status: Optional[str] = None
    registration_date: Optional[date] = None
    address: Optional[str] = None
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    notes: Optional[str] = None

# --- Схема для ОТОБРАЖЕНИЯ ---
class LegalEntity(LegalEntityBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True