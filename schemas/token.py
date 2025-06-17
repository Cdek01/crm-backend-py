# schemas/token.py
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Добавьте этот класс ---
class TokenData(BaseModel):
    """
    Схема для данных, которые хранятся внутри JWT токена.
    """
    username: Optional[str] = None