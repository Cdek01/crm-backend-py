# api/endpoints/history.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db import models, session
from api.deps import get_current_user
from services.eav_service import EAVService
from services.alias_service import AliasService
from services.history_service import HistoryService

router = APIRouter()

# Вспомогательная функция для инициализации сервисов
def get_history_service(db: Session = Depends(session.get_db)):
    # HistoryService требует EAVService, который в свою очередь требует AliasService
    alias_service = AliasService(db)
    eav_service = EAVService(db, alias_service)
    return HistoryService(db, eav_service)

@router.post("/undo", status_code=status.HTTP_200_OK)
def undo_last_action(
    current_user: models.User = Depends(get_current_user),
    history_service: HistoryService = Depends(get_history_service)
):
    """Отменяет последнее действие текущего пользователя."""
    return history_service.undo(current_user)

@router.post("/redo", status_code=status.HTTP_200_OK)
def redo_last_action(
    current_user: models.User = Depends(get_current_user),
    history_service: HistoryService = Depends(get_history_service)
):
    """Повторяет последнее отмененное действие текущего пользователя."""
    return history_service.redo(current_user)