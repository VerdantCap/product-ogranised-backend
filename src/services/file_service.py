import logging
from typing import List, Optional
from fastapi import UploadFile
from db.postgres import AsyncSession, get_postgres_session
from schemas.file_schema import File, FileCreate, FileUpdate
from enums import FileType
from daos.file_dao import FileDAO
from utils.storage import store_file

# Set up a logger for the FileService
logger = logging.getLogger(__name__)
class FileService:
    def __init__(self, file_dao: FileDAO = Depends(FileDAO) ):
        self.file_dao = file_dao

    def get_file(self, file_id: str,workspace_id: str) -> Optional[File]:
        file = self.file_dao.get_by_id(file_id)
        if not file or file.workspace_id != workspace_id:
            return None
        return file

    def get_files_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        return self.file_dao.get_by_workspace(workspace_id, skip, limit)

    def get_files_by_category(self, category: str, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        return self.file_dao.get_by_category(category, workspace_id, skip, limit)

    def get_files_by_space(self, space: str, workspace_id: str, skip: int = 0, limit: int = 100) -> List[File]:
        return self.file_dao.get_by_space(space, workspace_id, skip, limit)

    def store_and_create_file(self, file: UploadFile, workspace_id: str) -> File:
        storage_path = (
            f"workspaces/{workspace_id}/items/{item_id}"
            if item_id
            else f"workspaces/{workspace_id}/files"
        )
        file_path = await store_file(file)
        file_data = File(
            workspace_id=workspace_id,
            path=file_path,
            type=file.content_type,
            name=file.filename,
        )
        return self.file_dao.create(file_data)

    async def create_file(self, file_data: FileCreate) -> File:
        return await self.store_and_create_file(file_data.file, file_data.workspace_id)

    async def update_file(self, file_id: str, file_data: FileUpdate) -> File:
        file = self.file_dao.get_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        file_data = File(**file_data.dict(exclude_unset=True))
        return self.file_dao.update(file, file_data)

    async def delete_file(self, file_id: str):
        file = self.file_dao.get_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return self.file_dao.delete(file)