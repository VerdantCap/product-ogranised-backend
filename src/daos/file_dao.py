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

    def create_file(self, file: File):
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def update_file(self, file: File):
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def delete_file(self, file: File):
        self.db.delete(file)
        self.db.commit()

    def get_by_id( self, file_id: str) -> File:
        return self.db.query(File).filter(
            File.id == file_id
        ).first()

    def get_by_workspace( self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        return self.db.query(File).filter(
            File.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()

    def get_by_category( self, category: str, workspace_id: str) -> List[File]:
        return self.db.query(File).filter(
            File.category == category,
            File.workspace_id == workspace_id
        ).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[File]:
        return self.db.query(File).offset(skip).limit(limit).all()