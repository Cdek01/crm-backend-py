# schemas/eav.py
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


# Используем Enum для строгой типизации полей
class ValueTypeEnum(str, Enum):
    string = "string"
    integer = "integer"
    float = "float"
    date = "date"
    boolean = "boolean"


# --- Схемы для Атрибутов ('колонок') ---
class AttributeBase(BaseModel):
    name: str
    display_name: str
    value_type: ValueTypeEnum


class AttributeCreate(AttributeBase):
    pass


class Attribute(AttributeBase):
    id: int
    entity_type_id: int

    class Config:
        from_attributes = True


# --- Схемы для Типов Сущностей ('таблиц') ---
class EntityTypeBase(BaseModel):
    name: str
    display_name: str


class EntityTypeCreate(EntityTypeBase):
    pass


class EntityType(EntityTypeBase):
    id: int
    attributes: List[Attribute] = []

    class Config:
        from_attributes = True