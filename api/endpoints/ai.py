# api/endpoints/ai.py
from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from db import models
from api.deps import get_current_user
from services.eav_service import EAVService
from services.ai_service import AIService
from pydantic import BaseModel

router = APIRouter()


class AIQueryRequest(BaseModel):
    query: str
    table_name: str


# --- ИЗМЕНЕНИЕ: Эндпоинт теперь async def ---
@router.post("/parse-filter")
async def parse_filter_query(  # <-- Добавили async
        request: AIQueryRequest,
        current_user: models.User = Depends(get_current_user),
        eav_service: EAVService = Depends()
):
    """
    Принимает текстовый запрос и имя таблицы, возвращает JSON-фильтр.
    """
    entity_type = eav_service._get_entity_type_by_name(request.table_name, current_user)

    table_schema = [
        {"name": attr.name, "display_name": attr.display_name, "value_type": attr.value_type}
        for attr in entity_type.attributes
    ]

    ai_service = AIService(current_user)
    # --- ИЗМЕНЕНИЕ: Добавили await ---
    filters = await ai_service.parse_natural_language_to_filter(request.query, table_schema)

    return {"filters": filters}