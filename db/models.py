# db/models.py
from sqlalchemy import Table, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy import inspect
from sqlalchemy import (Column, Integer, String, DateTime, Date, Float,
                        Boolean, Text, ForeignKey, UniqueConstraint, Time)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from enum import Enum as PyEnum
import json
from sqlalchemy import LargeBinary


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
# Связывает одну ячейку (AttributeValue) с несколькими записями (Entity)
# для реализации связи "многие-ко-многим".
attribute_value_many_to_many_links = Table(
    'attribute_value_many_to_many_links', Base.metadata,
    Column('attribute_value_id', Integer, ForeignKey('attribute_values.id', ondelete="CASCADE"), primary_key=True),
    Column('target_entity_id', Integer, ForeignKey('entities.id', ondelete="CASCADE"), primary_key=True)
)
# -----------------------------

class Tenant(Base):
    __tablename__ = 'tenants'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # --- НАЧАЛО ПОЛНОЙ И ИСПРАВЛЕННОЙ ВЕРСИИ ---

    # --- Настройки интеграции с Модульбанком ---

    # 1. Зашифрованный токен.
    modulbank_api_token = Column(LargeBinary, nullable=True)

    # 2. Статус интеграции.
    modulbank_integration_status = Column(String(50), nullable=True, default='inactive')

    # 3. Дата последней успешной синхронизации.
    modulbank_last_sync = Column(DateTime(timezone=True), nullable=True)

    # 4. Сообщение об ошибке.
    modulbank_last_error = Column(Text, nullable=True)

    # --- Настройки расписания ---

    # 5. Тип расписания: 'manual', 'hourly', 'daily', 'weekly'
    modulbank_sync_schedule_type = Column(String(50), default='manual')

    # 6. Время для ежедневной/еженедельной синхронизации.
    modulbank_sync_time = Column(Time, nullable=True)

    # 7. День недели для еженедельной синхронизации (0=Пн, ..., 6=Вс).
    modulbank_sync_weekday = Column(Integer, nullable=True)

    # 8. ID связанной задачи в таблице periodic_tasks Celery.
    modulbank_periodic_task_id = Column(Integer, nullable=True)
    # Храним ID компаний и счетов, выбранных для синхронизации, в формате JSON.
    # Пример: {"companies": ["company_id_1"], "accounts": ["acc_id_A", "acc_id_B"]}
    modulbank_sync_sources = Column(Text, nullable=True)
    # --- КОНЕЦ ПОЛНОЙ И ИСПРАВЛЕННОЙ ВЕРСИИ ---

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Добавляем поля для интеграции с Билайн ---
    beeline_api_token = Column(LargeBinary, nullable=True)
    beeline_integration_status = Column(String(50), nullable=True, default='inactive')
    beeline_last_sync = Column(DateTime(timezone=True), nullable=True)
    beeline_last_error = Column(Text, nullable=True)
    beeline_sync_schedule_type = Column(String(50), default='manual')
    beeline_sync_time = Column(Time, nullable=True)
    beeline_sync_weekday = Column(Integer, nullable=True)
    beeline_periodic_task_id = Column(Integer, nullable=True)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    
    # --- ДОБАВЬТЕ ЭТИ RELATIONSHIP'Ы С КАСКАДОМ ---
    users = relationship("User", cascade="all, delete-orphan")
    entity_types = relationship("EntityType", cascade="all, delete-orphan")
    roles = relationship("Role", cascade="all, delete-orphan")
    attribute_aliases = relationship("AttributeAlias", cascade="all, delete-orphan")
    table_aliases = relationship("TableAlias", cascade="all, delete-orphan")
    select_option_lists = relationship("SelectOptionList", cascade="all, delete-orphan")
    # ---------------------------------------------

    def __str__(self):
        return self.name



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
    # --- ДОБАВЬТЕ ЭТО ПОЛЕ ---
    # Если True, то эта колонка-связь может хранить ссылки на несколько записей (многие-ко-многим).
    # Если False, то только на одну (один-ко-многим).
    allow_multiple_selection = Column(Boolean, default=False, nullable=False)
    # ---------------------------
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
    # Новое поле для хранения неограниченного текста
    value_text = Column(Text, nullable=True)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
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
    # --- ДОБАВЬТЕ ЭТОТ RELATIONSHIP ---
    # Это "виртуальное" поле для доступа к связанным записям через нашу новую таблицу.
    many_to_many_links = relationship(
        "Entity",
        secondary=attribute_value_many_to_many_links
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






# --- НАЧАЛО ИЗМЕНЕНИЙ ---

# 1. Создаем Enum для уровней доступа
class PermissionLevel(PyEnum):
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"

# 2. Создаем новую модель для хранения доступов
class SharedAccess(Base):
    __tablename__ = 'shared_access'
    id = Column(Integer, primary_key=True)

    # К какой таблице дан доступ
    entity_type_id = Column(Integer, ForeignKey('entity_types.id', ondelete="CASCADE"), nullable=False, index=True)
    # Кому дан доступ
    grantee_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)
    # Кто предоставил доступ
    grantor_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)
    # Какой уровень доступа
    permission_level = Column(String, nullable=False, default=PermissionLevel.VIEW.value)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи для удобного доступа
    entity_type = relationship("EntityType")
    grantee = relationship("User", foreign_keys=[grantee_user_id], back_populates="shared_with_me")
    grantor = relationship("User", foreign_keys=[grantor_user_id])

    # Гарантируем, что одному пользователю нельзя дать доступ к одной таблице дважды
    __table_args__ = (
        UniqueConstraint('entity_type_id', 'grantee_user_id', name='_entity_grantee_uc'),
    )





# Теперь нам нужно обновить существующую модель User, добавив ей связь с ролями
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    full_name = Column(String, index=True)
    avatar_url = Column(String, nullable=True)

    is_superuser = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=True, index=True)
    tenant = relationship("Tenant", back_populates="users")

    roles = relationship("Role", secondary=user_roles_table, backref="users")
    # --- ДОБАВЬТЕ ЭТОТ RELATIONSHIP ---
    # Показывает, к каким таблицам ДРУГИХ пользователей мне дали доступ
    shared_with_me = relationship("SharedAccess", back_populates="grantee", foreign_keys=[SharedAccess.grantee_user_id], cascade="all, delete-orphan")
    # ---------------------------------
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





class CalendarViewConfig(Base):
    """Хранит настройки для одного 'Представления типа Ка-лендарь'."""
    __tablename__ = 'calendar_view_configs'

    id = Column(Integer, primary_key=True)

    # --- Основные настройки ---
    name = Column(String, nullable=False)  # Название, которое видит пользователь: "Календарь по срокам"
    entity_type_id = Column(Integer, ForeignKey('entity_types.id', ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)

    # --- Настройки маппинга полей (что откуда брать) ---

    # 1. Заголовок события (обязательно)
    title_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="CASCADE"), nullable=False)

    # 2. Дата начала (обязательно)
    start_date_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="CASCADE"), nullable=False)

    # 3. Дата окончания (опционально, для событий-диапазонов)
    end_date_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)

    # 4. Флаг "Событие на весь день" (опционально)
    # Позволяет использовать поле типа "Checkbox" для определения,
    # должно ли событие занимать весь день в календаре.
    is_allday_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)

    # --- Настройки внешнего вида ---

    # 5. Раскраска событий (опционально)
    # Поле, значения которого будут определять цвет события (например, поле "Статус" или "Приоритет").
    color_attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete="SET NULL"), nullable=True)

    # 6. Настройки цветов
    # Храним JSON-объект, который сопоставляет конкретное значение с цветом.
    # Пример: '{"Новая": "#3498db", "В работе": "#f1c40f", "Готово": "#2ecc71"}'
    color_settings = Column(Text, nullable=True, default=json.dumps({}))

    # --- Настройки фильтрации и видимости ---

    # 7. Сохраненные фильтры
    # Позволяет сохранить набор фильтров вместе с представлением.
    # Например, календарь может показывать только "мои задачи" или "задачи с высоким приоритетом".
    filters = Column(Text, nullable=True)

    # 8. Видимые поля в карточке
    # Храним JSON-массив ID атрибутов, которые нужно показывать во всплывающей карточке
    # при клике на событие в календаре.
    # Пример: '[101, 102, 105]' (где 101 - "Статус", 102 - "Ответственный" и т.д.)
    visible_fields = Column(Text, nullable=True, default=json.dumps([]))

    # --- Дополнительные настройки ---

    # 9. Вид по умолчанию
    # В каком режиме открывать календарь: 'month', 'week', 'day'.
    default_view = Column(String(20), nullable=False, default='month')

    # 10. Флаг "Скрывать выходные"
    hide_weekends = Column(Boolean, nullable=False, default=False)

    # --- Связи (Relationships) для удобного доступа в коде ---
    entity_type = relationship("EntityType", foreign_keys=[entity_type_id])
    tenant = relationship("Tenant")

    # Связи с атрибутами
    title_attribute = relationship("Attribute", foreign_keys=[title_attribute_id])
    start_date_attribute = relationship("Attribute", foreign_keys=[start_date_attribute_id])
    end_date_attribute = relationship("Attribute", foreign_keys=[end_date_attribute_id])
    is_allday_attribute = relationship("Attribute", foreign_keys=[is_allday_attribute_id])
    color_attribute = relationship("Attribute", foreign_keys=[color_attribute_id])





