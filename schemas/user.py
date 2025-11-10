from pydantic import BaseModel, EmailStr
from typing import Optional, List

# Схема для получения данных при создании пользователя
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    registration_token: str


# Схема для отображения пользователя (без пароля!)
class User(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True # Раньше называлось orm_mode

class UserWithPermissions(User):
    permissions: List[str] = []


class PermissionInfo(BaseModel):
    name: str

    class Config:
        from_attributes = True

class RoleWithPermissionsInfo(BaseModel):
    name: str
    permissions: List[PermissionInfo]

    class Config:
        from_attributes = True

class UserAccessInfo(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_superuser: bool
    roles: List[RoleWithPermissionsInfo]
    # Добавляем итоговый список прав для удобства фронтенда
    effective_permissions: List[str]