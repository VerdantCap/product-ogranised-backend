from pydantic import BaseModel, field_validator 
from typing import List
from datetime import datetime

# Workspace Related Schemas
class WorkspaceBase(BaseModel):
    id: str
    name: str
    owner_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]
    spaces_order: List[ItemSpace]
    users: List[User]
    items: List["Item"]
    files: List["File"]
    events: List["Event"]
    tasks: List["Task"]

class WorkspaceCreate(BaseModel):
    name: str
    spaces_order: Optional[List[ItemSpace]]

class WorkspaceUpdate(BaseModel):
    name: Optional[str]
    spaces_order: Optional[List[ItemSpace]]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]