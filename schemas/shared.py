from pydantic import BaseModel

class SharedEntityTypeCreate(BaseModel):
    user_id: int
    entity_type_id: int