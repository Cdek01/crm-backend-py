# api/endpoints/imports.py
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body
from typing import List, Dict, Any

import pandas as pd
from pydantic import BaseModel

from db import models
from api.deps import get_current_user
from tasks.imports import process_file_import_task # Мы создадим это в следующем шаге

router = APIRouter()

# Создаем папку для временного хранения файлов
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ColumnMapping(BaseModel):
    original_header: str
    display_name: str
    value_type: str # 'string', 'integer', 'float', 'date', etc.
    do_import: bool


class ImportProcessRequest(BaseModel):
    new_table_name: str
    new_table_display_name: str
    columns: List[ColumnMapping]


@router.post("/upload")
async def upload_file_for_import(
    file: UploadFile = File(...),
    delimiter: str = ',', # Позволяем фронтенду указать разделитель
    current_user: models.User = Depends(get_current_user)
):
    """
    Шаг 1: Загрузка файла.
    Сохраняет файл, анализирует заголовки и первые 5 строк.
    """
    try:
        # Генерируем уникальное имя файла, чтобы избежать конфликтов
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Сохраняем файл на диск
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Используем pandas для анализа
        if file_extension.lower() == '.csv':
            # sep=None и engine='python' для автоопределения разделителя, если он не указан
            df_preview = pd.read_csv(file_path, sep=delimiter if delimiter else None, engine='python', nrows=5)
        elif file_extension.lower() in ['.xlsx', '.xls']:
            df_preview = pd.read_excel(file_path, nrows=5)
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла. Используйте CSV или Excel.")

        headers = df_preview.columns.tolist()
        # Преобразуем preview DataFrame в формат JSON
        preview_data = df_preview.head().to_dict(orient='records')

        return {
            "file_id": unique_filename,
            "headers": headers,
            "preview_data": preview_data
        }
    except Exception as e:
        # В случае ошибки удаляем файл, если он был создан
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")


@router.post("/process/{file_id}")
def process_import(
    file_id: str,
    config: ImportProcessRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Шаг 2: Запуск импорта.
    Принимает конфигурацию от пользователя и запускает фоновую задачу.
    """
    file_path = os.path.join(UPLOAD_DIR, file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл для импорта не найден. Возможно, сессия истекла.")

    # Запускаем фоновую задачу Celery
    task = process_file_import_task.delay(
        file_path=file_path,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        import_config=config.model_dump() # Передаем конфигурацию как словарь
    )

    return {"message": "Импорт запущен в фоновом режиме.", "task_id": task.id}