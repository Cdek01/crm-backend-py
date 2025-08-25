from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from db import models
from db.session import get_db
from schemas.user import UserCreate, User
from schemas.token import Token
from core import security
from core.config import settings

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):

    # --- НОВАЯ ЛОГИКА ПРОВЕРКИ ТОКЕНА ---
    # Это самая первая проверка. Если она не пройдена, дальше код не выполняется.
    if user_in.registration_token != settings.REGISTRATION_SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403 Forbidden - подходящий статус
            detail="Неверный токен регистрации",
        )
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    # Проверяем, существует ли уже пользователь (этот код остается без изменений)
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    # --- (остальной код создания пользователя и tenant'а остается без изменений) ---
    # new_tenant = models.Tenant(name=f"Компания {user_in.full_name or user_in.email}")
    new_tenant = models.Tenant(name=f"Компания {user_in.email}")

    db.add(new_tenant)
    db.flush()

    hashed_password = security.get_password_hash(user_in.password)
    new_user = models.User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        tenant_id=new_tenant.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}