import logging
from fastapi import Depends
from typing import Optional, List
from models.workspace_model import Workspace
from models.association_tables import user_workspace
from sqlalchemy import or_, select, update, delete
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime  

# Set up a logger for the WorkspaceDAO
logger = logging.getLogger(__name__)

class WorkspaceDAO:  
    """
    Data Access Object for Workspace.

    This class provides methods to perform CRUD operations on Workspace objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    async def create_workspace(self, workspace: Workspace) -> Workspace:  
        """
        Create a new workspace record in the database.
        Returns the created and refreshed Workspace object.
        """
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def update_workspace(self, workspace: Workspace) -> Workspace:
        """
        Update an existing workspace record in the database.

        Returns the updated Workspace object.
        """
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def delete_workspace(self, workspace_id: str, user_id: str) -> None:
        """
        Delete a workspace record and its associations from the database.
        This includes:
        - Removing entries from user_workspace table
        - Clearing active_workspace_id for users who had this workspace active
        - Removing the workspace record
        """
        
        # First delete from user_workspace table
        delete_associations_query = (
            delete(user_workspace)
            .where(user_workspace.c.workspace_id == workspace_id and user_workspace.c.user_id == user_id)
        )
        await self.db.execute(delete_associations_query)
        
        
        # Finally delete the workspace
        delete_workspace_query = delete(Workspace).where(Workspace.id == workspace_id)
        await self.db.execute(delete_workspace_query)
        
        # Commit all changes
        await self.db.commit()

    async def get_workspace_by_id(self, workspace_id: str) -> Workspace:  
        """
        Retrieve a workspace record by its ID.

        Returns the Workspace object if found, otherwise None.
        """
        query = (  
            select(Workspace)  
            .where(Workspace.id == workspace_id)  
        )  
        result: Optional[Workspace]= (await self.db.execute(query)).scalars().first()
        return result

    async def get_by_owner(self, owner_id: str) -> List[Workspace]:
        """
        Retrieve workspace records by owner ID.

        Returns a list of Workspace objects.
        """
        query = select(Workspace).where(Workspace.owner_id == owner_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_subscriptions(self) -> List[Workspace]:
        """
        Retrieve workspaces with active subscriptions.

        Returns a list of Workspace objects.
        """
        query = select(Workspace).where(
            or_(
                Workspace.expires_at.is_(None),
                Workspace.expires_at > datetime.now()
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def maintain_subscription(self, workspace: Workspace) -> Workspace:
        """
        Maintain a workspace's subscription by clearing cancellation and expiration dates.

        Returns the updated Workspace object.
        """
        workspace.cancelled_at = None
        workspace.expires_at = None
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def cancel_subscription(self, workspace: Workspace, expires_at: datetime) -> Workspace:
        """
        Cancel a workspace's subscription by setting cancellation and expiration dates.

        Returns the updated Workspace object.
        """
        workspace.cancelled_at = datetime.now()
        workspace.expires_at = expires_at
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def set_spaces(self, workspace: Workspace, selected_spaces: list) -> None: 
        """
        Set the order of spaces in a workspace.

        Updates the space_order field in the database.
        """
        query = (
            update(Workspace)
            .where(Workspace.id == workspace.id)
            .values(space_order=selected_spaces)
        )
        await self.db.execute(query)

    async def toggle_space(self, workspace: Workspace, space_value: str) -> Workspace:
        """
        Toggle a space in a workspace's space order.

        Returns the updated Workspace object.
        """
        spaces_order = workspace.spaces_order
        if space_value in spaces_order:
            spaces_order.remove(space_value)
        else:
            spaces_order.append(space_value)
        workspace.spaces_order = spaces_order
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def add_user(self, workspace: Workspace, user_id: str) -> Workspace:
        """
        Add a user to a workspace.

        Returns the updated Workspace object.
        """
        workspace.users.append(user_id)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace
    
    async def remove_user(self, workspace: Workspace, user_id: str) -> Workspace:
        """
        Remove a user from a workspace.

        Returns the updated Workspace object.
        """
        workspace.users.remove(user_id)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace
        
    async def get_workspaces_by_user_id(self, user_id: str) -> List[Workspace]:
        """
        Retrieve all workspaces associated with a user.
        
        This includes workspaces where the user is an owner or a member.
        Returns a list of Workspace objects.
        """
        # Query workspaces where the user is a member (through user_workspace association)
        query = (
            select(Workspace)
            .join(user_workspace, Workspace.id == user_workspace.c.workspace_id)
            .where(user_workspace.c.user_id == user_id)
        )
        result = await self.db.execute(query)
        member_workspaces = result.scalars().all()
        
        # Query workspaces where the user is the owner
        owner_query = select(Workspace).where(Workspace.owner_id == user_id)
        owner_result = await self.db.execute(owner_query)
        owner_workspaces = owner_result.scalars().all()
        
        # Combine and deduplicate results
        all_workspaces = list(set(member_workspaces + owner_workspaces))
        return all_workspaces
