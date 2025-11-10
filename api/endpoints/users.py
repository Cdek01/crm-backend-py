# api/endpoints/users.py

# --- Основные импорты ---
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from PIL import Image
from typing import IO

# --- Импорты из проекта ---
from db import models
from db.session import get_db
from sqlalchemy.orm import Session
from api.deps import get_current_user
from schemas.user import User as UserSchema

# --- НОВЫЕ ИМПОРТЫ для эндпоинта /me ---
from schemas.user import UserWithPermissions
from sqlalchemy.orm import joinedload

# ------------------------------------


router = APIRouter()

# --- Настройки для аватаров ---
AVATAR_UPLOAD_DIR = "static/avatars"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
AVATAR_SIZE = (256, 256)

os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)


# ===================================================================
# ЭНДПОИНТ ДЛЯ ПОЛУЧЕНИЯ ИНФОРМАЦИИ О ТЕКУЩЕМ ПОЛЬЗОВАТЕЛЕ
# ===================================================================

# Обратите внимание: URL теперь просто "/me"
# Полный URL будет /api/users/me, так как префикс /api/users задается в main.py
@router.get("/me", response_model=UserWithPermissions)
def read_users_me(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить информацию о текущем пользователе, включая его аватар и права доступа.
    """
    # Загружаем пользователя со всеми его ролями и правами этих ролей
    user_with_roles = (
        db.query(models.User)
        .options(
            joinedload(models.User.roles).
            joinedload(models.Role.permissions)
        )
        .filter(models.User.id == current_user.id)
        .first()
    )

    if not user_with_roles:
        response_user = UserWithPermissions.model_validate(current_user)
        response_user.permissions = []
        return response_user

    # Собираем все уникальные имена разрешений
    user_permissions = {perm.name for role in user_with_roles.roles for perm in role.permissions}

    response_user = UserWithPermissions.model_validate(user_with_roles)
    response_user.permissions = sorted(list(user_permissions))

    return response_user


# ===================================================================
# ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ АВАТАРОМ
# (Этот код остается без изменений)
# ===================================================================

def process_and_save_avatar(file: UploadFile, user_id: int) -> str:
    """
    Валидирует, обрабатывает (сжимает, обрезает) и сохраняет файл аватара.
    Возвращает относительный URL-путь к файлу.
    """
    extension = file.filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024}MB")

    try:
        image = Image.open(file.file)
        width, height = image.size
        new_edge = min(width, height)
        left, top = (width - new_edge) / 2, (height - new_edge) / 2
        right, bottom = (width + new_edge) / 2, (height + new_edge) / 2
        image = image.crop((left, top, right, bottom)).resize(AVATAR_SIZE, Image.Resampling.LANCZOS)

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        unique_filename = f"{user_id}_{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(AVATAR_UPLOAD_DIR, unique_filename)
        image.save(save_path, "JPEG", quality=85, optimize=True)

        return f"/{save_path.replace(os.path.sep, '/')}"  # Исправлено для корректной работы на разных ОС

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось обработать изображение: {e}")


@router.post("/me/avatar", response_model=UserSchema)
def upload_avatar(
        request: Request,
        avatar: UploadFile = File(...),
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Загрузить или обновить аватар текущего пользователя.
    """
    if current_user.avatar_url:
        # Пытаемся извлечь относительный путь из полного URL
        try:
            old_avatar_path = current_user.avatar_url.split(request.base_url._url)[1].lstrip('/')
            if os.path.exists(old_avatar_path):
                os.remove(old_avatar_path)
        except (OSError, IndexError):
            pass

    relative_path = process_and_save_avatar(avatar, current_user.id)

    # Формируем полный URL на основе запроса
    base_url = str(request.base_url)
    full_url = f"{base_url.rstrip('/')}{relative_path}"

    current_user.avatar_url = full_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user


@router.delete("/me/avatar", response_model=UserSchema)
def delete_avatar(
        request: Request,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Удалить аватар текущего пользователя.
    """
    if not current_user.avatar_url:
        return current_user

    try:
        relative_path = current_user.avatar_url.split(request.base_url._url)[1].lstrip('/')
        if os.path.exists(relative_path):
            os.remove(relative_path)
    except (OSError, IndexError):
        pass

    current_user.avatar_url = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/access-map", response_model=List[UserAccessInfo])
def get_all_user_access(
        db: Session = Depends(get_db),
        # Эта зависимость гарантирует, что эндпоинт доступен только суперадминистраторам
        current_user: models.User = Depends(get_current_user)
):
    """
    Получить полную карту доступов для всех пользователей.
    Доступно только для суперадминистраторов.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения этого действия.",
        )

    # 1. Загружаем всех пользователей с их ролями и правами этих ролей
    # Это один эффективный запрос к БД
    all_users = (
        db.query(models.User)
        .options(
            joinedload(models.User.roles)
            .joinedload(models.Role.permissions)
        )
        .order_by(models.User.id)
        .all()
    )

    # 2. Формируем красивый ответ
    response_list = []
    for user in all_users:
        # Собираем уникальные права для каждого пользователя
        user_permissions = {
            perm.name
            for role in user.roles
            for perm in role.permissions
        }

        # Создаем Pydantic-объект для ответа
        user_info = UserAccessInfo(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_superuser=user.is_superuser,
            roles=user.roles,  # Pydantic автоматически преобразует SQLAlchemy-объекты
            effective_permissions=sorted(list(user_permissions))
        )
        response_list.append(user_info)

    return response_list