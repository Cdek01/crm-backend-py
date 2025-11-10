# api/endpoints/shares.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from db import models, session
from api.deps import get_current_user
from schemas.shares import ShareCreate, ShareResponse

router = APIRouter()

@router.post("/", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def grant_access(
    share_in: ShareCreate,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Предоставить другому пользователю доступ к своей таблице."""
    # 1. Проверяем, что таблица существует и принадлежит текущему пользователю
    entity_type = db.query(models.EntityType).get(share_in.entity_type_id)
    if not entity_type or entity_type.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Таблица для предоставления доступа не найдена")

    # 2. Проверяем, существует ли пользователь, которому даем доступ
    grantee = db.query(models.User).get(share_in.grantee_user_id)
    if not grantee:
        raise HTTPException(status_code=404, detail="Пользователь для предоставления доступа не найден")

    # 3. Нельзя дать доступ самому себе
    if grantee.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя предоставить доступ самому себе")

    # 4. Проверяем, не был ли доступ уже предоставлен
    existing_share = db.query(models.SharedAccess).filter_by(
        entity_type_id=share_in.entity_type_id,
        grantee_user_id=share_in.grantee_user_id
    ).first()
    if existing_share:
        raise HTTPException(status_code=400, detail="Доступ к этой таблице для данного пользователя уже предоставлен")

    # 5. Создаем запись о доступе
    db_share = models.SharedAccess(
        entity_type_id=share_in.entity_type_id,
        grantee_user_id=share_in.grantee_user_id,
        grantor_user_id=current_user.id,
        permission_level=share_in.permission_level.value
    )
    db.add(db_share)
    db.commit()
    db.refresh(db_share)

    return db_share

@router.get("/entity/{entity_type_id}", response_model=List[ShareResponse])
def get_shares_for_entity(
    entity_type_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить список пользователей, которым предоставлен доступ к таблице."""
    entity_type = db.query(models.EntityType).get(entity_type_id)
    if not entity_type or entity_type.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    shares = db.query(models.SharedAccess).options(
        joinedload(models.SharedAccess.grantee)
    ).filter(
        models.SharedAccess.entity_type_id == entity_type_id
    ).all()

    return shares

@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_access(
    share_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Отозвать доступ к таблице."""
    share_to_delete = db.query(models.SharedAccess).options(
        joinedload(models.SharedAccess.entity_type)
    ).get(share_id)

    if not share_to_delete or share_to_delete.entity_type.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Запись о доступе не найдена")

    db.delete(share_to_delete)
    db.commit()
    return None