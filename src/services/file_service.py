import logging
import uuid
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, Depends, HTTPException
from models.file_model import File
from daos.file_dao import FileDAO
from daos.folder_dao import FolderDAO
from utils.storage import store_file, delete_file, get_file_url, get_file_size
from enums import FileType, ItemSpace
from config import settings

# Set up a logger for the FileService
logger = logging.getLogger(__name__)

class FileService:
    def __init__(
        self, 
        file_dao: FileDAO = Depends(FileDAO),
        folder_dao: FolderDAO = Depends(FolderDAO)
    ):
        self.file_dao = file_dao
        self.folder_dao = folder_dao

    async def get_file(self, file_id: str, workspace_id: str) -> Optional[File]:
        """
        Get a file by ID and verify it belongs to the specified workspace.
        
        Args:
            file_id: The ID of the file
            workspace_id: The ID of the workspace
            
        Returns:
            File: The file object if found, otherwise None
        """
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
        return f"/api/files/{file.id}/content"

    async def get_files_by_workspace(self, workspace_id: str, folder_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Get files by workspace ID, optionally filtered by folder.
        
        Args:
            workspace_id: The ID of the workspace
            folder_id: Optional folder ID to filter by
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            List[File]: List of file objects
        """
        return await self.file_dao.get_by_workspace(workspace_id, folder_id, skip, limit)

    async def get_files_by_category(self, category: str, workspace_id: str) -> List[File]:
        """
        Get files by category and workspace ID.
        
        Args:
            category: The category to filter by
            workspace_id: The ID of the workspace
            
        Returns:
            List[File]: List of file objects
        """
        return await self.file_dao.get_by_category(category, workspace_id)

    async def get_files_by_space(self, space: ItemSpace, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Get files by space and workspace ID.
        
        Args:
            space: The space to filter by
            workspace_id: The ID of the workspace
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            List[File]: List of file objects
        """
        return await self.file_dao.get_by_space(space, workspace_id, skip, limit)

    async def search_files(self, workspace_id: str, search_term: str, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Search for files by name or description.
        
        Args:
            workspace_id: The ID of the workspace
            search_term: The search term to look for
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            List[File]: List of file objects matching the search
        """
        return await self.file_dao.search_files(workspace_id, search_term, skip, limit)

    async def store_and_create_file(
        self, 
        file: UploadFile, 
        workspace_id: str, 
        folder_id: Optional[str] = None,
        category: Optional[str] = None,
        space: Optional[ItemSpace] = None,
        description: Optional[str] = None,
        file_type: Optional[FileType] = None
    ) -> File:
        """
        Store a file and create a database record for it.
        
        Args:
            file: The uploaded file
            workspace_id: The ID of the workspace
            folder_id: Optional folder ID to store the file in
            category: Optional category for the file
            space: Optional space for the file
            description: Optional description for the file
            file_type: Optional file type
            
        Returns:
            File: The created file object
        """
        # Verify the folder exists if provided
        if folder_id:
            folder = await self.folder_dao.get_by_id(folder_id)
            if not folder or folder.workspace_id != workspace_id:
                raise HTTPException(status_code=404, detail="Folder not found")
        
        # Determine storage path
        storage_path = f"workspaces/{workspace_id}/files"
        if folder_id:
            storage_path = f"workspaces/{workspace_id}/folders/{folder_id}"
        
        # Store the file
        file_path = await store_file(file, storage_path)
        
        # Get file size
        file_size = await get_file_size(file_path)
        
        # Determine file type if not provided
        if not file_type:
            file_type = FileType.CERTIFICATE  # Default type
        
        # Create file record
        file_record = File(
            id=str(uuid.uuid4()),
            name=file.filename,
            path=file_path,
            mime_type=file.content_type,
            size=file_size,
            description=description,
            workspace_id=workspace_id,
            folder_id=folder_id,
            category=category,
            space=space,
            type=file_type,
            owner_id=None  # This will be set by the controller
        )
        
        return await self.file_dao.create_file(file_record)

    async def update_file(
        self, 
        file_id: str, 
        workspace_id: str,
        update_data: Dict[str, Any]
    ) -> File:
        """
        Update a file's metadata.
        
        Args:
            file_id: The ID of the file to update
            workspace_id: The ID of the workspace
            update_data: Dictionary of fields to update
            
        Returns:
            File: The updated file object
        """
        file = await self.get_file(file_id, workspace_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Handle folder change
        if 'folder_id' in update_data and update_data['folder_id'] != file.folder_id:
            new_folder_id = update_data['folder_id']
            old_folder_id = file.folder_id
            
            # If moving to a folder, verify the new folder exists
            if new_folder_id:
                folder = await self.folder_dao.get_by_id(new_folder_id)
                if not folder or folder.workspace_id != workspace_id:
                    raise HTTPException(status_code=404, detail="Folder not found")
                
                # Get the new folder path for hierarchical storage
                folder_path = await self.folder_dao.get_folder_path(new_folder_id)
                folder_path_str = "/".join([f.id for f in folder_path])
                new_storage_path = f"workspaces/{workspace_id}/folders/{folder_path_str}"
            else:
                # Moving to root
                new_storage_path = f"workspaces/{workspace_id}/files"
            
            # Move the file to the new location
            from utils.storage import store_file, delete_file, get_file_url, get_file_size
            import os
            from fastapi import UploadFile
            
            # Get the file content
            old_path = file.path
            file_name = os.path.basename(old_path)
            
            # Create a new path for the file
            new_path = f"{new_storage_path}/{file_name}"
            
            # Update the file path
            file.path = new_path
            file.folder_id = new_folder_id
        
        # Update other fields
        for key, value in update_data.items():
            if key != 'folder_id' and hasattr(file, key):
                setattr(file, key, value)
        
        # Increment version
        file.version += 1
        
        return await self.file_dao.update_file(file)

    async def delete_file(self, file_id: str, workspace_id: str):
        """
        Delete a file.
        
        Args:
            file_id: The ID of the file to delete
            workspace_id: The ID of the workspace
        """
        file = await self.get_file(file_id, workspace_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete the file from storage
        delete_file(file.path)
        
        # Delete the file record from the database
        return await self.file_dao.delete_file(file)
    
    async def get_folder_contents(self, folder_id: str, workspace_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get the contents of a folder (subfolders and files).
        
        Args:
            folder_id: The ID of the folder
            workspace_id: The ID of the workspace
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            Dict: Dictionary containing folders and files
        """
        # Verify the folder exists if provided
        if folder_id:
            folder = await self.folder_dao.get_by_id(folder_id)
            if not folder or folder.workspace_id != workspace_id:
                raise HTTPException(status_code=404, detail="Folder not found")
        
        # Get subfolders
        folders = await self.folder_dao.get_by_workspace(workspace_id, folder_id, skip, limit)
        
        # Get files in the folder
        files = await self.file_dao.get_by_workspace(workspace_id, folder_id, skip, limit)
        
        # Get breadcrumb path if folder_id is provided
        breadcrumbs = []
        if folder_id:
            folder_path = await self.folder_dao.get_folder_path(folder_id)
            breadcrumbs = [
                {"id": folder.id, "name": folder.name}
                for folder in folder_path
            ]
        else:
            # Root level
            breadcrumbs = [{"id": None, "name": "Documents"}]
        
        # Get file counts for each folder
        folder_dicts = []
        for folder in folders:
            file_count = await self.file_dao.get_file_count_by_folder(folder.id)
            folder_dict = folder.to_dict()
            folder_dict["files_count"] = file_count
            folder_dicts.append(folder_dict)
        
        return {
            "folders": folder_dicts,
            "files": [file.to_dict() for file in files],
            "breadcrumbs": breadcrumbs
        }
