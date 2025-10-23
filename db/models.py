# db/models.py
from sqlalchemy import Table, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy import inspect
from sqlalchemy import (Column, Integer, String, DateTime, Date, Float,
                        Boolean, Text, ForeignKey, UniqueConstraint, Time)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base




# Таблица-связка для отношения "Многие-ко-Многим" между ролями и разрешениями
role_permissions_table = Table('role_permissions', Base.metadata,
                               Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
                               Column('permission_id', Integer, ForeignKey('permissions.id', ondelete="CASCADE"),
                                      primary_key=True)
                               )

# Таблица-связка для отношения "Многие-ко-Многим" между пользователями и ролями
user_roles_table = Table('user_roles', Base.metadata,
                         Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
                         Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
                         )

# Таблица-связка для хранения выбранных опций для ОДНОГО значения
# типа "множественный выбор".
# Связывает AttributeValue (конкретную ячейку) с несколькими SelectOption (вариантами выбора).
attribute_value_multiselect_options = Table(
    'attribute_value_multiselect_options', Base.metadata,
    Column('attribute_value_id', Integer, ForeignKey('attribute_values.id', ondelete="CASCADE"), primary_key=True),
    Column('select_option_id', Integer, ForeignKey('select_options.id', ondelete="CASCADE"), primary_key=True)
)
# ------------------------------------


class Tenant(Base):
    __tablename__ = 'tenants'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- ДОБАВЬТЕ ЭТИ RELATIONSHIP'Ы С КАСКАДОМ ---
    users = relationship("User", cascade="all, delete-orphan")
    leads = relationship("Lead", cascade="all, delete-orphan")
    legal_entities = relationship("LegalEntity", cascade="all, delete-orphan")
    individuals = relationship("Individual", cascade="all, delete-orphan")
    entity_types = relationship("EntityType", cascade="all, delete-orphan")
    roles = relationship("Role", cascade="all, delete-orphan")
    attribute_aliases = relationship("AttributeAlias", cascade="all, delete-orphan")
    table_aliases = relationship("TableAlias", cascade="all, delete-orphan")
    select_option_lists = relationship("SelectOptionList", cascade="all, delete-orphan")

    # ---------------------------------------------

    def __str__(self):
        return self.name




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
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="legal_entities") # Добавляем back_populates


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

    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="individuals")

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

    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="leads")

# ... (в конце файла, после существующих моделей User, Lead и т.д.)

class EntityType(Base):
    """Описывает 'тип' пользовательской таблицы, например, 'Проекты', 'Контракты'."""
    __tablename__ = 'entity_types'
    id = Column(Integer, primary_key=True)
    # Системное имя, используется в URL, например 'projects'
    # --- ИЗМЕНЕНИЕ 1: Убираем unique=True отсюда ---
    name = Column(String, index=True, nullable=False)

    display_name = Column(String, nullable=False)

    # Добавляем `order_by="Attribute.id"` в `relationship`
    attributes = relationship(
        "Attribute",
        back_populates="entity_type",
        cascade="all, delete-orphan",
        order_by="Attribute.id", # <-- ВОТ ЭТО ИЗМЕНЕНИЕ
        foreign_keys="[Attribute.entity_type_id]"  # <-- ДОБАВЬТЕ ЭТОТ ПАРАМЕТР

    )
    entities = relationship("Entity", back_populates="entity_type", cascade="all, delete-orphan")
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="entity_types")
    # --- ИЗМЕНЕНИЕ 2: Добавляем композитное ограничение ---
    # Это говорит базе данных: "Комбинация значений в колонках 'name' и 'tenant_id'
    # должна быть уникальной во всей таблице".
    foreign_keys = "[Attribute.entity_type_id]"  # <--- ДОБАВЬТЕ ЭТОТ ПАРАМЕТР

    __table_args__ = (
        UniqueConstraint('name', 'tenant_id', name='_name_tenant_uc'),
    )
    def __str__(self):
        return self.display_name # Будет отображаться "Логи отправки SMS"


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
    # --- ДОБАВЬТЕ ЭТО ПОЛЕ ---
    # Тип связи: 'one-to-many' или 'many-to-many'
    relation_type = Column(String, nullable=True)

    entity_type = relationship("EntityType", back_populates="attributes",
        foreign_keys=[entity_type_id])

    # Это отношение говорит SQLAlchemy, что у одного Атрибута может быть много Значений.
    # cascade="all, delete-orphan" - самая важная часть.
    # "all" - применяет все операции (save-update, merge, etc.) к связанным объектам.
    # "delete-orphan" - удаляет 'AttributeValue', если он больше не связан ни с каким 'Attribute'.
    # "delete" (в составе "all") - удаляет все связанные 'AttributeValue', когда удаляется сам 'Attribute'.
    values = relationship("AttributeValue", cascade="all, delete-orphan")


    # Если value_type = 'select', это поле будет ссылаться на список опций
    select_list_id = Column(Integer, ForeignKey('select_option_lists.id'), nullable=True)
    select_list = relationship("SelectOptionList")
    # -------------------------

    # Хранит текст формулы, например, "{price} * {quantity}"
    formula_text = Column(Text, nullable=True)

    # Хранит символ валюты, если value_type = 'currency'
    currency_symbol = Column(String(5), nullable=True)

    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    target_entity_type_id = Column(Integer, ForeignKey('entity_types.id', ondelete="SET NULL"), nullable=True)
    source_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)
    target_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)
    display_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    back_relation_display_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)
    reciprocal_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)

    # Определяем связи для удобного доступа. `remote_side=[id]` нужен для self-referencing FK.
    target_entity_type = relationship("EntityType", foreign_keys=[target_entity_type_id])
    source_attribute = relationship("Attribute", foreign_keys=[source_attribute_id], remote_side=[id])
    target_attribute = relationship("Attribute", foreign_keys=[target_attribute_id], remote_side=[id])
    display_attribute = relationship("Attribute", foreign_keys=[display_attribute_id], remote_side=[id])

    back_relation_display_attribute = relationship("Attribute", foreign_keys=[back_relation_display_attribute_id], remote_side=[id])
    reciprocal_attribute = relationship("Attribute", foreign_keys=[reciprocal_attribute_id], uselist=False)

    def __str__(self):
        return self.display_name # Будет отображаться "Номер телефона", "Статус отправки" и т.д.




class Entity(Base):
    """Представляет одну 'строку' в пользовательской таблице. Например, конкретный проект."""
    __tablename__ = 'entities'
    id = Column(Integer, primary_key=True, index=True)
    entity_type_id = Column(Integer, ForeignKey('entity_types.id'), nullable=False)

    position = Column(Float, default=0.0, nullable=False, index=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь для каскадного удаления всех значений при удалении сущности
    values = relationship("AttributeValue", back_populates="entity", cascade="all, delete-orphan")
    entity_type = relationship("EntityType", back_populates="entities")
    def __str__(self):
        # Получаем инспектор для этого объекта.
        # Это стандартный способ проверить состояние объекта в SQLAlchemy.
        ins = inspect(self)

        # Проверяем, был ли атрибут 'entity_type' уже загружен.
        # 'entity_type' not in ins.unloaded - означает "атрибут НЕ находится в списке незагруженных".
        if 'entity_type' not in ins.unloaded:
            # Если он загружен, безопасно обращаемся к нему
            return f"Запись #{self.id} в таблице '{self.entity_type.display_name}'"
        else:
            # Если он НЕ загружен, возвращаем только ID,
            # чтобы избежать ошибки DetachedInstanceError.
            return f"Запись #{self.id}"


class AttributeValue(Base):
    """Хранит одно конкретное значение для одной строки и одной колонки."""
    __tablename__ = 'attribute_values'
    id = Column(Integer, primary_key=True)
    # Эти два поля почти всегда используются вместе в JOIN'ах
    entity_id = Column(Integer, ForeignKey('entities.id', ondelete="CASCADE"), nullable=False, index=True)
    attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="CASCADE"), nullable=False, index=True)

    # Храним значения разных типов в разных полях
    # Индексируем каждое поле со значением
    value_string = Column(Text, nullable=True, index=True)
    value_integer = Column(Integer, nullable=True, index=True)
    value_float = Column(Float, nullable=True, index=True)
    value_date = Column(DateTime, nullable=True, index=True)
    value_boolean = Column(Boolean, nullable=True, index=True)
    value_time = Column(Time, nullable=True, index=True)


    entity = relationship("Entity", back_populates="values")
    attribute = relationship("Attribute", back_populates="values")

    # Это "виртуальное" поле. Оно говорит SQLAlchemy, что для получения
    # значений типа multiselect нужно посмотреть в таблицу `attribute_value_multiselect_options`
    # и найти там все связанные `SelectOption`.
    multiselect_values = relationship(
        "SelectOption",
        secondary=attribute_value_multiselect_options
    )

    def __str__(self):
        # Эта функция вернет первое непустое значение из полей
        value = (
                self.value_string or
                self.value_integer or
                self.value_float or
                self.value_date or
                self.value_boolean
        )

        # Если по какой-то причине все поля пустые, вернем 'NULL'
        if value is None:
            return 'NULL'

        # Преобразуем значение в строку и возвращаем
        return str(value)



class AttributeAlias(Base):
    """Хранит пользовательские названия (псевдонимы) для колонок таблиц."""
    __tablename__ = 'attribute_aliases'

    id = Column(Integer, primary_key=True)
    # Системное имя таблицы, например 'leads' или 'custom_projects'
    table_name = Column(String, index=True, nullable=False)
    # Системное имя атрибута, например 'organization_name' или 'project_budget'
    attribute_name = Column(String, index=True, nullable=False)
    # Пользовательское название, которое будет отображаться
    display_name = Column(String, nullable=False)

    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="attribute_aliases")
    # Гарантируем, что для одного пользователя может быть только одно переименование
    # для одной колонки в одной таблице.
    __table_args__ = (
        UniqueConstraint('tenant_id', 'table_name', 'attribute_name', name='_tenant_table_attr_uc'),
    )

    def __str__(self):
        # Эта функция вернет первое непустое значение из полей
        value = (
                self.value_string or
                self.value_integer or
                self.value_float or
                self.value_date or
                self.value_boolean
        )

        # Если по какой-то причине все поля пустые, вернем 'NULL'
        if value is None:
            return 'NULL'

        # Преобразуем значение в строку и возвращаем
        return str(value)


class TableAlias(Base):
    """Хранит пользовательские названия (псевдонимы) для таблиц."""
    __tablename__ = 'table_aliases'

    id = Column(Integer, primary_key=True)
    # Системное имя таблицы, например 'leads' или 'custom_projects'
    table_name = Column(String, index=True, nullable=False)
    # Пользовательское название, которое будет отображаться
    display_name = Column(String, nullable=False)

    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="table_aliases")

    # Гарантируем, что для одного пользователя может быть только одно переименование для одной таблицы.
    __table_args__ = (
        UniqueConstraint('tenant_id', 'table_name', name='_tenant_table_name_uc'),
    )



class Permission(Base):
    """Модель атомарного разрешения (например, 'leads:view')"""
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    # Системное имя, например "leads:view" или "projects:edit"
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)  # Описание для UI, например "Просмотр списка лидов"
    # --- ДОБАВЬТЕ ЭТОТ МЕТОД ---
    def __str__(self):
        return self.name

class Role(Base):
    """Модель роли, которая объединяет набор разрешений"""
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Например, "Менеджер" или "Администратор"

    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="roles")

    # Связь с разрешениями (Многие-ко-Многим)
    permissions = relationship("Permission", secondary=role_permissions_table, backref="roles")

    # Гарантируем, что имена ролей уникальны в рамках одного клиента (тенанта)
    __table_args__ = (
        UniqueConstraint('name', 'tenant_id', name='_role_name_tenant_uc'),
    )
    # --- ДОБАВЬТЕ ЭТОТ МЕТОД ---
    def __str__(self):
        return self.name

# Теперь нам нужно обновить существующую модель User, добавив ей связь с ролями
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    full_name = Column(String, index=True)

    is_superuser = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=True, index=True)
    tenant = relationship("Tenant", back_populates="users")

    roles = relationship("Role", secondary=user_roles_table, backref="users")
    # shared_entity_types = relationship("SharedEntityType", back_populates="user")
    def __str__(self):
        return self.email




class AttributeOrder(Base):
    """
    Хранит пользовательский порядок отображения колонок (атрибутов)
    для конкретного типа сущности (таблицы).
    """
    __tablename__ = 'attribute_order'

    id = Column(Integer, primary_key=True)

    # Для какого пользователя этот порядок
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)

    # В какой таблице
    entity_type_id = Column(Integer, ForeignKey('entity_types.id', ondelete="CASCADE"), nullable=False, index=True)

    # Какая колонка
    attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="CASCADE"), nullable=False, index=True)

    # На какой позиции (0, 1, 2, ...)
    position = Column(Integer, nullable=False)

    user = relationship("User")
    entity_type = relationship("EntityType")
    attribute = relationship("Attribute")

    # Гарантируем, что для одной колонки в одной таблице у одного юзера может быть только одна позиция
    __table_args__ = (
        UniqueConstraint('user_id', 'entity_type_id', 'attribute_id', name='_user_type_attr_uc'),
    )





class SelectOptionList(Base):
    """Контейнер для набора опций выпадающего списка, например, 'Статусы лида'."""
    __tablename__ = 'select_option_lists'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False) # Название списка
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="select_option_lists")
    options = relationship("SelectOption", back_populates="option_list", cascade="all, delete-orphan")
    # Гарантируем уникальность имен списков в рамках одного клиента
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_option_list_name_tenant_uc'),)
    def __str__(self): return self.name




class SelectOption(Base):
    """Одна опция в выпадающем списке, например, 'В работе'."""
    __tablename__ = 'select_options'
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False) # Текст опции
    option_list_id = Column(Integer, ForeignKey('select_option_lists.id'), nullable=False)
    option_list = relationship("SelectOptionList", back_populates="options")
    def __str__(self): return self.value


# --- ДОБАВЬТЕ ЭТОТ НОВЫЙ КЛАСС ---
class EntityRelation(Base):
    """Таблица-связка для хранения связей Многие-ко-многим."""
    __tablename__ = 'entity_relations'

    id = Column(Integer, primary_key=True)

    # Какая колонка-связь определяет эту "ниточку"
    attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="CASCADE"), nullable=False, index=True)

    # ID "левой" стороны связи (например, ID Проекта)
    entity_a_id = Column(Integer, ForeignKey('entities.id', ondelete="CASCADE"), nullable=False, index=True)

    # ID "правой" стороны связи (например, ID Задачи)
    entity_b_id = Column(Integer, ForeignKey('entities.id', ondelete="CASCADE"), nullable=False, index=True)

    # Связи для удобного доступа
    attribute = relationship("Attribute")
    entity_a = relationship("Entity", foreign_keys=[entity_a_id])
    entity_b = relationship("Entity", foreign_keys=[entity_b_id])

    __table_args__ = (
        UniqueConstraint('attribute_id', 'entity_a_id', 'entity_b_id', name='_relation_uc'),
    )
# ------------------------------------