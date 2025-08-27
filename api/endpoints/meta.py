# api/endpoints/meta.py
from fastapi import APIRouter, Depends, status
from typing import List

from db import models
from schemas.eav import EntityType, EntityTypeCreate, Attribute, AttributeCreate, EntityTypeUpdate, AttributeOrderSetRequest
from services.eav_service import EAVService
from api.deps import get_current_user


router = APIRouter()



@router.get("/entity-types", response_model=List[EntityType])
def get_all_entity_types(
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Получить список всех пользовательских типов сущностей ('таблиц').
    """
    return service.get_all_entity_types(current_user=current_user)


@router.get("/entity-types/{entity_type_id}", response_model=EntityType)
def get_entity_type(
    entity_type_id: int,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Получить детальную информацию о конкретном типе сущности по его ID,
    включая все его атрибуты ('колонки').
    """
    # Этот вызов теперь вернет объект с примененными псевдонимами
    return service.get_entity_type_by_id(entity_type_id=entity_type_id, current_user=current_user)




@router.delete("/entity-types/{entity_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity_type(
    entity_type_id: int,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Удалить пользовательский тип сущности ('таблицу').

    **ВНИМАНИЕ:** Это действие необратимо и приведет к удалению:
    - Самой 'таблицы' (типа сущности).
    - Всех ее 'колонок' (атрибутов).
    - Всех 'строк' (сущностей) внутри этой таблицы.
    - Всех данных в 'ячейках' (значений атрибутов).
    """
    return service.delete_entity_type(entity_type_id=entity_type_id, current_user=current_user)


# ...

@router.delete("/entity-types/{entity_type_id}/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attribute(
    entity_type_id: int,
    attribute_id: int,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Удалить атрибут ('колонку') из типа сущности.

    **ВНИМАНИЕ:** Это действие необратимо и приведет к удалению всех
    данных, сохраненных в этой 'колонке' для всех 'строк' данной таблицы.
    """
    return service.delete_attribute_from_type(
        entity_type_id=entity_type_id,
        attribute_id=attribute_id,
        current_user=current_user
    )



@router.post("/entity-types", response_model=EntityType, status_code=status.HTTP_201_CREATED)
def create_entity_type(
    entity_type_in: EntityTypeCreate,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user) # Эта зависимость у вас уже есть
):
    """Создать новый тип сущности (пользовательскую 'таблицу')."""
    # ИЗМЕНЕНИЕ: Передаем current_user в сервис
    return service.create_entity_type(entity_type_in=entity_type_in, current_user=current_user)

# ... остальные эндпоинты


@router.post("/entity-types/{entity_type_id}/attributes", response_model=Attribute, status_code=status.HTTP_201_CREATED)
def create_attribute(
    entity_type_id: int,
    attribute_in: AttributeCreate,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    return service.create_attribute_for_type(
        entity_type_id=entity_type_id,
        attribute_in=attribute_in,
        current_user=current_user # <-- Важный аргумент
    )

@router.put("/entity-types/{entity_type_id}", response_model=EntityType)
def update_entity_type(
    entity_type_id: int,
    entity_type_in: EntityTypeUpdate,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
    ):
    """
    Обновить отображаемое имя для типа сущности ('таблицы').
    """
    return service.update_entity_type(
    entity_type_id=entity_type_id,
    entity_type_in=entity_type_in,
    current_user=current_user
)



@router.post("/entity-types/{entity_type_id}/attributes/order", status_code=status.HTTP_200_OK)
def set_attribute_order(
    entity_type_id: int,
    order_in: AttributeOrderSetRequest,
    service: EAVService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    return service.set_attribute_order(
        entity_type_id=entity_type_id,
        attribute_ids=order_in.attribute_ids,
        current_user=current_user
    )





