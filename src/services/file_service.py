import logging
from typing import List, Optional
from fastapi import UploadFile, Depends, HTTPException
from schemas import File, FileCreate, FileUpdate
from daos.file_dao import FileDAO
from utils.storage import store_file, delete_file, get_file_url
from config import settings

# Set up a logger for the FileService
logger = logging.getLogger(__name__)
class FileService:
    def __init__(self, file_dao: FileDAO = Depends(FileDAO) ):
        self.file_dao = file_dao

    async def get_file(self, file_id: str, workspace_id: str) -> Optional[File]:
        file = await self.file_dao.get_by_id(file_id)
        if not file or file.workspace_id != workspace_id:
            return None
        return file

    async def get_file_url(self, file_id: str, workspace_id: str) -> Optional[str]:
        """
        Get the URL for a file.
        
        Args:
            file_id: The ID of the file
            workspace_id: The ID of the workspace
            
        Returns:
            str: The URL to access the file, or None if the file doesn't exist
        """
        file = await self.get_file(file_id, workspace_id)
        if not file:
            return None
        
        # If using S3 storage, return the S3 URL
        if hasattr(settings, 'USE_S3_STORAGE') and settings.USE_S3_STORAGE:
            return get_file_url(file.path)
        
        # Otherwise, construct a URL to the local file
        return f"/files/{file.id}"

    async def get_files_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        return await self.file_dao.get_by_workspace(workspace_id, skip, limit)

    async def get_files_by_category(self, category: str, workspace_id: str) -> List[File]:
        return await self.file_dao.get_by_category(category, workspace_id)

    async def get_files_by_space(self, space: str, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        # This method needs to be implemented in the DAO or removed if not used
        raise NotImplementedError("get_by_space method not implemented in FileDAO")

    async def store_and_create_file(self, file: UploadFile, workspace_id: str, item_id: Optional[str]) -> File:
        storage_path = (
            f"workspaces/{workspace_id}/items/{item_id}"
            if item_id
            else f"workspaces/{workspace_id}/files"
        )
        file_path = await store_file(file, storage_path)
        file_data = File(
            workspace_id=workspace_id,
            path=file_path,
            type=file.content_type,
            name=file.filename,
        )
        return await self.file_dao.create_file(file_data)

    async def create_file(self, file_data: FileCreate) -> File:
        return await self.store_and_create_file(file_data.file, file_data.workspace_id)

    async def update_file(self, file_id: str, file_data: FileUpdate) -> File:
        file = await self.file_dao.get_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        for key, value in file_data.dict(exclude_unset=True).items():
            setattr(file, key, value)
        return await self.file_dao.update_file(file)

    async def delete_file(self, file_id: str):
        file = await self.file_dao.get_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete the file from storage
        delete_file(file.path)
        
        # Delete the file record from the database
        return await self.file_dao.delete_file(file)
