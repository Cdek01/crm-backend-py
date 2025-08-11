from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import models, session


class RoleService:
    def __init__(self, db: Session = Depends(session.get_db)):
        self.db = db

    def create_role(self, name: str, current_user: models.User) -> models.Role:
        existing_role = self.db.query(models.Role).filter_by(
            name=name, tenant_id=current_user.tenant_id
        ).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="Роль с таким именем уже существует")

        new_role = models.Role(name=name, tenant_id=current_user.tenant_id)
        self.db.add(new_role)
        self.db.commit()
        self.db.refresh(new_role)
        return new_role

    # Здесь же будут методы для назначения прав роли, назначения ролей юзеру и т.д.