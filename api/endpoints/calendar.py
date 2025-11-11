# api/endpoints/calendar.py

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from datetime import date

from db import models
from api.deps import get_current_user
from services.calendar_service import CalendarService

router = APIRouter()

@router.get("/events/{view_id}", response_model=List[Dict[str, Any]])
def get_calendar_events(
    view_id: int,
    start: date = Query(..., description="Дата начала периода в формате YYYY-MM-DD"),
    end: date = Query(..., description="Дата окончания периода в формате YYYY-MM-DD"),
    service: CalendarService = Depends(),
    current_user: models.User = Depends(get_current_user)
):
    """
    Получает все события для указанного представления календаря в заданном диапазоне дат.
    Это основной эндпоинт, который будет использовать фронтенд для отрисовки календаря.
    """
    return service.get_events_for_view(view_id, start, end, current_user)