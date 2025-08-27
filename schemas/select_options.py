# schemas/select_options.py
from pydantic import BaseModel
from typing import List, Optional


# --- Схемы для Опций (вариантов выбора) ---

class SelectOptionBase(BaseModel):
    value: str


class SelectOptionCreate(SelectOptionBase):
    pass


class SelectOptionUpdate(SelectOptionBase):
    pass


class SelectOption(SelectOptionBase):
    id: int

    class Config:
        from_attributes = True


# --- Схемы для Списков (контейнеров опций) ---

class SelectOptionListBase(BaseModel):
    name: str


class SelectOptionListCreate(SelectOptionListBase):
    pass


class SelectOptionListUpdate(SelectOptionListBase):
    pass


class SelectOptionList(SelectOptionListBase):
    id: int
    options: List[SelectOption] = []

    class Config:
        from_attributes = True