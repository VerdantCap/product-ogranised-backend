import logging
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Path, Response
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import uuid
import os

from models.file_model import File as FileModel
from models.folder_model import Folder
from daos.file_dao import FileDAO
from daos.folder_dao import FolderDAO
from daos.workspace_dao import WorkspaceDAO
from models.user_model import User
from services.auth_service import get_current_user
from services.file_service import FileService
from utils.route import APIRouter
from utils.storage import get_file_url
from enums import FileType, ItemSpace
from config import settings

# Create a router for file-related endpoints
file_router = APIRouter()

# Set up a logger for the file controller
logger = logging.getLogger(__name__)

@file_router.get("/")
async def list_files(
    skip: int = Query(0, description="Skip files"),
    limit: int = Query(100, description="Limit files"),
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
):
    """
    Get all files with pagination.
    """
    files = await file_dao.get_multi(skip, limit)
    return {"files": [file.to_dict() for file in files]}

@file_router.get("/workspace")
async def get_files_by_workspace(
    folder_id: Optional[str] = None,
    skip: int = Query(0, description="Skip files"),
    limit: int = Query(100, description="Limit files"),
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
    file_dao: FileDAO = Depends(FileDAO),
    folder_dao: FolderDAO = Depends(FolderDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get files by workspace ID, optionally filtered by folder.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    # Verify the folder exists if provided
    if folder_id:
        folder = await folder_dao.get_by_id(folder_id)
        if not folder or folder.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Folder not found")
    
    # Get subfolders
    folders = await folder_dao.get_by_workspace(workspace_id, folder_id, skip, limit)
    
    # Get files in the folder
    files = await file_dao.get_by_workspace(workspace_id, folder_id, skip, limit)
    
    # Get breadcrumb path if folder_id is provided
    breadcrumbs = []
    if folder_id:
        folder_path = await folder_dao.get_folder_path(folder_id)
        breadcrumbs = [
            {"id": folder.id, "name": folder.name}
            for folder in folder_path
        ]
    else:
        # Root level
        breadcrumbs = [{"id": None, "name": "Root"}]
    
    # Create folder dictionaries manually to avoid lazy loading
    folder_dicts = []
    for folder in folders:
        folder_dicts.append({
            "id": folder.id,
            "name": folder.name,
            "description": folder.description,
            "created_at": folder.created_at.isoformat() if folder.created_at else None,
            "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
            "parent_id": folder.parent_id,
            "workspace_id": folder.workspace_id,
            "owner_id": folder.owner_id,
            "files_count": 0  # Set to 0 to avoid lazy loading
        })
    
    return {
        "folders": folder_dicts,
        "files": [file.to_dict() for file in files],
        "breadcrumbs": breadcrumbs
    }

@file_router.get("/category/{category}")
async def get_files_by_category(
    category: str,
    skip: int = Query(0, description="Skip files"),
    limit: int = Query(100, description="Limit files"),
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get files by category and workspace ID.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    files = await file_dao.get_by_category(category, workspace_id)
    return {"files": [file.to_dict() for file in files]}

@file_router.get("/space/{space}")
async def get_files_by_space(
    space: ItemSpace,
    skip: int = Query(0, description="Skip files"),
    limit: int = Query(100, description="Limit files"),
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get files by space and workspace ID.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    files = await file_dao.get_by_space(space, workspace_id, skip, limit)
    return {"files": [file.to_dict() for file in files]}

@file_router.get("/search")
async def search_files(
    query: str,
    skip: int = Query(0, description="Skip files"),
    limit: int = Query(100, description="Limit files"),
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
    folder_dao: FolderDAO = Depends(FolderDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Search for files and folders by name or description.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    files = await file_dao.search_files(workspace_id, query, skip, limit)
    folders = await folder_dao.search_folders(workspace_id, query, skip, limit)
    
    # Create folder dictionaries manually to avoid lazy loading
    folder_dicts = []
    for folder in folders:
        folder_dicts.append({
            "id": folder.id,
            "name": folder.name,
            "description": folder.description,
            "created_at": folder.created_at.isoformat() if folder.created_at else None,
            "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
            "parent_id": folder.parent_id,
            "workspace_id": folder.workspace_id,
            "owner_id": folder.owner_id,
            "files_count": 0  # Set to 0 to avoid lazy loading
        })
    
    return {
        "files": [file.to_dict() for file in files],
        "folders": folder_dicts
    }

@file_router.get("/{file_id}")
async def get_file(
    file_id: str = Path(..., description="The ID of the file to retrieve"),
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
):
    """
    Get a specific file by ID.
    """
    file = await file_dao.get_by_id(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file.to_dict()

@file_router.get("/{file_id}/url")
async def get_file_url_endpoint(
    file_id: str = Path(..., description="The ID of the file to get URL for"),
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get the URL for a specific file.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    url = await file_service.get_file_url(file_id, workspace_id)
    if not url:
        raise HTTPException(status_code=404, detail="File not found")
    return {"url": url}

@file_router.get("/{file_id}/content")
async def get_file_content(
    file_id: str = Path(..., description="The ID of the file to download"),
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get the content of a specific file.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    # Get the file
    file = await file_service.get_file(file_id, workspace_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine the file path
    if hasattr(settings, 'USE_S3_STORAGE') and settings.USE_S3_STORAGE:
        # For S3 storage, redirect to the S3 URL
        url = get_file_url(file.path)
        return Response(status_code=302, headers={"Location": url})
    else:
        # For local storage, stream the file
        full_path = os.path.join(settings.STORAGE_DIR, file.path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        def iterfile():
            with open(full_path, mode="rb") as file_like:
                yield from file_like
        
        return StreamingResponse(
            iterfile(),
            media_type=file.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file.name}"'
            }
        )

@file_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: str = Form(None),
    category: str = Form(None),
    description: str = Form(None),
    space: ItemSpace = Form(None),
    file_type: FileType = Form(FileType.CERTIFICATE),
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Upload a new file.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    # Determine storage path
    storage_path = f"workspaces/{workspace_id}/files"
    if folder_id:
        storage_path = f"workspaces/{workspace_id}/folders/{folder_id}"
    
    # Store the file directly using the storage utility
    from utils.storage import store_file, get_file_size
    file_path = await store_file(file, storage_path)
    file_size = await get_file_size(file_path)
    
    # Create file record with owner_id set
    file_record = FileModel(
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
        owner_id=user["user_id"],
        version=1  # Set initial version
    )
    
    # Save the file record
    file_record = await file_service.file_dao.create_file(file_record)
    
    return file_record.to_dict()

@file_router.put("/{file_id}")
async def update_file(
    file_id: str = Path(..., description="The ID of the file to update"),
    name: Optional[str] = Form(None),
    folder_id: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    space: Optional[ItemSpace] = Form(None),
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Update a file's metadata.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    # Prepare update data
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if folder_id is not None:
        update_data["folder_id"] = folder_id
    if category is not None:
        update_data["category"] = category
    if description is not None:
        update_data["description"] = description
    if space is not None:
        update_data["space"] = space
    
    # Update the file
    updated_file = await file_service.update_file(file_id, workspace_id, update_data)
    
    return updated_file.to_dict()

@file_router.delete("/{file_id}")
async def delete_file(
    file_id: str = Path(..., description="The ID of the file to delete"),
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Delete a file.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    await file_service.delete_file(file_id, workspace_id)
    return {"detail": "File deleted successfully"}

# Folder endpoints
@file_router.post("/folders")
async def create_folder(
    name: str = Form(...),
    workspace_id: str = Form(None),
    parent_id: str = Form(None),
    description: str = Form(None),
    user: User = Depends(get_current_user),
    folder_dao: FolderDAO = Depends(FolderDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Create a new folder.
    """
    if not workspace_id:
        # Get the user's workspaces
        workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        if not workspaces:
            raise HTTPException(status_code=404, detail="No workspace found for this user")
        
        # Use the first workspace ID
        workspace_id = workspaces[0].id
    
    # Verify parent folder if provided
    if parent_id:
        parent_folder = await folder_dao.get_by_id(parent_id)
        if not parent_folder or parent_folder.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Parent folder not found")
    
    # Create folder
    folder = Folder(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        parent_id=parent_id,
        workspace_id=workspace_id,
        owner_id=user["user_id"]
    )
    
    folder = await folder_dao.create_folder(folder)
    
    # Create a dictionary manually instead of using to_dict() to avoid lazy loading
    return {
        "id": folder.id,
        "name": folder.name,
        "description": folder.description,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
        "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
        "parent_id": folder.parent_id,
        "workspace_id": folder.workspace_id,
        "owner_id": folder.owner_id,
        "files_count": 0  # Set to 0 for new folders
    }

@file_router.get("/folders/{folder_id}")
async def get_folder(
    folder_id: str = Path(..., description="The ID of the folder to retrieve"),
    skip: int = Query(0, description="Skip files"),
    limit: int = Query(100, description="Limit files"),
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
    folder_dao: FolderDAO = Depends(FolderDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get a specific folder and its contents.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    # Verify the folder exists
    folder = await folder_dao.get_by_id(folder_id)
    if not folder or folder.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Get subfolders
    folders = await folder_dao.get_by_workspace(workspace_id, folder_id, skip, limit)
    
    # Get files in the folder
    files = await file_dao.get_by_workspace(workspace_id, folder_id, skip, limit)
    
    # Get breadcrumb path
    folder_path = await folder_dao.get_folder_path(folder_id)
    breadcrumbs = [
        {"id": folder.id, "name": folder.name}
        for folder in folder_path
    ]
    
    # Create folder dictionaries manually to avoid lazy loading
    folder_dicts = []
    for folder in folders:
        folder_dicts.append({
            "id": folder.id,
            "name": folder.name,
            "description": folder.description,
            "created_at": folder.created_at.isoformat() if folder.created_at else None,
            "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
            "parent_id": folder.parent_id,
            "workspace_id": folder.workspace_id,
            "owner_id": folder.owner_id,
            "files_count": 0  # Set to 0 to avoid lazy loading
        })
    
    return {
        "folders": folder_dicts,
        "files": [file.to_dict() for file in files],
        "breadcrumbs": breadcrumbs
    }

@file_router.put("/folders/{folder_id}")
async def update_folder(
    folder_id: str = Path(..., description="The ID of the folder to update"),
    name: Optional[str] = Form(None),
    parent_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    folder_dao: FolderDAO = Depends(FolderDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Update a folder's metadata.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    # Get the folder
    folder = await folder_dao.get_by_id(folder_id)
    if not folder or folder.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Verify parent folder if provided
    if parent_id and parent_id != folder.parent_id:
        # Check for circular reference
        if parent_id == folder_id:
            raise HTTPException(status_code=400, detail="A folder cannot be its own parent")
        
        # Check if parent exists
        parent_folder = await folder_dao.get_by_id(parent_id)
        if not parent_folder or parent_folder.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Parent folder not found")
        
        # Check if the new parent is a descendant of this folder
        parent_path = await folder_dao.get_folder_path(parent_id)
        if any(f.id == folder_id for f in parent_path):
            raise HTTPException(status_code=400, detail="Cannot move a folder to its own descendant")
        
        folder.parent_id = parent_id
    
    # Update fields
    if name is not None:
        folder.name = name
    if description is not None:
        folder.description = description
    
    # Save changes
    folder = await folder_dao.update_folder(folder)
    
    # Create a dictionary manually instead of using to_dict() to avoid lazy loading
    return {
        "id": folder.id,
        "name": folder.name,
        "description": folder.description,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
        "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
        "parent_id": folder.parent_id,
        "workspace_id": folder.workspace_id,
        "owner_id": folder.owner_id,
        "files_count": 0  # Set to 0 to avoid lazy loading
    }

@file_router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str = Path(..., description="The ID of the folder to delete"),
    user: User = Depends(get_current_user),
    folder_dao: FolderDAO = Depends(FolderDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Delete a folder and all its contents.
    """
    # Get the user's workspaces
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        raise HTTPException(status_code=404, detail="No workspace found for this user")
    
    # Use the first workspace ID
    workspace_id = workspaces[0].id
    
    # Get the folder
    folder = await folder_dao.get_by_id(folder_id)
    if not folder or folder.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Delete the folder (cascade will delete subfolders and files)
    await folder_dao.delete_folder(folder)
    
    return {"detail": "Folder deleted successfully"}
