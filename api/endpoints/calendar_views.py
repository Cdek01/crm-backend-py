# api/endpoints/calendar_views.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from db import models
from api.deps import get_current_user
from schemas.calendar import CalendarViewConfigCreate, CalendarViewConfigUpdate, CalendarViewConfigResponse
from services.calendar_service import CalendarService

router = APIRouter()


@router.post("/", response_model=CalendarViewConfigResponse, status_code=status.HTTP_201_CREATED)
def create_calendar_view(
        config_in: CalendarViewConfigCreate,
        service: CalendarService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Создать новое 'Представление типа Календарь' для таблицы.

    Принимает полную конфигурацию: название, ID таблицы, ID полей для заголовка, дат и т.д.
    """
    return service.create_config(config_in, current_user)


@router.get("/for-entity/{entity_type_id}", response_model=List[CalendarViewConfigResponse])
def get_views_for_entity(
        entity_type_id: int,
        service: CalendarService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Получить список всех настроенных представлений-календарей для одной конкретной таблицы.

    Это позволит фронтенду отобразить выпадающий список "Вид: Календарь по срокам", "Вид: Календарь по встречам".
    """
    return service.get_configs_for_entity(entity_type_id, current_user)


@router.get("/{view_id}", response_model=CalendarViewConfigResponse)
def get_view_details(
        view_id: int,
        service: CalendarService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Получить детальную информацию о конфигурации одного конкретного представления-календаря.

    Полезно для открытия окна настроек этого вида.
    """
    return service.get_config_by_id(view_id, current_user)


@router.put("/{view_id}", response_model=CalendarViewConfigResponse)
def update_calendar_view(
        view_id: int,
        config_in: CalendarViewConfigUpdate,
        service: CalendarService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Обновить настройки существующего представления-календаря.

    Например, поменять поле для раскраски или добавить/изменить сохраненные фильтры.
    """
    return service.update_config(view_id, config_in, current_user)


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_view(
        view_id: int,
        service: CalendarService = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    """
    Удалить представление-календарь.
    """
    service.delete_config(view_id, current_user)
    # Для статуса 204 тело ответа должно быть пустым
    return None