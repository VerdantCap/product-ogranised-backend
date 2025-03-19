import logging
from fastapi import Depends
from typing import List, Optional
from sqlalchemy import select, func, desc
from models.folder_model import Folder
from db.postgres import AsyncSession, get_postgres_session

# Set up a logger for the FolderDAO
logger = logging.getLogger(__name__)

class FolderDAO:
    """
    Data Access Object for Folder.

    This class provides methods to perform CRUD operations on Folder objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    async def create_folder(self, folder: Folder):
        """
        Create a new folder record in the database.

        Returns the created Folder object.
        """
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        return folder

    async def update_folder(self, folder: Folder):
        """
        Update an existing folder record in the database.

        Returns the updated Folder object.
        """
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        return folder

    async def delete_folder(self, folder: Folder):
        """
        Delete a folder record from the database.
        """
        self.db.delete(folder)
        await self.db.commit()

    async def get_by_id(self, folder_id: str) -> Optional[Folder]:
        """
        Retrieve a folder record by its ID.

        Returns the Folder object if found, otherwise None.
        """
        query = select(Folder).where(Folder.id == folder_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_workspace(self, workspace_id: str, parent_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Folder]:
        """
        Retrieve folder records by workspace ID with pagination.
        Optionally filter by parent_id.

        Returns a list of Folder objects.
        """
        query = select(Folder).where(Folder.workspace_id == workspace_id)
        
        # If parent_id is provided, filter by it
        # If parent_id is None, get folders at the root level (no parent)
        if parent_id is not None:
            query = query.where(Folder.parent_id == parent_id)
        else:
            query = query.where(Folder.parent_id == None)
            
        query = query.order_by(desc(Folder.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_folder_path(self, folder_id: str) -> List[Folder]:
        """
        Get the path of folders from root to the specified folder.

        Returns a list of Folder objects representing the path.
        """
        path = []
        current_folder = await self.get_by_id(folder_id)
        
        while current_folder:
            path.insert(0, current_folder)
            if current_folder.parent_id:
                current_folder = await self.get_by_id(current_folder.parent_id)
            else:
                break
                
        return path

    async def search_folders(self, workspace_id: str, search_term: str, skip: int = 0, limit: int = 100) -> List[Folder]:
        """
        Search for folders by name or description.

        Returns a list of Folder objects.
        """
        search_pattern = f"%{search_term}%"
        query = select(Folder).where(
            Folder.workspace_id == workspace_id,
            (Folder.name.ilike(search_pattern) | Folder.description.ilike(search_pattern))
        ).order_by(desc(Folder.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Folder]:
        """
        Retrieve multiple folder records with pagination.

        Returns a list of Folder objects.
        """
        query = select(Folder).order_by(desc(Folder.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_subfolder_count(self, folder_id: str) -> int:
        """
        Get the count of subfolders in a folder.

        Returns the count as an integer.
        """
        query = select(func.count()).select_from(Folder).where(Folder.parent_id == folder_id)
        result = await self.db.execute(query)
        return result.scalar()
    
    async def get_folder_count_by_workspace(self, workspace_id: str) -> int:
        """
        Get the count of folders in a workspace.

        Returns the count as an integer.
        """
        query = select(func.count()).select_from(Folder).where(Folder.workspace_id == workspace_id)
        result = await self.db.execute(query)
        return result.scalar()
