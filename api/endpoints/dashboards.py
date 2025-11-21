# api/endpoints/dashboards.py
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Optional, Any

from db import models
from api.deps import get_current_user
from celery.result import AsyncResult
from celery_worker import celery_app
from tasks.analytics import generate_dashboard_summary_task

router = APIRouter()


class GenerateTaskResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None


@router.post("/summary/generate", response_model=GenerateTaskResponse, status_code=status.HTTP_202_ACCEPTED)
def start_summary_generation(current_user: models.User = Depends(get_current_user)):
    """
    Запускает фоновую задачу по генерации AI-сводки для дашборда.
    Мгновенно возвращает ID задачи.
    """
    task = generate_dashboard_summary_task.delay(user_id=current_user.id)
    return {"task_id": task.id}


@router.get("/summary/status/{task_id}", response_model=TaskStatusResponse)
def get_summary_status(task_id: str):
    """
    Проверяет статус задачи по ее ID.
    Возвращает статус (PENDING, SUCCESS, FAILURE) и результат, если он готов.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    result = task_result.result
    if task_result.failed():
        # Если задача упала с ошибкой, результат может быть объектом исключения
        result = str(task_result.result)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": result
    }