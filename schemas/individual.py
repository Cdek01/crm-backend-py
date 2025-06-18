# schemas/individual.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

# --- Базовая схема для СОЗДАНИЯ ---
class IndividualBase(BaseModel):
    full_name: str
    inn: Optional[str] = Field(None, max_length=12, description="ИНН физического лица")
    city: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    is_sole_proprietor: Optional[bool] = False
    notes: Optional[str] = None # Поле для заметок, которое мы добавили в модель

# --- Схема для СОЗДАНИЯ ---
class IndividualCreate(IndividualBase):
    pass

# --- Схема для ОБНОВЛЕНИЯ (ИСПРАВЛЕНИЕ) ---
class IndividualUpdate(BaseModel):
    # Перечисляем все поля из IndividualBase, делая их опциональными
    full_name: Optional[str] = None
    inn: Optional[str] = Field(None, max_length=12, description="ИНН физического лица")
    city: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    is_sole_proprietor: Optional[bool] = None
    notes: Optional[str] = None

# --- Схема для ОТОБРАЖЕНИЯ ---
class Individual(IndividualBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True