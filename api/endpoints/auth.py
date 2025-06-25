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
    # Проверяем, существует ли уже пользователь
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    # --- НОВАЯ ЛОГИКА ДЛЯ MULTI-TENANCY ---
    # 1. Создаем нового "клиента" (Tenant) для этого пользователя.
    # В реальном приложении имя может браться из формы регистрации.
    new_tenant = models.Tenant(name=f"Компания {user_in.full_name or user_in.email}")
    db.add(new_tenant)
    db.flush() # Используем flush, чтобы получить new_tenant.id до коммита

    # 2. Хешируем пароль и создаем пользователя, привязывая его к новому Tenant.
    hashed_password = security.get_password_hash(user_in.password)
    new_user = models.User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        tenant_id=new_tenant.id  # <-- ПРИВЯЗКА К КЛИЕНТУ
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