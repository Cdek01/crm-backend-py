from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db import models, session
from schemas.lead import Lead, LeadCreate, LeadUpdate
from api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=Lead, status_code=status.HTTP_201_CREATED)
def create_lead(
        lead_in: LeadCreate,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Создать новый лид. Ответственным автоматически назначается текущий пользователь.
    """
    new_lead = models.Lead(
        **lead_in.model_dump(),
        responsible_user_id=current_user.id
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead


@router.get("/", response_model=List[Lead])
def get_all_leads(
        db: Session = Depends(session.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(get_current_user)
):
    """
    Получить список всех лидов.
    """
    leads = db.query(models.Lead).offset(skip).limit(limit).all()
    return leads


@router.get("/{lead_id}", response_model=Lead)
def get_lead_by_id(
        lead_id: int,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Получить лид по ID.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Лид не найден")
    return lead


@router.put("/{lead_id}", response_model=Lead)
def update_lead(
        lead_id: int,
        lead_in: LeadUpdate,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Обновить информацию о лиде.
    """
    lead_query = db.query(models.Lead).filter(models.Lead.id == lead_id)
    db_lead = lead_query.first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Лид не найден")

    lead_query.update(lead_in.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
        lead_id: int,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Удалить лид.
    """
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Лид не найден")

    db.delete(db_lead)
    db.commit()
    return None