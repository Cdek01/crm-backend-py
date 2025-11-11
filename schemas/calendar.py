# schemas/calendar.py

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import json

class CalendarViewConfigBase(BaseModel):
    name: str
    entity_type_id: int
    title_attribute_id: int
    start_date_attribute_id: int
    end_date_attribute_id: Optional[int] = None
    is_allday_attribute_id: Optional[int] = None
    color_attribute_id: Optional[int] = None
    color_settings: Optional[Dict[str, str]] = Field(default_factory=dict)
    filters: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    visible_fields: Optional[List[int]] = Field(default_factory=list)
    default_view: str = 'month'
    hide_weekends: bool = False

class CalendarViewConfigCreate(CalendarViewConfigBase):
    pass

class CalendarViewConfigUpdate(BaseModel):
    name: Optional[str] = None
    entity_type_id: Optional[int] = None
    title_attribute_id: Optional[int] = None
    start_date_attribute_id: Optional[int] = None
    end_date_attribute_id: Optional[int] = None
    is_allday_attribute_id: Optional[int] = None
    color_attribute_id: Optional[int] = None
    color_settings: Optional[Dict[str, str]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    visible_fields: Optional[List[int]] = None
    default_view: Optional[str] = None
    hide_weekends: Optional[bool] = None

class CalendarViewConfigResponse(CalendarViewConfigBase):
    id: int
    tenant_id: int

    class Config:
        from_attributes = True

    # Валидаторы для преобразования JSON-строк из БД в Python-объекты
    @field_validator('color_settings', 'filters', 'visible_fields', mode='before')
    @classmethod
    def parse_json_strings(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v # Возвращаем как есть, если не JSON, pydantic выдаст ошибку
        return v