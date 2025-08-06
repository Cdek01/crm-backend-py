# admin.py
from sqladmin import ModelView
from sqladmin.filters import BooleanFilter, ForeignKeyFilter
from db import models


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


class UserAdmin(ModelView, model=models.User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    column_list = [models.User.id, models.User.email, models.User.full_name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.User.email, models.User.full_name]

    # ИСПРАВЛЕНИЕ: Убираем label
    column_filters = [
        ForeignKeyFilter(models.User.tenant, "name")
    ]


class LeadAdmin(ModelView, model=models.Lead):
    name = "Лид"
    name_plural = "Лиды"
    icon = "fa-solid fa-filter"
    column_list = [models.Lead.id, models.Lead.organization_name, models.Lead.lead_status, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.Lead.organization_name, models.Lead.inn]

    column_filters = [
        models.Lead.lead_status,
        models.Lead.source,
        ForeignKeyFilter(models.Lead.tenant, "name")
    ]


class LegalEntityAdmin(ModelView, model=models.LegalEntity):
    name = "Юр. лицо"
    name_plural = "Юр. лица"
    icon = "fa-solid fa-building"
    column_list = [models.LegalEntity.id, models.LegalEntity.short_name, models.LegalEntity.inn, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.LegalEntity.short_name, models.LegalEntity.inn]

    column_filters = [
        models.LegalEntity.status,
        ForeignKeyFilter(models.LegalEntity.tenant, "name")
    ]


class IndividualAdmin(ModelView, model=models.Individual):
    name = "Физ. лицо"
    name_plural = "Физ. лица"
    icon = "fa-solid fa-address-card"
    column_list = [models.Individual.id, models.Individual.full_name, models.Individual.email, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.Individual.full_name, models.Individual.email, models.Individual.inn]

    column_filters = [
        BooleanFilter(models.Individual.is_sole_proprietor),
        ForeignKeyFilter(models.Individual.tenant, "name")
    ]


class EntityTypeAdmin(ModelView, model=models.EntityType):
    name = "Тип таблицы (кастом.)"
    name_plural = "Типы таблиц (кастом.)"
    icon = "fa-solid fa-table-list"
    column_list = [models.EntityType.id, models.EntityType.name, models.EntityType.display_name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}

    column_filters = [
        ForeignKeyFilter(models.EntityType.tenant, "name")
    ]


class AttributeAdmin(ModelView, model=models.Attribute):
    name = "Атрибут (кастом.)"
    name_plural = "Атрибуты (кастом.)"
    icon = "fa-solid fa-table-columns"
    column_list = [models.Attribute.id, models.Attribute.name, models.Attribute.display_name,
                   models.Attribute.value_type, "entity_type"]
    column_formatters = {"entity_type": entity_type_formatter}

    column_filters = [
        ForeignKeyFilter(models.Attribute.entity_type, "name"),
        models.Attribute.value_type,
    ]


class AttributeAliasAdmin(ModelView, model=models.AttributeAlias):
    name = "Псевдоним колонки"
    name_plural = "Псевдонимы колонок"
    icon = "fa-solid fa-pen-ruler"
    column_list = [models.AttributeAlias.id, models.AttributeAlias.table_name, models.AttributeAlias.attribute_name,
                   models.AttributeAlias.display_name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.AttributeAlias.table_name, models.AttributeAlias.attribute_name,
                              models.AttributeAlias.display_name]

    column_filters = [
        models.AttributeAlias.table_name,
        ForeignKeyFilter(models.AttributeAlias.tenant, "name")
    ]


class TableAliasAdmin(ModelView, model=models.TableAlias):
    name = "Псевдоним таблицы"
    name_plural = "Псевдонимы таблиц"
    icon = "fa-solid fa-table"

    column_list = [models.TableAlias.id, models.TableAlias.table_name, models.TableAlias.display_name, "tenant"]
    column_formatters = {"tenant": tenant_formatter}
    column_searchable_list = [models.TableAlias.table_name, models.TableAlias.display_name]

    column_filters = [
        models.TableAlias.table_name,
        ForeignKeyFilter(models.TableAlias.tenant, "name")
    ]