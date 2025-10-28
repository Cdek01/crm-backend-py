# api/endpoints/imports.py
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
import logging

import pandas as pd
from pydantic import BaseModel

from db import models
from api.deps import get_current_user
from tasks.imports import process_file_import_task

# Получаем логгер
logger = logging.getLogger(__name__)

router = APIRouter()

# Создаем папку для временного хранения файлов
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ColumnMapping(BaseModel):
    original_header: str
    display_name: str
    value_type: str
    do_import: bool


class ImportProcessRequest(BaseModel):
    new_table_name: str
    new_table_display_name: str
    columns: List[ColumnMapping]


@router.post("/upload")
async def upload_file_for_import(
    file: UploadFile = File(...),
    delimiter: str = ',',
    current_user: models.User = Depends(get_current_user)
):
    """
    Шаг 1: Загрузка файла.
    Сохраняет файл, анализирует заголовки и первые 5 строк.
    """
    file_path = None  # Инициализируем переменную
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if file_extension.lower() == '.csv':
            df_preview = pd.read_csv(file_path, sep=delimiter or None, engine='python', nrows=5)
        elif file_extension.lower() in ['.xlsx', '.xls']:
            df_preview = pd.read_excel(file_path, nrows=5)
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла. Используйте CSV или Excel.")

        # --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
        # Заменяем все значения NaN на None, который корректно преобразуется в JSON 'null'
        df_preview_cleaned = df_preview.where(pd.notna(df_preview), None)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        headers = df_preview_cleaned.columns.tolist()
        preview_data = df_preview_cleaned.to_dict(orient='records')

        return {
            "file_id": unique_filename,
            "headers": headers,
            "preview_data": preview_data
        }
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        # Улучшаем вывод ошибок для отладки
        logger.error(f"Ошибка при загрузке файла: {e}", exc_info=True)
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

    task = process_file_import_task.delay(
        file_path=file_path,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        import_config=config.model_dump()
    )

    return {"message": "Импорт запущен в фоновом режиме.", "task_id": task.id}