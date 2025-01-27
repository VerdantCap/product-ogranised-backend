from pydantic import BaseModel 
from typing import Optional
from models.workspace_model import Workspace

class Event(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    name: str
    description: Optional[str]
    start_at: str
    end_at: str

class EventCreate(BaseModel):
    name: str
    description: Optional[str]
    start_at: str
    end_at: str

class EventUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    start_at: Optional[str]
    end_at: Optional[str]
