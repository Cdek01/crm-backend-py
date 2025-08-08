# main.py

# --- ШАГ 1: ОСНОВНЫЕ ИМПОРТЫ ---
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

# --- ШАГ 2: ИМПОРТЫ ИЗ ВАШЕГО ПРОЕКТА ---
# Модули для работы с БД и конфигурацией
from db import models, base, session

# Схемы и зависимости для API
from schemas.user import User
from api.deps import get_current_user

# Роутеры для всех ваших API эндпоинтов
from api.endpoints import auth, leads, legal_entities, individuals, meta, data, aliases

# Модули для админ-панели
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from admin import (
    TenantAdmin, UserAdmin, LeadAdmin, LegalEntityAdmin,
    IndividualAdmin, EntityTypeAdmin, AttributeAdmin, AttributeAliasAdmin, TableAliasAdmin,
    RoleAdmin, PermissionAdmin
)

# --------------------------------------------------------------------------
# --- ШАГ 3: ИНИЦИАЛИЗАЦИЯ БД И ПРИЛОЖЕНИЯ ---
# --------------------------------------------------------------------------

# Создаем таблицы в БД при первом запуске (если их нет)
base.Base.metadata.create_all(bind=session.engine)

# Создаем главный экземпляр FastAPI ОДИН РАЗ
app = FastAPI(title="CRM API")


# --------------------------------------------------------------------------
# --- ШАГ 4: НАСТРОЙКА MIDDLEWARE (ПОСРЕДНИКОВ) ---
# Важно: Middleware добавляются до роутеров и админки
# --------------------------------------------------------------------------

# Настройка CORS для разрешения запросов от фронтенда
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для сессий, необходимых для аутентификации в админке
app.add_middleware(
    SessionMiddleware,
    secret_key="a_very_long_and_secret_string_for_sessions",
    session_cookie="admin_session_cookie"  # Уникальное имя для cookie админки
)


# --------------------------------------------------------------------------
# --- ШАГ 5: НАСТРОЙКА И РЕГИСТРАЦИЯ АДМИН-ПАНЕЛИ ---
# --------------------------------------------------------------------------

# Класс для кастомной аутентификации в админ-панели
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # ВАЖНО: Это только для разработки.
        # В реальном приложении здесь должна быть проверка пользователя в БД и сравнение хешей паролей.
        if username == "admin" and password == "supersecret":
            request.session.update({"token": "admin_logged_in"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        # Проверяем, есть ли наш маркер в сессии, установленный после успешного логина
        return "token" in request.session

# Создаем экземпляр бэкенда аутентификации
authentication_backend = AdminAuth(secret_key="a_very_secret_key_for_auth_backend")
# Создаем экземпляр админки и "прикрепляем" его к нашему приложению и движку БД
admin = Admin(app=app, engine=session.engine, authentication_backend=authentication_backend)

# Регистрируем все представления моделей, которые хотим видеть в админке
admin.add_view(TenantAdmin)
admin.add_view(UserAdmin)
admin.add_view(LeadAdmin)
admin.add_view(LegalEntityAdmin)
admin.add_view(IndividualAdmin)
admin.add_view(EntityTypeAdmin)
admin.add_view(AttributeAdmin)
admin.add_view(AttributeAliasAdmin)
admin.add_view(TableAliasAdmin)
admin.add_view(RoleAdmin)
admin.add_view(PermissionAdmin)
# Если вы создали AttributeAliasAdmin, раскомментируйте следующую строку
# admin.add_view(AttributeAliasAdmin)


# --------------------------------------------------------------------------
# --- ШАГ 6: ПОДКЛЮЧЕНИЕ API-РОУТЕРОВ ---
# --------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(legal_entities.router, prefix="/api/legal-entities", tags=["Legal Entities"])
app.include_router(individuals.router, prefix="/api/individuals", tags=["Individuals"])
app.include_router(aliases.router, prefix="/api/aliases", tags=["Aliases"])
app.include_router(meta.router, prefix="/api/meta", tags=["Meta (Constructor)"])
app.include_router(data.router, prefix="/api/data", tags=["Data (Custom)"])


# --------------------------------------------------------------------------
# --- ШАГ 7: ГЛОБАЛЬНЫЕ ЭНДПОИНТЫ (если нужны) ---
# --------------------------------------------------------------------------

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to CRM API"}

@app.get("/api/users/me", response_model=User, tags=["Users"])
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user