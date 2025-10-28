# api/endpoints/files.py
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from db import models
from api.deps import get_current_user

router = APIRouter()

# Путь к папке, куда будут сохраняться аудиофайлы
AUDIO_UPLOAD_DIR = os.path.join("static", "uploads", "audio")
os.makedirs(AUDIO_UPLOAD_DIR, exist_ok=True)


@router.post("/upload/audio")
async def upload_audio_file(
        file: UploadFile = File(...),
        current_user: models.User = Depends(get_current_user)
):
    """
    Принимает аудиофайл, сохраняет его на сервере с уникальным именем
    и возвращает относительный URL-путь для сохранения в базе данных.
    """
    # Проверка типа файла (опционально, но рекомендуется)
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Недопустимый тип файла. Загрузите аудиофайл.")

    try:
        file_extension = os.path.splitext(file.filename)[1]
        # Генерируем уникальное имя, чтобы избежать перезаписи файлов
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        file_path = os.path.join(AUDIO_UPLOAD_DIR, unique_filename)

        # Сохраняем файл на диск
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Формируем путь, который будет использоваться в URL
        # Например: /static/uploads/audio/xxxxxxxx.mp3
        url_path = f"/{file_path.replace(os.path.sep, '/')}"

        return {"url_path": url_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}")