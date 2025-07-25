# db/models.py

from sqlalchemy import (Column, Integer, String, DateTime, Date, Float,
                        Boolean, Text, ForeignKey)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Tenant(Base):
    __tablename__ = 'tenants'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=True, index=True) # Сделаем nullable=True на время
    tenant = relationship("Tenant")


# --- НОВЫЕ И ПОЛНЫЕ МОДЕЛИ ---

class LegalEntity(Base):
    """Модель для юридических лиц"""
    __tablename__ = "legal_entities"

    id = Column(Integer, primary_key=True, index=True)
    short_name = Column(String, nullable=True)
    full_name = Column(Text, nullable=True)
    inn = Column(String(12), unique=True, index=True)
    kpp = Column(String(9), nullable=True)
    ogrn = Column(String(15), unique=True, index=True)
    status = Column(String, nullable=True)
    registration_date = Column(Date, nullable=True)
    liquidation_date = Column(Date, nullable=True)

    primary_activity_name = Column(Text, nullable=True)
    primary_activity_code = Column(String, nullable=True)
    employee_count = Column(Integer, nullable=True)

    # Руководство и собственники (храним как текст для простоты)
    managers = Column(Text, nullable=True)
    ex_managers = Column(Text, nullable=True)
    shareholders = Column(Text, nullable=True)
    founders = Column(Text, nullable=True)
    ex_founders = Column(Text, nullable=True)
    share_details = Column(Text, nullable=True)  # "Доля акций в организациях"
    established_entities = Column(Text, nullable=True)  # "Учрежденные юрлица"

    authorized_capital = Column(Float, nullable=True)

    # Контакты
    websites = Column(Text, nullable=True)
    phone_numbers = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    ex_addresses = Column(Text, nullable=True)  # "Бывшие адреса"

    # Финансовые показатели
    financial_report_year = Column(Integer, nullable=True)
    balance = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    net_profit = Column(Float, nullable=True)

    # Исполнительные производства
    enforcement_proceedings_sum = Column(Float, nullable=True)
    enforcement_proceedings_count = Column(Integer, nullable=True)

    # Регистрационные номера
    pfr_number = Column(String, nullable=True)
    fss_number = Column(String, nullable=True)
    foms_number = Column(String, nullable=True)

    # Классификаторы
    okpo = Column(String, nullable=True)
    okato = Column(String, nullable=True)
    oktmo = Column(String, nullable=True)
    okopf = Column(String, nullable=True)
    okogu = Column(String, nullable=True)
    okfs = Column(String, nullable=True)

    tax_authority = Column(String, nullable=True)
    other_info = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)



class Individual(Base):
    """Модель для физических лиц"""
    __tablename__ = "individuals"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    inn = Column(String(12), unique=True, index=True, nullable=True)
    city = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)

    is_sole_proprietor = Column(Boolean, default=False, nullable=True)  # ИП
    notes = Column(Text, nullable=True) # <--- ДОБАВЬТЕ ЭТУ СТРОКУ

    # Связи с компаниями (храним как текст для простоты)
    founder_in = Column(Text, nullable=True)
    manager_in = Column(Text, nullable=True)
    other_position = Column(Text, nullable=True)  # "Иная должность"

    monitoring = Column(Boolean, default=False)

    # `Дата добавления` и `Дата создания` покрываются этим полем
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)


class Lead(Base):
    """Модель для Лидов (воронка продаж)"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    # Основная информация о компании-лиде
    organization_name = Column(String, index=True)
    inn = Column(String(12), nullable=True, index=True)
    establishment_date = Column(Date, nullable=True)  # "Дата образования"
    contact_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    websites = Column(Text, nullable=True)
    address = Column(Text, nullable=True)

    # Поля воронки
    source = Column(String, nullable=True)
    lead_status = Column(String, default="New", index=True)
    rating = Column(Integer, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    scenario = Column(String, nullable=True)  # "Сценарий"

    # Ответственный
    responsible_manager_id = Column(Integer, ForeignKey("users.id"))
    responsible_manager = relationship("User")

    # Дополнительная информация (дублирует много полей из LegalEntity)
    company_status = Column(String, nullable=True)
    primary_activity = Column(Text, nullable=True)
    okved_codes = Column(Text, nullable=True)
    employee_count = Column(Integer, nullable=True)
    manager_name = Column(String, nullable=True)
    authorized_capital = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    net_profit = Column(Float, nullable=True)

    predecessors = Column(Text, nullable=True)  # "Предшественник"
    successors = Column(Text, nullable=True)  # "Преемник"

    notes = Column(Text, nullable=True)
    monitoring = Column(Boolean, default=False)

    # Даты
    last_contact_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)



# ... (в конце файла, после существующих моделей User, Lead и т.д.)

class EntityType(Base):
    """Описывает 'тип' пользовательской таблицы, например, 'Проекты', 'Контракты'."""
    __tablename__ = 'entity_types'
    id = Column(Integer, primary_key=True)
    # Системное имя, используется в URL, например 'projects'
    name = Column(String, unique=True, index=True, nullable=False)
    # Отображаемое имя для фронтенда, например 'Проекты'
    display_name = Column(String, nullable=False)

    # Связь для удобного получения всех атрибутов типа
    attributes = relationship("Attribute", back_populates="entity_type", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="entity_type")

    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)


class Attribute(Base):
    """Описывает 'колонку' в пользовательской таблице, например, 'Название проекта', 'Бюджет'."""
    __tablename__ = 'attributes'
    id = Column(Integer, primary_key=True)
    entity_type_id = Column(Integer, ForeignKey('entity_types.id'), nullable=False)
    # Системное имя, используется как ключ в JSON, например 'project_name'
    name = Column(String, nullable=False)
    # Отображаемое имя для фронтенда, например 'Название Проекта'
    display_name = Column(String, nullable=False)
    # Тип значения: 'string', 'integer', 'float', 'date', 'boolean'. Важно для валидации.
    value_type = Column(String, nullable=False)

    entity_type = relationship("EntityType", back_populates="attributes")


class Entity(Base):
    """Представляет одну 'строку' в пользовательской таблице. Например, конкретный проект."""
    __tablename__ = 'entities'
    id = Column(Integer, primary_key=True, index=True)
    entity_type_id = Column(Integer, ForeignKey('entity_types.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь для каскадного удаления всех значений при удалении сущности
    values = relationship("AttributeValue", back_populates="entity", cascade="all, delete-orphan")
    entity_type = relationship("EntityType", back_populates="entities")


class AttributeValue(Base):
    """Хранит одно конкретное значение для одной строки и одной колонки."""
    __tablename__ = 'attribute_values'
    id = Column(Integer, primary_key=True)
    # Эти два поля почти всегда используются вместе в JOIN'ах
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    attribute_id = Column(Integer, ForeignKey('attributes.id'), nullable=False)

    # Храним значения разных типов в разных полях
    # Индексируем каждое поле со значением
    value_string = Column(Text, nullable=True)
    value_integer = Column(Integer, nullable=True)
    value_float = Column(Float, nullable=True)
    value_date = Column(DateTime, nullable=True)
    value_boolean = Column(Boolean, nullable=True)

    entity = relationship("Entity", back_populates="values")
    attribute = relationship("Attribute")