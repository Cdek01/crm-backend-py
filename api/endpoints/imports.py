# api/endpoints/imports.py
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
import logging
import numpy as np # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ В НАЧАЛЕ ФАЙЛА

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


def infer_column_type(series: pd.Series) -> str:
    """
    "Умная" функция, которая пытается определить тип данных для колонки (серии pandas).
    """
    # 1. Убираем пустые значения, они не должны влиять на определение типа
    series = series.dropna()
    if series.empty:
        return "string"  # Если все значения пустые, считаем строкой

    # 2. Попытка преобразования в число
    try:
        numeric_series = pd.to_numeric(series)
        # Если все числа целые, то это integer
        if (numeric_series == numeric_series.astype(int)).all():
            return "integer"
        else:
            return "float"  # Иначе - float
    except (ValueError, TypeError):
        pass  # Не получилось, идем дальше

    # 3. Попытка преобразования в дату
    try:
        # errors='coerce' превратит не-даты в NaT (Not a Time)
        date_series = pd.to_datetime(series, errors='coerce')
        # Если после преобразования не осталось пустых значений, значит все было датами
        if date_series.notna().all():
            return "date"
    except (ValueError, TypeError):
        pass

    # 4. Попытка преобразования в boolean
    # Проверяем, похожи ли все значения на True/False
    bool_values = {'true', 'false', '1', '0', 'yes', 'no', 'да', 'нет'}
    if series.str.lower().isin(bool_values).all():
        return "boolean"

    # 5. Если ничего не подошло - это строка
    return "string"


@router.post("/upload")
async def upload_file_for_import(
        file: UploadFile = File(...),
        delimiter: str = ',',
        current_user: models.User = Depends(get_current_user)
):
    """
    Шаг 1: Загрузка файла.
    Сохраняет файл, "умно" анализирует заголовки и типы, возвращает превью.
    """
    file_path = None
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Читаем сэмпл файла для анализа (например, 200 строк)
        # dtype=str гарантирует, что pandas не будет угадывать типы сам на этом этапе
        if file_extension.lower() == '.csv':
            df_sample = pd.read_csv(file_path, sep=delimiter or None, engine='python', nrows=200, keep_default_na=False)
        elif file_extension.lower() in ['.xlsx', '.xls']:
            df_sample = pd.read_excel(file_path, nrows=200, keep_default_na=False)
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла. Используйте CSV или Excel.")

        # --- НОВАЯ ЛОГИКА АНАЛИЗА ---
        headers_with_types = []
        for header in df_sample.columns:
            inferred_type = infer_column_type(df_sample[header])
            headers_with_types.append({
                "original_header": header,
                "suggested_type": inferred_type
            })

        # Готовим превью данных
        df_preview = df_sample.head(5).replace({np.nan: None})
        preview_data = df_preview.to_dict(orient='records')

        return {
            "file_id": unique_filename,
            "headers": headers_with_types,  # <-- Теперь возвращаем список объектов
            "preview_data": preview_data
        }
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        logger.error(f"Ошибка при загрузке и анализе файла: {e}", exc_info=True)
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