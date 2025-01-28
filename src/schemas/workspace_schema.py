from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enums import ItemSpace
# Workspace Related Schemas
class Workspace(BaseModel):
    id: str
    name: str
    owner_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]
    spaces_order: List[ItemSpace]

class WorkspaceCreate(BaseModel):
    name: str
    spaces_order: Optional[List[ItemSpace]]

class WorkspaceUpdate(BaseModel):
    name: Optional[str]
    spaces_order: Optional[List[ItemSpace]]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]