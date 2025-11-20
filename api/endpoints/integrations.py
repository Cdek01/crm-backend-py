# api/endpoints/integrations.py

from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Literal, List
from datetime import time, datetime
import requests
import json

from core.config import settings
from db import models, session
from api.deps import get_current_user
from core.encryption import encrypt_data
from tasks.banking import setup_schedule_for_tenant, sync_tenant_operations
from services.eav_service import EAVService
from services.banking_setup_service import setup_banking_table
# --- НАЧАЛО ИЗМЕНЕНИЙ: Новые импорты ---
from services.beeline_setup_service import setup_beeline_table
from tasks.beeline_sync import setup_schedule_for_beeline, sync_beeline_calls
# --- КОНЕЦ ИЗМЕНЕНИЙ ---

router = APIRouter()


# --- Схемы данных ---

class ModulbankIntegrationSettings(BaseModel):
    """Единая схема для сохранения всех настроек интеграции."""
    api_token: Optional[str] = Field(None, description="API-ключ. Отправляется только при изменении.")
    schedule_type: Literal['manual', 'hourly', 'daily', 'weekly'] = 'manual'
    sync_time: Optional[time] = None
    sync_weekday: Optional[int] = Field(None, ge=0, le=6)
    # Поля для выбора источников
    selected_company_ids: List[str] = []
    selected_account_ids: List[str] = []


class ModulbankIntegrationStatus(BaseModel):
    """Схема для отображения текущего статуса на фронтенде."""
    is_active: bool
    schedule_type: str
    sync_time: Optional[time] = None
    sync_weekday: Optional[int] = None
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    # Добавляем сохраненный выбор, чтобы фронтенд мог его отобразить
    selected_account_ids: List[str] = []


class BankAccount(BaseModel):
    id: str
    number: str
    currency: str
    balance: float


class CompanyInfo(BaseModel):
    companyId: str
    companyName: str
    bankAccounts: List[BankAccount]


class TokenValidateRequest(BaseModel):
    api_token: str

# --- Схемы данных для Билайн (добавьте их после схем для Modulbank) ---

class BeelineTokenValidateRequest(BaseModel):
    api_token: str

class BeelineIntegrationSettings(BaseModel):
    api_token: Optional[str] = Field(None, description="API-ключ. Отправляется только при изменении.")
    schedule_type: Literal['manual', 'hourly', 'daily', 'weekly'] = 'manual'
    sync_time: Optional[time] = None
    sync_weekday: Optional[int] = Field(None, ge=0, le=6)

class BeelineIntegrationStatus(BaseModel):
    is_active: bool
    schedule_type: str
    sync_time: Optional[time] = None
    sync_weekday: Optional[int] = None
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None












# --- Эндпоинты ---

@router.post("/modulbank/validate-token", response_model=List[CompanyInfo])
def validate_modulbank_token(token_in: TokenValidateRequest):
    """Принимает API-токен, проверяет его и возвращает список доступных компаний и счетов."""
    headers = {'Authorization': f'Bearer {token_in.api_token}'}
    try:
        response = requests.post("https://api.modulbank.ru/v1/account-info", headers=headers, timeout=10)
        response.raise_for_status()
        companies = [CompanyInfo.model_validate(c) for c in response.json()]
        return companies
    except requests.exceptions.RequestException as e:
        detail = f"Ошибка API Модульбанка: {e.response.text if e.response else e}"
        raise HTTPException(status_code=400, detail=detail)


@router.get("/modulbank/settings", response_model=ModulbankIntegrationStatus)
def get_modulbank_settings(db: Session = Depends(session.get_db), current_user: models.User = Depends(get_current_user)):
    """Получает текущие настройки и статус интеграции для отображения в профиле."""
    tenant = db.query(models.Tenant).get(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    selected_accounts = []
    if tenant.modulbank_sync_sources:
        try:
            sources = json.loads(tenant.modulbank_sync_sources)
            selected_accounts = sources.get("accounts", [])
        except json.JSONDecodeError:
            pass

    return ModulbankIntegrationStatus(
        is_active=(tenant.modulbank_integration_status == 'active'),
        schedule_type=tenant.modulbank_sync_schedule_type or 'manual',
        sync_time=tenant.modulbank_sync_time,
        sync_weekday=tenant.modulbank_sync_weekday,
        last_sync=tenant.modulbank_last_sync,
        last_error=tenant.modulbank_last_error,
        selected_account_ids=selected_accounts
    )


@router.post("/modulbank/settings", status_code=status.HTTP_200_OK)
def save_modulbank_settings(
        settings: ModulbankIntegrationSettings,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user),
        eav_service: EAVService = Depends()
):
    """Сохраняет все настройки интеграции: API-ключ, выбор счетов и расписание."""
    tenant = db.query(models.Tenant).get(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    message = "Настройки интеграции обновлены."

    if settings.api_token:
        try:
            setup_banking_table(db=db, eav_service=eav_service, current_user=current_user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Не удалось создать таблицу для банковских операций: {e}")

        tenant.modulbank_api_token = encrypt_data(settings.api_token)
        tenant.modulbank_integration_status = 'active'
        tenant.modulbank_last_error = None
        sync_tenant_operations.delay(tenant.id)
        message = "Интеграция с Модульбанком активирована. Первая синхронизация запущена."

    elif not tenant.modulbank_api_token:
        raise HTTPException(status_code=400, detail="Для активации интеграции необходимо предоставить API-ключ.")

    tenant.modulbank_sync_schedule_type = settings.schedule_type
    tenant.modulbank_sync_time = settings.sync_time
    tenant.modulbank_sync_weekday = settings.sync_weekday

    tenant.modulbank_sync_sources = json.dumps({
        "companies": settings.selected_company_ids,
        "accounts": settings.selected_account_ids
    })

    new_task_id = setup_schedule_for_tenant(tenant, db)
    tenant.modulbank_periodic_task_id = new_task_id

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
        raise HTTPException(status_code=4.04, detail="Клиент не найден")

    # 1. Вызываем функцию, которая найдет и удалит периодическую задачу из базы данных Celery
    setup_schedule_for_tenant(tenant, db, disable=True)

    # 2. Очищаем ВСЕ поля, связанные с интеграцией, в нашей таблице tenants
    tenant.modulbank_api_token = None
    tenant.modulbank_integration_status = 'inactive'
    tenant.modulbank_last_sync = None
    tenant.modulbank_last_error = None
    tenant.modulbank_sync_schedule_type = 'manual'  # Возвращаем к значению по умолчанию
    tenant.modulbank_sync_time = None
    tenant.modulbank_sync_weekday = None
    tenant.modulbank_periodic_task_id = None
    tenant.modulbank_sync_sources = None  # Очищаем выбор счетов

    # 3. Сохраняем изменения в базе данных
    db.commit()

    return {"status": "ok", "message": "Интеграция с Модульбанком отключена."}


# --- НАЧАЛО ИЗМЕНЕНИЙ: Новые эндпоинты для Билайн ---

@router.post("/beeline/validate-token", status_code=status.HTTP_200_OK)
def validate_beeline_token(token_in: BeelineTokenValidateRequest):
    """Принимает API-токен Билайн, проверяет его и возвращает статус."""
    headers = {'X-MPBX-API-AUTH-TOKEN': token_in.api_token}
    try:
        # Делаем простой запрос, чтобы проверить, работает ли токен
        response = requests.get(f"{settings.BEELINE_BASE_URL}/abonents", headers=headers, timeout=10)
        response.raise_for_status()
        return {"status": "ok", "message": "Токен действителен."}
    except requests.exceptions.RequestException as e:
        detail = f"Ошибка API Билайн: {e.response.text if e.response else e}"
        raise HTTPException(status_code=400, detail=detail)


@router.get("/beeline/settings", response_model=BeelineIntegrationStatus)
def get_beeline_settings(db: Session = Depends(session.get_db), current_user: models.User = Depends(get_current_user)):
    """Получает текущие настройки и статус интеграции с Билайн."""
    tenant = db.get(models.Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    return BeelineIntegrationStatus(
        is_active=(tenant.beeline_integration_status == 'active'),
        schedule_type=tenant.beeline_sync_schedule_type or 'manual',
        sync_time=tenant.beeline_sync_time,
        sync_weekday=tenant.beeline_sync_weekday,
        last_sync=tenant.beeline_last_sync,
        last_error=tenant.beeline_last_error,
    )


@router.post("/beeline/settings", status_code=status.HTTP_200_OK)
def save_beeline_settings(
        settings_in: BeelineIntegrationSettings,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user),
        eav_service: EAVService = Depends()
):
    """Сохраняет все настройки интеграции с Билайн: API-ключ и расписание."""
    tenant = db.get(models.Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    message = "Настройки интеграции обновлены."

    if settings_in.api_token:
        # Если пришел новый токен, создаем таблицу (если нужно) и активируем интеграцию
        try:
            setup_beeline_table(db=db, eav_service=eav_service, current_user=current_user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Не удалось создать таблицу для истории звонков: {e}")

        tenant.beeline_api_token = encrypt_data(settings_in.api_token)
        tenant.beeline_integration_status = 'active'
        tenant.beeline_last_error = None
        # Запускаем первую синхронизацию немедленно
        sync_beeline_calls.delay()
        message = "Интеграция с Билайн активирована. Первая синхронизация запущена."
    elif not tenant.beeline_api_token:
        raise HTTPException(status_code=400, detail="Для активации интеграции необходимо предоставить API-ключ.")

    # Обновляем настройки расписания
    tenant.beeline_sync_schedule_type = settings_in.schedule_type
    tenant.beeline_sync_time = settings_in.sync_time
    tenant.beeline_sync_weekday = settings_in.sync_weekday

    # Создаем/обновляем периодическую задачу в Celery Beat
    new_task_id = setup_schedule_for_beeline(tenant, db)
    tenant.beeline_periodic_task_id = new_task_id

    db.commit()
    return {"status": "ok", "message": message}


@router.delete("/beeline/settings", status_code=status.HTTP_200_OK)
def disconnect_beeline(
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """Полностью отключает интеграцию с Билайн."""
    tenant = db.get(models.Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    setup_schedule_for_beeline(tenant, db, disable=True)

    tenant.beeline_api_token = None
    tenant.beeline_integration_status = 'inactive'
    tenant.beeline_last_sync = None
    tenant.beeline_last_error = None
    tenant.beeline_sync_schedule_type = 'manual'
    tenant.beeline_sync_time = None
    tenant.beeline_sync_weekday = None
    tenant.beeline_periodic_task_id = None

    db.commit()
    return {"status": "ok", "message": "Интеграция с Билайн отключена."}
# --- КОНЕЦ ИЗМЕНЕНИЙ ---```
