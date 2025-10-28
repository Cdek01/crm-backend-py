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
    audio = "audio"



# --- Схемы для Атрибутов ('колонок') ---
class AttributeBase(BaseModel):
    name: str
    display_name: str
    value_type: ValueTypeEnum




class AttributeCreate(BaseModel):
    name: str
    display_name: str
    value_type: ValueTypeEnum  # Должен быть "relation" для этого сценария
    # --- ДОБАВЬТЕ ЭТО ПОЛЕ ---
    allow_multiple_selection: Optional[bool] = False
    # ---------------------------
    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    # Поля для основной (прямой) связи. Теперь они могут приходить сразу при создании.

    target_entity_type_id: Optional[int] = None
    source_attribute_id: Optional[int] = None  # Это поле нам пока не нужно для двусторонней связи
    target_attribute_id: Optional[int] = None  # И это
    display_attribute_id: Optional[int] = None

    # Поля для создания ОБРАТНОЙ связи
    create_back_relation: Optional[bool] = False  # Флаг "Создать обратную связь"
    back_relation_name: Optional[str] = None  # Системное имя для обратной колонки (например, "project")
    back_relation_display_name: Optional[str] = None  # Отображаемое имя ("Проект")
    back_relation_display_attribute_id: Optional[int] = None

    # Эти поля остаются
    select_list_id: Optional[int] = None
    formula_text: Optional[str] = None
    currency_symbol: Optional[str] = None
    list_items: Optional[List[str]] = None

class Attribute(AttributeBase):
    id: int
    entity_type_id: int
    # --- ДОБАВЬТЕ ЭТО ПОЛЕ ---
    allow_multiple_selection: bool
    # ---------------------------
    select_list_id: Optional[int] = None
    formula_text: Optional[str] = None
    currency_symbol: Optional[str] = None
    target_entity_type_id: Optional[int] = None
    source_attribute_id: Optional[int] = None
    target_attribute_id: Optional[int] = None
    display_attribute_id: Optional[int] = None
    back_relation_display_attribute_id: Optional[int] = None  # Это поле у вас уже должно быть

    # --- ДОБАВЬТЕ ЭТУ СТРОКУ ---
    reciprocal_attribute_id: Optional[int] = None
    # ---------------------------

    model_config = ConfigDict(from_attributes=True)


    @field_validator('value_type', mode='before')
    @classmethod
    def validate_value_type(cls, v):
        """
        Принимает строку из БД (например, "string") и преобразует
        ее в член Enum (ValueTypeEnum.string) перед валидацией.
        """
        if isinstance(v, str):
            try:
                return ValueTypeEnum(v)
            except ValueError:
                # Если пришел неизвестный тип, оставляем как есть,
                # чтобы Pydantic сам выдал ошибку.
                return v
        return v


class AttributeUpdate(BaseModel):
    display_name: Optional[str] = None
    formula_text: Optional[str] = None
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