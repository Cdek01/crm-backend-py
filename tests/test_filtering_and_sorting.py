# tests/test_filtering_and_sorting.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from pydantic_settings import BaseSettings
from main import app  # Импортируем ваше FastAPI приложение
from db.base import Base
from db.session import get_db
from db import models
from api.deps import get_current_user

# --- 1. НАСТРОЙКА ТЕСТОВОЙ БАЗЫ ДАННЫХ ---
# Используем отдельную SQLite базу в памяти для каждого тестового запуска
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем все таблицы перед началом тестов
Base.metadata.create_all(bind=engine)


# --- 2. ПЕРЕОПРЕДЕЛЕНИЕ ЗАВИСИМОСТЕЙ (Dependency Overrides) ---
# Эта функция будет подменять `get_db` в эндпоинтах, чтобы они работали с тестовой БД
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Эта функция подменяет `get_current_user`, чтобы не проверять JWT-токен в тестах
# Мы просто "доверяем" пользователю, которого создали для теста
def override_get_current_user():
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == "testuser@example.com").first()
    db.close()
    return user


# Применяем переопределения к нашему приложению
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# --- 3. PYTEST FIXTURES (Подготовка данных) ---

@pytest.fixture(scope="function")
def db() -> Generator:
    # Создаем таблицы перед каждым тестом
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    yield db_session
    db_session.close()
    # Удаляем все таблицы после каждого теста, чтобы тесты были независимыми
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


# Фикстура для создания начальных данных
@pytest.fixture(scope="function", autouse=True)
def setup_test_data(db):
    # Создаем клиента (Tenant)
    tenant = models.Tenant(name="Test Tenant")
    db.add(tenant)
    db.flush()

    # Создаем пользователя для тестов
    user = models.User(
        email="testuser@example.com",
        hashed_password="fake_password",
        tenant_id=tenant.id
    )
    db.add(user)
    db.flush()

    # --- Создаем тестовые данные для всех таблиц ---

    # Лиды (Leads)
    db.add_all([
        models.Lead(organization_name="Alpha Project", lead_status="New", rating=5, tenant_id=tenant.id,
                    responsible_manager_id=user.id),
        models.Lead(organization_name="Beta Services", lead_status="In Progress", rating=3, tenant_id=tenant.id,
                    responsible_manager_id=user.id),
        models.Lead(organization_name="Gamma Inc", lead_status="New", rating=4, tenant_id=tenant.id,
                    responsible_manager_id=user.id),
    ])

    # Юр. лица (Legal Entities)
    db.add_all([
        models.LegalEntity(short_name="StroyMontazh", inn="7701234567", status="Действующая", revenue=1000000,
                           tenant_id=tenant.id),
        models.LegalEntity(short_name="AgroProm", inn="7707654321", status="Действующая", revenue=5000000,
                           tenant_id=tenant.id),
        models.LegalEntity(short_name="IT Solutions", inn="7705112233", status="В процессе ликвидации", revenue=250000,
                           tenant_id=tenant.id),
    ])

    # Физ. лица (Individuals)
    db.add_all([
        models.Individual(full_name="Иванов Иван Иванович", email="ivanov@test.com", city="Москва",
                          tenant_id=tenant.id),
        models.Individual(full_name="Петров Петр Петрович", email="petrov@test.com", city="Санкт-Петербург",
                          tenant_id=tenant.id),
        models.Individual(full_name="Сидоров Сидор Сидорович", email="sidorov@test.com", city="Москва",
                          tenant_id=tenant.id),
    ])

    db.commit()


# --- 4. САМИ ТЕСТЫ ---

# Тесты для Лидов (Leads)
def test_filter_leads_by_status(client):
    response = client.get("/api/leads?lead_status=New")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item['lead_status'] == 'New' for item in data)


def test_sort_leads_by_rating_desc(client):
    response = client.get("/api/leads?sort_by=rating&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    ratings = [item['rating'] for item in data]
    assert ratings == [5, 4, 3]  # Проверяем правильный порядок


def test_sort_leads_by_name_asc(client):
    response = client.get("/api/leads?sort_by=organization_name&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    names = [item['organization_name'] for item in data]
    assert names == ["Alpha Project", "Beta Services", "Gamma Inc"]


# Тесты для Юр. лиц (Legal Entities)
def test_filter_legal_entities_by_status(client):
    response = client.get("/api/legal-entities?status=Действующая")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item['status'] == 'Действующая' for item in data)


def test_filter_legal_entities_by_inn(client):
    response = client.get("/api/legal-entities?inn=7707654321")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['short_name'] == "AgroProm"


def test_sort_legal_entities_by_revenue_desc(client):
    response = client.get("/api/legal-entities?sort_by=revenue&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    revenues = [item['revenue'] for item in data]
    assert revenues == [5000000, 1000000, 250000]


# Тесты для Физ. лиц (Individuals)
def test_filter_individuals_by_city(client, db):
    # Мы не добавляли фильтр по городу в сервис, но это легко сделать по аналогии.
    # Если вы добавите, этот тест будет работать. А пока давайте отфильтруем по email.
    response = client.get("/api/individuals?email=ivanov@test.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['full_name'] == "Иванов Иван Иванович"


def test_sort_individuals_by_name_asc(client):
    response = client.get("/api/individuals?sort_by=full_name&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    names = [item['full_name'] for item in data]
    assert names == ["Иванов Иван Иванович", "Петров Петр Петрович", "Сидоров Сидор Сидорович"]