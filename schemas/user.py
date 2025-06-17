from pydantic import BaseModel, EmailStr
from typing import Optional

# Схема для получения данных при создании пользователя
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

# Схема для отображения пользователя (без пароля!)
class User(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True # Раньше называлось orm_mode