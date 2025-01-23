import logging
from fastapi import Depends
from typing import List
from models.file_model import File
from db.postgres import AsyncSession, get_postgres_session


logger = logging.getLogger(__name__)

class FileDAO:
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db

    def get_by_workspace( self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        return self.db.query(File).filter(
            File.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()

    def get_by_category( self, category: str, workspace_id: str) -> List[File]:
        return self.db.query(File).filter(
            File.category == category,
            File.workspace_id == workspace_id
        ).all()