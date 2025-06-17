# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from api.endpoints import auth, leads
from db import models, base, session
from core import security
from core.config import settings
from api.deps import get_current_user
from schemas.user import User # Этот импорт нужен для response_model

# Создаем таблицы в БД при первом запуске (если их нет)
base.Base.metadata.create_all(bind=session.engine)

app = FastAPI(title="CRM API")

# Подключаем роутер аутентификации
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(leads.router, prefix="/api/leads", tags=["leads"]) # <--- Добавьте эту строку


# --- Защита эндпоинтов ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(db: Session = Depends(session.get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == username).first()
    if user is None:
        raise credentials_exception
    return user


# --- Пример защищенного эндпоинта ---
# Эндпоинт /api/users/me теперь будет выглядеть так:
@app.get("/api/users/me", response_model=User, tags=["users"])
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/")
def read_root():
    return {"message": "Welcome to CRM API"}