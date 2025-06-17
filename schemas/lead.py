from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class LeadBase(BaseModel):
    organization_name: str
    inn: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    lead_status: Optional[str] = "New"
    rating: Optional[int] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    last_contact_date: Optional[date] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(LeadBase):
    pass

class Lead(LeadBase):
    id: int
    responsible_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True