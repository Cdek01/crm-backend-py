# migrate_legacy_data.py
import logging
from db.session import SessionLocal
from db import models
from services.eav_service import EAVService
from services.alias_service import AliasService

# Настройка логирования, чтобы видеть прогресс
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def migrate_data():
    """
    Основная функция для миграции данных из старых таблиц в EAV.
    """
    db = SessionLocal()
    try:
        # Инициализируем сервисы, которые нам понадобятся
        alias_service = AliasService(db=db)
        eav_service = EAVService(db=db, alias_service=alias_service)

        # --- Миграция Лидов (Leads) ---
        logging.info(">>> Начинаем миграцию Лидов (Leads)...")
        # УКАЖИТЕ ПРАВИЛЬНОЕ СИСТЕМНОЕ ИМЯ ВАШЕЙ НОВОЙ EAV-ТАБЛИЦЫ ДЛЯ ЛИДОВ
        new_leads_table_name = "crm_leads"

        all_leads = db.query(models.Lead).all()
        for lead in all_leads:
            # Получаем пользователя, чтобы правильно создать запись
            owner = db.query(models.User).filter(models.User.tenant_id == lead.tenant_id).first()
            if not owner:
                logging.warning(f"Не найден владелец для Lead ID={lead.id}, пропуск.")
                continue

            # Собираем данные для переноса. Ключи - это системные имена колонок в EAV.
            lead_data = {
                "organization_name": lead.organization_name,
                "inn": lead.inn,
                "contact_number": lead.contact_number,
                "email": lead.email,
                "source": lead.source,
                "lead_status": lead.lead_status,
                # Добавьте сюда остальные поля, которые нужно перенести
            }
            # Удаляем пустые значения, чтобы не создавать лишних записей
            lead_data_cleaned = {k: v for k, v in lead_data.items() if v is not None}

            eav_service.create_entity(new_leads_table_name, lead_data_cleaned, owner)
            logging.info(f"Лид '{lead.organization_name}' (ID={lead.id}) успешно перенесен.")

        logging.info(f"*** Миграция Лидов завершена. Перенесено {len(all_leads)} записей. ***")

        # --- Миграция Юр. Лиц (Legal Entities) ---
        logging.info("\n>>> Начинаем миграцию Юр. Лиц (Legal Entities)...")
        # УКАЖИТЕ ИМЯ ВАШЕЙ НОВОЙ EAV-ТАБЛИЦЫ
        new_legal_table_name = "crm_legal"

        all_legal = db.query(models.LegalEntity).all()
        for entity in all_legal:
            owner = db.query(models.User).filter(models.User.tenant_id == entity.tenant_id).first()
            if not owner: continue

            entity_data = {
                "short_name": entity.short_name,
                "full_name": entity.full_name,
                "inn": entity.inn,
                "ogrn": entity.ogrn,
                "status": entity.status,
                "address": entity.address,
            }
            entity_data_cleaned = {k: v for k, v in entity_data.items() if v is not None}
            eav_service.create_entity(new_legal_table_name, entity_data_cleaned, owner)
            logging.info(f"Юр. лицо '{entity.short_name}' (ID={entity.id}) успешно перенесено.")

        logging.info(f"*** Миграция Юр. Лиц завершена. Перенесено {len(all_legal)} записей. ***")

        # --- Миграция Физ. Лиц (Individuals) ---
        # (Аналогично, добавьте сюда логику для Individuals)

    finally:
        db.close()


if __name__ == "__main__":
    print("Этот скрипт выполнит миграцию данных из старых таблиц в EAV.")
    print("!!! ПЕРЕД ЗАПУСКОМ УБЕДИТЕСЬ, ЧТО ВЫ СДЕЛАЛИ РЕЗЕРВНУЮ КОПИЮ БАЗЫ ДАННЫХ !!!")
    confirm = input("Введите 'migrate' для подтверждения запуска: ")
    if confirm == 'migrate':
        migrate_data()
    else:
        print("Миграция отменена.")