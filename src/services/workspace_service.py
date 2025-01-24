
from fastapi import Depends
from daos.workspace_dao import WorkspaceDAO
from models.workspace_model import Workspace
from schemas.workspace_schema import EventCreate

class WorkspaceService:  
    def __init__(self,
        workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):  
        self.workspace_dao = workspace_dao  

    async def create_workspace(self, name: str, billing_plan: str, stripe_id: str, user_id: int, selected_spaces: list) -> Workspace:  
        workspace = await self.workspace_dao.create_workspace(name, billing_plan, stripe_id, user_id)  
        workspace = await self.workspace_dao.set_spaces(workspace, selected_spaces)  
        return workspace
    
    async def get_workspace(self, workspace_id: str) -> Workspace:
        workspace = await self.workspace_dao.get_workspace(workspace_id)
        return workspace
    
    async def update_workspace(self, workspace: Workspace, selected_spaces:  list) -> Workspace:
        workspace = await self.workspace_dao.set_spaces(workspace, selected_spaces)
        return workspace
    
    async def create_event(self, event_data: EventCreate):  
        return self.event_dao.create_event(event_data)  