# api/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from sqlalchemy.orm import joinedload
from db import models, session
from core.config import settings


# Эта строка указывает FastAPI, откуда брать токен для проверки
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
        db: Session = Depends(session.get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_data = TokenData(username=username) # Можно использовать для доп. валидации
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == username).first()
    if user is None:
        raise credentials_exception
    return user


def require_permission(permission_name: str):
    """
    Фабрика зависимостей. Проверяет, имеет ли пользователь разрешение.
    Суперадминистратор проходит любую проверку.
    """

    def permission_checker(current_user: models.User = Depends(get_current_user)):
        # --- ДОБАВЬТЕ ЭТУ ПРОВЕРКУ В САМОМ НАЧАЛЕ ---
        # Если пользователь - суперадминистратор, разрешаем доступ не глядя.
        if current_user.is_superuser:
            return True
        # -----------------------------------------------

        # Этот код выполнится только для обычных пользователей
        user_with_perms = (
            current_user.session.query(models.User)
            .options(joinedload(models.User.roles).joinedload(models.Role.permissions))
            .filter(models.User.id == current_user.id)
            .one()
        )

        user_permissions = {perm.name for role in user_with_perms.roles for perm in role.permissions}

        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения этого действия",
            )

        return True

    return permission_checker