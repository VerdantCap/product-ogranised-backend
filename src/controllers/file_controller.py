import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional
from uuid import uuid4

from models.file_model import File as FileModel
from daos.file_dao import FileDAO
from models.user_model import User
from services.auth_service import get_current_user
from services.file_service import FileService
from utils.route import APIRouter
from schemas import FileCreate
from enums import FileType

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
    return await file_dao.get_multi(skip, limit)

@file_router.get("/by-workspace/{workspace_id}")
async def get_files_by_workspace(
    workspace_id: str,
    skip: int = Query(0, description="Skip files"),
    limit: int = Query(100, description="Limit files"),
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
):
    """
    Get files by workspace ID.
    """
    return await file_dao.get_by_workspace(workspace_id, skip, limit)

@file_router.get("/by-category/{category}")
async def get_files_by_category(
    category: str,
    workspace_id: str,
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
):
    """
    Get files by category and workspace ID.
    """
    return await file_dao.get_by_category(category, workspace_id)

@file_router.get("/{file_id}")
async def get_file(
    file_id: str,
    user: User = Depends(get_current_user),
    file_dao: FileDAO = Depends(FileDAO),
):
    """
    Get a specific file by ID.
    """
    file = await file_dao.get_by_id(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@file_router.get("/{file_id}/url")
async def get_file_url(
    file_id: str,
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
):
    """
    Get the URL for a specific file.
    """
    workspace_id = user.active_workspace_id
    url = await file_service.get_file_url(file_id, workspace_id)
    if not url:
        raise HTTPException(status_code=404, detail="File not found")
    return {"url": url}

@file_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    workspace_id: str = None,
    folder: str = None,
    category: str = None,
    file_type: FileType = FileType.CERTIFICATE,
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
):
    """
    Upload a new file.
    """
    if not workspace_id:
        workspace_id = user.active_workspace_id
    
    return await file_service.store_and_create_file(file, workspace_id, None)

@file_router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    file_service: FileService = Depends(FileService),
):
    """
    Delete a file.
    """
    await file_service.delete_file(file_id)
    return {"detail": "File deleted successfully"}
