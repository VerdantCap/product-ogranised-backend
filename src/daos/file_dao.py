import logging
from fastapi import Depends
from typing import List, Optional
from sqlalchemy import select, func, desc
from models.file_model import File
from enums import ItemSpace
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

    async def create_file(self, file: File):
        """
        Create a new file record in the database.

        Returns the created File object.
        """
        self.db.add(file)
        await self.db.commit()
        await self.db.refresh(file)
        return file

    async def update_file(self, file: File):
        """
        Update an existing file record in the database.

        Returns the updated File object.
        """
        self.db.add(file)
        await self.db.commit()
        await self.db.refresh(file)
        return file

    async def delete_file(self, file: File):
        """
        Delete a file record from the database.
        """
        self.db.delete(file)
        await self.db.commit()

    async def get_by_id(self, file_id: str) -> Optional[File]:
        """
        Retrieve a file record by its ID.

        Returns the File object if found, otherwise None.
        """
        query = select(File).where(File.id == file_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_workspace(self, workspace_id: str, folder_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Retrieve file records by workspace ID with pagination.
        Optionally filter by folder_id.

        Returns a list of File objects.
        """
        query = select(File).where(File.workspace_id == workspace_id)
        
        # If folder_id is provided, filter by it
        # If folder_id is None, get files at the root level (no folder)
        if folder_id is not None:
            query = query.where(File.folder_id == folder_id)
        else:
            query = query.where(File.folder_id == None)
            
        query = query.order_by(desc(File.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_category(self, category: str, workspace_id: str) -> List[File]:
        """
        Retrieve file records by category and workspace ID.

        Returns a list of File objects.
        """
        query = select(File).where(
            File.category == category,
            File.workspace_id == workspace_id
        ).order_by(desc(File.created_at))
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_space(self, space: ItemSpace, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Retrieve file records by space and workspace ID.

        Returns a list of File objects.
        """
        query = select(File).where(
            File.space == space,
            File.workspace_id == workspace_id
        ).order_by(desc(File.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_files(self, workspace_id: str, search_term: str, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Search for files by name or description.

        Returns a list of File objects.
        """
        search_pattern = f"%{search_term}%"
        query = select(File).where(
            File.workspace_id == workspace_id,
            (File.name.ilike(search_pattern) | File.description.ilike(search_pattern))
        ).order_by(desc(File.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Retrieve multiple file records with pagination.

        Returns a list of File objects.
        """
        query = select(File).order_by(desc(File.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_file_count_by_folder(self, folder_id: str) -> int:
        """
        Get the count of files in a folder.

        Returns the count as an integer.
        """
        query = select(func.count()).select_from(File).where(File.folder_id == folder_id)
        result = await self.db.execute(query)
        return result.scalar()
    
    async def get_file_count_by_workspace(self, workspace_id: str) -> int:
        """
        Get the count of files in a workspace.

        Returns the count as an integer.
        """
        query = select(func.count()).select_from(File).where(File.workspace_id == workspace_id)
        result = await self.db.execute(query)
        return result.scalar()
