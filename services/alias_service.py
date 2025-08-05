# services/alias_service.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from db import models, session


class AliasService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    def set_alias(
            self,
            table_name: str,
            attribute_name: str,
            display_name: str,
            current_user: models.User
    ) -> models.AttributeAlias:
        """
        Устанавливает или обновляет псевдоним для колонки.
        """
        # Ищем существующий псевдоним по уникальному ключу
        existing_alias = self.db.query(models.AttributeAlias).filter_by(
            tenant_id=current_user.tenant_id,
            table_name=table_name,
            attribute_name=attribute_name
        ).first()

        if existing_alias:
            # Если нашли - обновляем
            existing_alias.display_name = display_name
            db_obj = existing_alias
        else:
            # Если не нашли - создаем новый
            db_obj = models.AttributeAlias(
                tenant_id=current_user.tenant_id,
                table_name=table_name,
                attribute_name=attribute_name,
                display_name=display_name
            )

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_aliases_for_tenant(self, current_user: models.User) -> Dict[str, Dict[str, str]]:
        """
        Получает все псевдонимы для текущего пользователя и форматирует их
        в удобный для фронтенда словарь.
        """
        aliases = self.db.query(models.AttributeAlias).filter_by(
            tenant_id=current_user.tenant_id
        ).all()

        # Форматируем в вид: { 'leads': { 'organization_name': 'Клиент' } }
        result: Dict[str, Dict[str, str]] = {}
        for alias in aliases:
            if alias.table_name not in result:
                result[alias.table_name] = {}
            result[alias.table_name][alias.attribute_name] = alias.display_name

        return result

    def delete_alias(self, table_name: str, attribute_name: str, current_user: models.User):
        """
        Удаляет (сбрасывает) псевдоним, возвращая колонке стандартное название.
        """
        alias_to_delete = self.db.query(models.AttributeAlias).filter_by(
            tenant_id=current_user.tenant_id,
            table_name=table_name,
            attribute_name=attribute_name
        ).first()

        if not alias_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Псевдоним для данного атрибута не найден"
            )

        self.db.delete(alias_to_delete)
        self.db.commit()
        return None