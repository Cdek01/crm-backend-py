# main.py

# --- ШАГ 1: ОСНОВНЫЕ ИМПОРТЫ ---
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqladmin import BaseView, expose
import os
from fastapi.staticfiles import StaticFiles  # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ

# --- ШАГ 2: ИМПОРТЫ ИЗ ВАШЕГО ПРОЕКТА ---
# Модули для работы с БД и конфигурацией
from db import models, base, session

# Роутеры для всех ваших API эндпоинтов
from api.endpoints import auth, meta, data, aliases, select_lists
from starlette.templating import Jinja2Templates
from core.logging_config import setup_logging

# Модули для админ-панели
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from admin import (
    TenantAdmin, UserAdmin, EntityTypeAdmin, AttributeAdmin, AttributeAliasAdmin, TableAliasAdmin,
    RoleAdmin, PermissionAdmin,
    AssignRoleView, SharedAccessAdmin

)
from api.endpoints import roles, imports, files, ai, users, shares, calendar_views, calendar, integrations, dashboards

setup_logging()

# --------------------------------------------------------------------------
# --- ШАГ 3: ИНИЦИАЛИЗАЦИЯ БД И ПРИЛОЖЕНИЯ ---
# --------------------------------------------------------------------------

# Создаем таблицы в БД при первом запуске (если их нет)
base.Base.metadata.create_all(bind=session.engine)


# Создаем директорию для хранения загруженных файлов, если ее нет
STATIC_DIR = "static"
AVATAR_DIR = os.path.join(STATIC_DIR, "avatars")

UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
# ---------------------------

# Создаем главный экземпляр FastAPI ОДИН РАЗ
app = FastAPI(title="CRM API")

# --- ИЗМЕНЕНИЕ: Настройка раздачи статических файлов ---
# Эта строка делает файлы из папки 'static' доступными по URL /static/...
# Например, файл static/avatars/user_1.jpg будет доступен по адресу http://.../static/avatars/user_1.jpg
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
# --------------------------------------------------------

templates = Jinja2Templates(directory="templates")

# --------------------------------------------------------------------------
# --- ШАГ 4: НАСТРОЙКА MIDDLEWARE (ПОСРЕДНИКОВ) ---
# Важно: Middleware добавляются до роутеров и админки
# --------------------------------------------------------------------------

# Настройка CORS для разрешения запросов от фронтенда
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "https://srm-ruddy.vercel.app",
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

app.include_router(roles.router, prefix="/api/roles", tags=["Roles"])


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
# Получаем абсолютный путь к директории, где лежит main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Создаем абсолютный путь к папке templates
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Инициализируем Admin, передавая ему путь к нашим шаблонам
admin = Admin(
    app=app,
    engine=session.engine,
    authentication_backend=authentication_backend,
    templates_dir=TEMPLATES_DIR
)

# Регистрируем все представления моделей, которые хотим видеть в админке
admin.add_view(TenantAdmin)
admin.add_view(UserAdmin)
admin.add_view(EntityTypeAdmin)
admin.add_view(AttributeAdmin)
admin.add_view(AttributeAliasAdmin)
admin.add_view(TableAliasAdmin)
admin.add_view(RoleAdmin)
admin.add_view(PermissionAdmin)
admin.add_view(AssignRoleView)
admin.add_view(SharedAccessAdmin)


# --------------------------------------------------------------------------
# --- ШАГ 6: ПОДКЛЮЧЕНИЕ API-РОУТЕРОВ ---
# --------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(aliases.router, prefix="/api/aliases", tags=["Aliases"])
app.include_router(meta.router, prefix="/api/meta", tags=["Meta (Constructor)"])
app.include_router(data.router, prefix="/api/data", tags=["Data (Custom)"])
app.include_router(select_lists.router, prefix="/api/meta/select-lists", tags=["Meta (Select Lists)"])
app.include_router(imports.router, prefix="/api/imports", tags=["Imports"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(shares.router, prefix="/api/shares", tags=["Shares (Access Control)"])
app.include_router(calendar_views.router, prefix="/api/calendar-views", tags=["Calendar Views Config"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar Events"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"]) # <--
app.include_router(dashboards.router, prefix="/api/dashboards", tags=["Dashboards"])
# --------------------------------------------------------------------------
# --- ШАГ 7: ГЛОБАЛЬНЫЕ ЭНДПОИНТЫ (если нужны) ---
# --------------------------------------------------------------------------

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to CRM API"}
