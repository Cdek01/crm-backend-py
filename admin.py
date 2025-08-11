# admin.py
from sqladmin import ModelView
from sqladmin.filters import BooleanFilter, ForeignKeyFilter
from db import models
from fastapi import Request, HTTPException # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ
from wtforms import Form, StringField, PasswordField  # <-- ИЗМЕНИТЕ ИМПОРТ
from wtforms.validators import DataRequired  # <-- ДОБАВЬТЕ ИМПОРТ
from core import security # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ
from sqladmin.fields import QuerySelectField, QuerySelectMultipleField # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ

# --- Функции-форматтеры ---
def tenant_formatter(model, name):
    return model.tenant.name if model.tenant else "N/A"


def entity_type_formatter(model, name):
    return model.entity_type.name if model.entity_type else "N/A"


# ---------------------------------------------------------------------

class TenantAdmin(ModelView, model=models.Tenant):
    name = "Клиент"
    name_plural = "Клиенты"
    icon = "fa-solid fa-crown"
    column_list = [models.Tenant.id, models.Tenant.name, models.Tenant.created_at]
    column_searchable_list = [models.Tenant.name]


class UserCreateForm(Form):
    email = StringField('Email', validators=[DataRequired()])
    full_name = StringField('Full Name')
    password = PasswordField('Password', validators=[DataRequired()])


class UserAdmin(ModelView, model=models.User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_list = [
        models.User.id,
        models.User.email,
        models.User.full_name,
        "tenant",
        models.User.is_superuser,
    ]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.User.email, models.User.full_name]

    # Указываем поля для формы. SQLAdmin должен сам обработать связь 'roles'.
    form_columns = [
        models.User.email,
        models.User.full_name,
        models.User.tenant,
        models.User.is_superuser,
        models.User.roles,
    ]
class LeadAdmin(ModelView, model=models.Lead):
    name = "Лид"
    name_plural = "Лиды"
    icon = "fa-solid fa-filter"
    column_list = [models.Lead.id, models.Lead.organization_name, models.Lead.lead_status, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.Lead.organization_name, models.Lead.inn]




class LegalEntityAdmin(ModelView, model=models.LegalEntity):
    name = "Юр. лицо"
    name_plural = "Юр. лица"
    icon = "fa-solid fa-building"
    column_list = [models.LegalEntity.id, models.LegalEntity.short_name, models.LegalEntity.inn, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.LegalEntity.short_name, models.LegalEntity.inn]



class IndividualAdmin(ModelView, model=models.Individual):
    name = "Физ. лицо"
    name_plural = "Физ. лица"
    icon = "fa-solid fa-address-card"
    column_list = [models.Individual.id, models.Individual.full_name, models.Individual.email, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.Individual.full_name, models.Individual.email, models.Individual.inn]


class EntityTypeAdmin(ModelView, model=models.EntityType):
    name = "Тип таблицы (кастом.)"
    name_plural = "Типы таблиц (кастом.)"
    icon = "fa-solid fa-table-list"
    column_list = [models.EntityType.id, models.EntityType.name, models.EntityType.display_name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}




class AttributeAdmin(ModelView, model=models.Attribute):
    name = "Атрибут (кастом.)"
    name_plural = "Атрибуты (кастом.)"
    icon = "fa-solid fa-table-columns"
    column_list = [models.Attribute.id, models.Attribute.name, models.Attribute.display_name,
                   models.Attribute.value_type, "entity_type"]
    column_formatters = {"entity_type": entity_type_formatter}




class AttributeAliasAdmin(ModelView, model=models.AttributeAlias):
    name = "Псевдоним колонки"
    name_plural = "Псевдонимы колонок"
    icon = "fa-solid fa-pen-ruler"
    column_list = [models.AttributeAlias.id, models.AttributeAlias.table_name, models.AttributeAlias.attribute_name,
                   models.AttributeAlias.display_name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.AttributeAlias.table_name, models.AttributeAlias.attribute_name,
                              models.AttributeAlias.display_name]




class TableAliasAdmin(ModelView, model=models.TableAlias):
    name = "Псевдоним таблицы"
    name_plural = "Псевдонимы таблиц"
    icon = "fa-solid fa-table"

    column_list = [models.TableAlias.id, models.TableAlias.table_name, models.TableAlias.display_name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.TableAlias.table_name, models.TableAlias.display_name]




class PermissionAdmin(ModelView, model=models.Permission):
    name = "Разрешение"
    name_plural = "Разрешения"
    icon = "fa-solid fa-key"

    # 1. Разрешаем создание, редактирование и удаление
    can_create = True
    can_edit = True
    can_delete = True

    column_list = [models.Permission.id, models.Permission.name, models.Permission.description]
    column_searchable_list = [models.Permission.name]

    # 2. Определяем список "защищенных" системных разрешений.
    # Их нельзя будет удалить или изменить их системное имя.
    # Этот список должен совпадать с тем, что у вас в seed_permissions.py
    PROTECTED_PERMISSIONS = {
        'roles:manage', 'leads:view', 'leads:create', 'leads:edit', 'leads:delete',
        'legal_entities:view', 'legal_entities:create', 'legal_entities:edit', 'legal_entities:delete',
        'individuals:view', 'individuals:create', 'individuals:edit', 'individuals:delete',
        'meta:view', 'meta:manage', 'aliases:manage',
    }

    # 3. Переопределяем метод удаления
    async def delete_model(self, request: Request, pk: str) -> None:
        # Получаем объект, который собираемся удалить
        session = request.state.session
        model = await self.get_object_for_delete(pk)

        if model and model.name in self.PROTECTED_PERMISSIONS:
            # Если имя разрешения в нашем списке защищенных, выбрасываем ошибку
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя удалить системное разрешение '{model.name}'."
            )

        # Если проверка пройдена, вызываем стандартный метод удаления
        await super().delete_model(request, pk)

    # 4. Переопределяем метод сохранения изменений
    async def update_model(self, request: Request, pk: str, data: dict) -> None:
        session = request.state.session
        model = await self.get_object_for_edit(pk)

        # Запрещаем менять системное имя 'name' у защищенных разрешений
        if model and model.name in self.PROTECTED_PERMISSIONS and 'name' in data and data['name'] != model.name:
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя изменить системное имя для разрешения '{model.name}'."
            )

        # Разрешаем менять описание и другие поля
        await super().update_model(request, pk, data)




class RoleAdmin(ModelView, model=models.Role):
    name = "Роль"
    name_plural = "Роли"
    icon = "fa-solid fa-user-shield"

    column_list = [models.Role.id, models.Role.name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.Role.name]

    # Используем самый простой способ определения полей на форме
    form_columns = [
        models.Role.name,
        models.Role.tenant,
        models.Role.permissions,
    ]
