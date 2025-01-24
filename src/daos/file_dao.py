import logging
from fastapi import Depends
from typing import List
from models.file_model import File
from db.postgres import AsyncSession, get_postgres_session

# Set up a logger for the FileDAO
logger = logging.getLogger(__name__)

class FileDAO:
    """
    Data Access Object for File.

    This class provides methods to perform CRUD operations on File objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    def create_file(self, file: File):
        """
        Create a new file record in the database.

        Returns the created File object.
        """
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def update_file(self, file: File):
        """
        Update an existing file record in the database.

        Returns the updated File object.
        """
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def delete_file(self, file: File):
        """
        Delete a file record from the database.
        """
        self.db.delete(file)
        self.db.commit()

    def get_by_id(self, file_id: str) -> File:
        """
        Retrieve a file record by its ID.

        Returns the File object if found, otherwise None.
        """
        return self.db.query(File).filter(
            File.id == file_id
        ).first()

    def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Retrieve file records by workspace ID with pagination.

        Returns a list of File objects.
        """
        return self.db.query(File).filter(
            File.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()

    def get_by_category(self, category: str, workspace_id: str) -> List[File]:
        """
        Retrieve file records by category and workspace ID.

        Returns a list of File objects.
        """
        return self.db.query(File).filter(
            File.category == category,
            File.workspace_id == workspace_id
        ).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Retrieve multiple file records with pagination.

        Returns a list of File objects.
        """
        return self.db.query(File).offset(skip).limit(limit).all()
