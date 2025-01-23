from pydantic import BaseModel 
from typing import Optional
from models.workspace_model import Workspace

class Event(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    name: str
    description: Optional[str]
    workspace: Workspace

class EventCreate(BaseModel):
    workspace_id: str
    name: str
    description: Optional[str]

class EventUpdate(BaseModel):
    id: str
    name: str
    description: Optional[str]
