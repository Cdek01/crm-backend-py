# schemas/eav.py
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from enum import Enum


# Используем Enum для строгой типизации полей
class ValueTypeEnum(str, Enum):
    string = "string"
    integer = "integer"
    float = "float"
    date = "date"
    boolean = "boolean"
    time = "time"
    select = "select"
    email = "email"
    phone = "phone"
    url = "url"
    percent = "percent"
    currency = "currency"
    multiselect = "multiselect"
    formula = "formula"
    relation = "relation"



# --- Схемы для Атрибутов ('колонок') ---
class AttributeBase(BaseModel):
    name: str
    display_name: str
    value_type: ValueTypeEnum




class AttributeCreate(BaseModel):
    name: str
    display_name: str
    value_type: ValueTypeEnum
    select_list_id: Optional[int] = None
    formula_text: Optional[str] = None
    currency_symbol: Optional[str] = None
    # --- ДОБАВЬТЕ ЭТИ ПОЛЯ ---
    target_entity_type_id: Optional[int] = None
    source_attribute_id: Optional[int] = None
    target_attribute_id: Optional[int] = None
    display_attribute_id: Optional[int] = None
    # ---------------------------
    list_items: Optional[List[str]] = None


class Attribute(AttributeBase):
    id: int
    entity_type_id: int

    # --- УБЕДИТЕСЬ, ЧТО ЭТИ ПОЛЯ ЗДЕСЬ ЕСТЬ ---
    select_list_id: Optional[int] = None
    formula_text: Optional[str] = None
    currency_symbol: Optional[str] = None
    target_entity_type_id: Optional[int] = None
    source_attribute_id: Optional[int] = None
    target_attribute_id: Optional[int] = None
    display_attribute_id: Optional[int] = None
    # ----------------------------------------

    model_config = ConfigDict(from_attributes=True)


    @field_validator('value_type', mode='before')
    @classmethod
    def validate_value_type(cls, v):
        """
        Этот валидатор будет принимать строку из базы данных (например, "string")
        и преобразовывать ее в член Enum (ValueTypeEnum.string) перед
        созданием Pydantic-модели.
        """
        if isinstance(v, str):
            return ValueTypeEnum(v)
        return v


class AttributeUpdate(BaseModel):
    display_name: Optional[str] = None
    target_entity_type_id: Optional[int] = None
    source_attribute_id: Optional[int] = None
    target_attribute_id: Optional[int] = None
    display_attribute_id: Optional[int] = None


# --- Схемы для Типов Сущностей ('таблиц') ---
class EntityTypeBase(BaseModel):
    name: str
    display_name: str


class EntityTypeCreate(EntityTypeBase):
    pass

# --- ДОБАВЬТЕ ЭТУ СХЕМУ ---
class EntityTypeUpdate(BaseModel):
    display_name: str
# --------------------------

class EntityType(EntityTypeBase):
    id: int
    attributes: List[Attribute] = []

    class Config:
        from_attributes = True


class AttributeOrderSetRequest(BaseModel):
    # Список ID атрибутов в новом, правильном порядке
    attribute_ids: List[int]


class EntityOrderSetRequest(BaseModel):
    # Список ID строк (сущностей) в новом, правильном порядке
    entity_ids: List[int]



class EntityOrderUpdateSmartRequest(BaseModel):
    entity_id: int # ID строки, которую переместили
    # Позиция строки, ПОСЛЕ которой нужно вставить (может быть None, если вставили в начало)
    after_position: Optional[float] = None
    # Позиция строки, ПЕРЕД которой нужно вставить (может быть None, если вставили в конец)
    before_position: Optional[float] = None