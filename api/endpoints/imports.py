# api/endpoints/imports.py
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
import logging

import pandas as pd
from pydantic import BaseModel
import numpy as np
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


# Убедитесь, что эта вспомогательная функция тоже есть в файле, НАД @router.post("/upload")
def infer_column_type(series: pd.Series) -> str:
    """
    "Умная" функция, которая пытается определить тип данных для колонки (серии pandas).
    """
    # 1. Убираем пустые значения и строки из пробелов
    series_cleaned = series.loc[series.astype(str).str.strip() != ''].dropna()
    if series_cleaned.empty:
        return "string"

    # 2. Попытка преобразования в число
    try:
        numeric_series = pd.to_numeric(series_cleaned)
        if (numeric_series % 1 == 0).all():  # Проверяем, все ли числа целые
            return "integer"
        else:
            return "float"
    except (ValueError, TypeError):
        pass

    # 3. Попытка преобразования в дату
    try:
        # errors='coerce' превратит не-даты в NaT (Not a Time)
        date_series = pd.to_datetime(series_cleaned, errors='coerce')
        if date_series.notna().all():
            return "date"
    except (ValueError, TypeError):
        pass

    # 4. Попытка преобразования в boolean
    bool_values = {'true', 'false', '1', '0', 'yes', 'no', 'да', 'нет'}
    if all(str(val).lower() in bool_values for val in series_cleaned):
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
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Читаем сэмпл файла, позволяя pandas сделать первичное определение типов
        if file_extension == '.csv':
            df_sample = pd.read_csv(file_path, sep=delimiter or None, engine='python', nrows=200, keep_default_na=False)
        elif file_extension in ['.xlsx', '.xls']:
            df_sample = pd.read_excel(file_path, nrows=200, keep_default_na=False)
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла. Используйте CSV или Excel.")

        # Анализируем каждую колонку для определения предполагаемого типа
        headers_with_types = []
        for header in df_sample.columns:
            inferred_type = infer_column_type(df_sample[header])
            headers_with_types.append({
                "original_header": header,
                "suggested_type": inferred_type
            })

        # Готовим превью данных: берем 5 строк и заменяем NaN/NaT на None для JSON
        df_preview_cleaned = df_sample.head(5).replace({np.nan: None, pd.NaT: None})
        preview_data = df_preview_cleaned.to_dict(orient='records')

        return {
            "file_id": unique_filename,
            "headers": headers_with_types,
            "preview_data": preview_data
        }
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        logger.error(f"Ошибка при загрузке и анализе файла: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")
# @router.post("/upload")
# async def upload_file_for_import(
#         file: UploadFile = File(...),
#         delimiter: str = ',',
#         current_user: models.User = Depends(get_current_user)
# ):
#     """
#     Шаг 1: Загрузка файла.
#     Сохраняет файл, анализирует заголовки и первые 5 строк.
#     """
#     file_path = None
#     try:
#         file_extension = os.path.splitext(file.filename)[1]
#         unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
#         file_path = os.path.join(UPLOAD_DIR, unique_filename)
#
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#
#         if file_extension.lower() == '.csv':
#             df_preview = pd.read_csv(file_path, sep=delimiter or None, engine='python', nrows=5)
#         elif file_extension.lower() in ['.xlsx', '.xls']:
#             df_preview = pd.read_excel(file_path, nrows=5)
#         else:
#             raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла. Используйте CSV или Excel.")
#
#         # --- НАЧАЛО ОТЛАДОЧНОГО БЛОКА ---
#         print("\n" + "=" * 20 + " DEBUG INFO " + "=" * 20)
#         print("--- DataFrame ДО очистки ---")
#         print(df_preview)
#         print("--- Типы данных ДО очистки ---")
#         print(df_preview.dtypes)
#         print("-" * 52)
#
#         # Заменяем все значения NaN на None
#         df_preview_cleaned = df_preview.replace({np.nan: None})
#
#         print("--- DataFrame ПОСЛЕ очистки ---")
#         print(df_preview_cleaned)
#         print("--- Типы данных ПОСЛЕ очистки ---")
#         print(df_preview_cleaned.dtypes)
#         print("=" * 52 + "\n")
#         # --- КОНЕЦ ОТЛАДОЧНОГО БЛОКА ---
#
#         headers = df_preview_cleaned.columns.tolist()
#         preview_data = df_preview_cleaned.to_dict(orient='records')
#
#         return {
#             "file_id": unique_filename,
#             "headers": headers,
#             "preview_data": preview_data
#         }
#     except Exception as e:
#         if file_path and os.path.exists(file_path):
#             os.remove(file_path)
#
#         logger.error(f"Ошибка при загрузке файла: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")


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