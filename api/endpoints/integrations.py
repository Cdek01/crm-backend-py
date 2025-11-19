# api/endpoints/integrations.py

from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import time, datetime

# --- Импорты из проекта ---
from db import models, session
from api.deps import get_current_user
from core.encryption import encrypt_data, decrypt_data
from tasks.banking import setup_schedule_for_tenant, sync_tenant_operations

router = APIRouter()


# --- Новая, объединенная Pydantic-схема ---

class ModulbankIntegrationSettings(BaseModel):
    """Схема для получения и сохранения всех настроек интеграции."""
    api_token: Optional[str] = Field(None,
                                     description="API-ключ. Отправляется только при сохранении, скрывается при получении.")
    schedule_type: Literal['manual', 'hourly', 'daily', 'weekly'] = 'manual'
    sync_time: Optional[time] = Field(None, description="Время для ежедневной/еженедельной синхронизации.")
    sync_weekday: Optional[int] = Field(None, ge=0, le=6,
                                        description="День недели для еженедельной синхронизации (0=Пн).")


class ModulbankIntegrationStatus(BaseModel):
    """Схема для отображения текущего статуса на фронтенде."""
    is_active: bool
    schedule_type: str
    sync_time: Optional[time] = None
    sync_weekday: Optional[int] = None
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None


# --- Новые, объединенные эндпоинты ---

@router.get("/modulbank/settings", response_model=ModulbankIntegrationStatus)
def get_modulbank_settings(
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Получает текущие настройки и статус интеграции с Модульбанком для отображения в профиле.
    """
    tenant = db.query(models.Tenant).get(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    return ModulbankIntegrationStatus(
        is_active=(tenant.modulbank_integration_status == 'active'),
        schedule_type=tenant.modulbank_sync_schedule_type or 'manual',
        sync_time=tenant.modulbank_sync_time,
        sync_weekday=tenant.modulbank_sync_weekday,
        last_sync=tenant.modulbank_last_sync,
        last_error=tenant.modulbank_last_error
    )


@router.post("/modulbank/settings", status_code=status.HTTP_200_OK)
def save_modulbank_settings(
        settings: ModulbankIntegrationSettings,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Сохраняет все настройки интеграции: API-ключ и расписание.
    """
    tenant = db.query(models.Tenant).get(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # --- Обновление API-ключа ---
    if settings.api_token:
        # Если пришел новый токен, шифруем и сохраняем его
        tenant.modulbank_api_token = encrypt_data(settings.api_token)
        tenant.modulbank_integration_status = 'active'
        tenant.modulbank_last_error = None  # Сбрасываем старые ошибки

        # Запускаем первую синхронизацию сразу после ввода нового ключа
        sync_tenant_operations.delay(tenant.id)
        message = "Интеграция с Модульбанком активирована. Первая синхронизация запущена."
    elif not tenant.modulbank_api_token:
        # Если токен не пришел и его не было раньше, интеграцию активировать нельзя
        raise HTTPException(status_code=400, detail="Для активации интеграции необходимо предоставить API-ключ.")
    else:
        message = "Расписание синхронизации обновлено."

    # --- Обновление расписания ---
    tenant.modulbank_sync_schedule_type = settings.schedule_type
    tenant.modulbank_sync_time = settings.sync_time
    tenant.modulbank_sync_weekday = settings.sync_weekday

    # Вызываем функцию, которая обновит расписание в таблицах Celery Beat
    new_task_id = setup_schedule_for_tenant(tenant, db) # <-- Добавляем 'db'
    tenant.modulbank_periodic_task_id = new_task_id  # Сохраняем ID новой задачи

    db.commit()
    return {"status": "ok", "message": message}


@router.delete("/modulbank/settings", status_code=status.HTTP_200_OK)
def disconnect_modulbank(
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Полностью отключает интеграцию, удаляет токен и расписание.
    """
    tenant = db.query(models.Tenant).get(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Удаляем задачу из расписания Celery Beat
    setup_schedule_for_tenant(tenant, db, disable=True)

    # Очищаем все поля в нашей БД
    tenant.modulbank_api_token = None
    tenant.modulbank_integration_status = 'inactive'
    tenant.modulbank_last_sync = None
    tenant.modulbank_last_error = None
    tenant.modulbank_sync_schedule_type = 'manual'
    tenant.modulbank_sync_time = None
    tenant.modulbank_sync_weekday = None
    tenant.modulbank_periodic_task_id = None

    db.commit()
    return {"status": "ok", "message": "Интеграция с Модульбанком отключена."}