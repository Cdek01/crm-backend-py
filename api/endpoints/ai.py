# api/endpoints/ai.py
from fastapi import APIRouter, Depends, Body
from typing import List, Dict, Any

from db import models
from api.deps import get_current_user
from services.eav_service import EAVService  # Нам нужен EAV для получения схемы таблицы
from services.ai_service import AIService
from pydantic import BaseModel

router = APIRouter()


class AIQueryRequest(BaseModel):
    query: str
    table_name: str


@router.post("/parse-filter")
def parse_filter_query(
        request: AIQueryRequest,
        current_user: models.User = Depends(get_current_user),
        eav_service: EAVService = Depends()
):
    """
    Принимает текстовый запрос и имя таблицы, возвращает JSON-фильтр.
    """
    # 1. Получаем "справку" (схему) для нужной таблицы
    entity_type = eav_service._get_entity_type_by_name(request.table_name, current_user)

    # Упрощаем схему для передачи в AI
    table_schema = [
        {
            "name": attr.name,
            "display_name": attr.display_name,
            "value_type": attr.value_type
        }
        for attr in entity_type.attributes
    ]

    # 2. Создаем AI-сервис и просим его разобрать запрос
    ai_service = AIService(current_user)
    filters = ai_service.parse_natural_language_to_filter(request.query, table_schema)

    return {"filters": filters}