# schemas/shares.py
from pydantic import BaseModel
from typing import List, Optional
from db.models import PermissionLevel # Импортируем наш Enum

# --- Схема для создания нового доступа ---
class ShareCreate(BaseModel):
    entity_type_id: int
    grantee_user_id: int
    permission_level: PermissionLevel # Используем Enum для валидации

# --- Вспомогательные схемы для ответа ---
class GranteeUser(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- Схема для ответа API со списком доступов ---
class ShareResponse(BaseModel):
    id: int
    permission_level: PermissionLevel
    grantee: GranteeUser

    class Config:
        from_attributes = True