from pydantic import BaseModel 
from typing import Optional
from enums import FileType

class FileCreate(BaseModel):
    workspace_id: str
    path: str
    type: str
    folder: Optional[str]
    category: Optional[str]

class FileUpdate(BaseModel):
    path: str
    type: str
    folder: Optional[str]
    category: Optional[FileType]

class File(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    path: str
    type: str
    folder: Optional[str]
    category: Optional[str]