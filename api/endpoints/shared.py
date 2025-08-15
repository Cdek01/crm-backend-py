from fastapi import APIRouter, Depends, status
from db import models, session
from schemas.shared import SharedEntityTypeCreate
from api.deps import get_current_user
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def share_entity_type(
        share_in: SharedEntityTypeCreate,
        db: Session = Depends(session.get_db),
        current_user: models.User = Depends(get_current_user)
):
    # В реальном приложении здесь должна быть проверка, что current_user - суперадмин
    # if not current_user.is_superuser: raise HTTPException(...)

    db_share = models.SharedEntityType(**share_in.dict())
    db.add(db_share)
    db.commit()
    return {"status": "ok"}