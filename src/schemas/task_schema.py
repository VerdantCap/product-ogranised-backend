from pydantic import BaseModel 
from typing import Optional
from datetime import datetime
from models.workspace_model import Workspace
from models.user_model import User

# Task Related Schemas
class Task(BaseModel):
    id: str
    workspace_id: str
    assignee_id: str
    title: str
    description: Optional[str]
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    assignee: Optional[User]

class TaskCreate(BaseModel):
    workspace_id: str
    assignee_id: str
    title: str
    description: str
    due_at: Optional[datetime]

class TaskUpdate(BaseModel):
    workspace_id: str
    assignee_id: str
    title: str
    description: str
    due_at: Optional[datetime]
    completed_at: Optional[datetime]