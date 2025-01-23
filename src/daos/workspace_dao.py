import logging
from fastapi import Depends
from typing import Optional
from models.workspace_model import Workspace
from models.event_model import Event
from sqlalchemy import and_, delete, exists, select, update
from db.postgres import AsyncSession, get_postgres_session 
from models import Workspace  # Assuming you have a Workspace model
from schemas.workspace_schema import EventCreate  



logger = logging.getLogger(__name__)

class WorkspaceDAO:  
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db

    async def create_workspace(self, workspace: Workspace) -> None:  
        self.db.add(workspace)  

    async def set_spaces(self, workspace: Workspace, selected_spaces: list) -> None: 
        query = (
            update(Workspace)
            .where(Workspace.id == workspace.id)
            .values(space_order=selected_spaces)
        )
        await self.db.execute(query)

    async def get_workspace(self, workspace_id: str) -> Workspace:  
        query = (  
            select(Workspace)  
            .where(Workspace.id == workspace_id)  
        )  
        result: Optional[Workspace]= (await self.db.execute(query)).scalars().first()
        return result
    
    def create_event(self, event_data: EventCreate) -> None:  
        db_event = Event(event_data)  
        self.db.add(db_event)  

    # def maintain_subscription(self):  
    #     was_cancelled = not self.has_active_subscription() or self.on_grace_period()  

    #     self.cancelled_at = None  
    #     self.expires_at = None  
    #     if was_cancelled:  
    #         self.subscription_renewed()  
    #     return self  

    # def cancel_subscription(self, expires_at: datetime):  
    #     was_active = self.has_active_subscription()  
    #     self.cancelled_at = datetime.now()  
    #     self.expires_at = expires_at  
    #     if was_active:  
    #         self.subscription_cancelled()  

    #     return self  



    # def toggle_space(self, space_value: str):  
    #     if space_value in self.spaces_order:  
    #         self.spaces_order.remove(space_value)  
    #     else:  
    #         self.spaces_order.append(space_value)  
    #     return self

    # def is_space_enabled(self, space_value: str) -> bool:  
    #     return space_value in self.spaces_order  

    # def is_valid_space(self, space_value: str) -> bool:  
    #     try:  
    #         ItemSpace(space_value)
    #         return True  
    #     except ValueError:  
    #         return False   