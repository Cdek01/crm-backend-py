# main.py

# --- ШАГ 1: ОСНОВНЫЕ ИМПОРТЫ ---
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqladmin import BaseView, expose
import os # <-- Убедитесь, что этот импорт есть вверху файла

# --- ШАГ 2: ИМПОРТЫ ИЗ ВАШЕГО ПРОЕКТА ---
# Модули для работы с БД и конфигурацией
from db import models, base, session

# Схемы и зависимости для API
from schemas.user import User, UserWithPermissions
from api.deps import get_current_user
from sqlalchemy.orm import joinedload # <-- Добавьте импорт
from fastapi.responses import RedirectResponse, HTMLResponse # <-- Добавьте HTMLResponse

# Роутеры для всех ваших API эндпоинтов
from api.endpoints import auth, leads, legal_entities, individuals, meta, data, aliases, select_lists
from starlette.templating import Jinja2Templates # <-- Убедитесь, что этот импорт есть

# Модули для админ-панели
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from admin import (
    TenantAdmin, UserAdmin, LeadAdmin, LegalEntityAdmin,
    IndividualAdmin, EntityTypeAdmin, AttributeAdmin, AttributeAliasAdmin, TableAliasAdmin,
    RoleAdmin, PermissionAdmin,
    AssignRoleView
)
from api.endpoints import roles, shared # <-- добавьте roles



# --------------------------------------------------------------------------
# --- ШАГ 3: ИНИЦИАЛИЗАЦИЯ БД И ПРИЛОЖЕНИЯ ---
# --------------------------------------------------------------------------

# Создаем таблицы в БД при первом запуске (если их нет)
base.Base.metadata.create_all(bind=session.engine)

# Создаем главный экземпляр FastAPI ОДИН РАЗ
app = FastAPI(title="CRM API")

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
admin.add_view(LeadAdmin)
admin.add_view(LegalEntityAdmin)
admin.add_view(IndividualAdmin)
admin.add_view(EntityTypeAdmin)
admin.add_view(AttributeAdmin)
admin.add_view(AttributeAliasAdmin)
admin.add_view(TableAliasAdmin)
admin.add_view(RoleAdmin)
admin.add_view(PermissionAdmin)
admin.add_view(AssignRoleView) # <-- ДОБАВЬТЕ ЭТО
# admin.add_view(SharedEntityTypeAdmin)
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
app.include_router(shared.router, prefix="/api/shares", tags=["Shares"])
app.include_router(select_lists.router, prefix="/api/meta/select-lists", tags=["Meta (Select Lists)"])

# --------------------------------------------------------------------------
# --- ШАГ 7: ГЛОБАЛЬНЫЕ ЭНДПОИНТЫ (если нужны) ---
# --------------------------------------------------------------------------

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to CRM API"}


@app.get("/api/users/me", response_model=UserWithPermissions, tags=["Users"])
def read_users_me(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(session.get_db)
):
    """
    Получить информацию о текущем пользователе и его разрешениях.
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

    # Собираем все уникальные имена разрешений, проходя по всем ролям пользователя.
    user_permissions = set()
    for role in user_with_roles.roles:
        for perm in role.permissions:
            user_permissions.add(perm.name)

    response_user = UserWithPermissions.model_validate(user_with_roles)
    response_user.permissions = sorted(list(user_permissions))

    return response_user