import logging
from fastapi import Depends
from typing import Optional, List
from models.workspace_model import Workspace
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

    async def create_workspace(self, workspace: Workspace) -> None:  
        """
        Create a new workspace record in the database.
        """
        self.db.add(workspace)

    async def update_workspace(self, workspace: Workspace) -> Workspace:
        """
        Update an existing workspace record in the database.

        Returns the updated Workspace object.
        """
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    async def delete_workspace(self, workspace_id: str) -> None:
        """
        Delete a workspace record from the database by workspace ID.
        """
        query = delete(Workspace).where(Workspace.id == workspace_id)
        await self.db.execute(query)

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

    def get_by_owner(self, owner_id: str) -> List[Workspace]:
        """
        Retrieve workspace records by owner ID.

        Returns a list of Workspace objects.
        """
        return self.db.query(Workspace).filter(Workspace.owner_id == owner_id).all()

    async def get_active_subscriptions(self) -> List[Workspace]:
        """
        Retrieve workspaces with active subscriptions.

        Returns a list of Workspace objects.
        """
        return self.db.query(Workspace).filter(
            or_(
                Workspace.expires_at.is_(None),
                Workspace.expires_at > datetime.now()
            )
        ).all()

    async def maintain_subscription(self, workspace: Workspace) -> Workspace:
        """
        Maintain a workspace's subscription by clearing cancellation and expiration dates.

        Returns the updated Workspace object.
        """
        workspace.cancelled_at = None
        workspace.expires_at = None
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def cancel_subscription(self, workspace: Workspace, expires_at: datetime) -> Workspace:
        """
        Cancel a workspace's subscription by setting cancellation and expiration dates.

        Returns the updated Workspace object.
        """
        workspace.cancelled_at = datetime.now()
        workspace.expires_at = expires_at
        self.db.commit()
        self.db.refresh(workspace)
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

    def toggle_space(self, workspace: Workspace, space_value: str) -> Workspace:
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
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def add_user(self, workspace: Workspace, user_id: str) -> Workspace:
        """
        Add a user to a workspace.

        Returns the updated Workspace object.
        """
        workspace.users.append(user_id)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace
    
    def remove_user(self, workspace: Workspace, user_id: str) -> Workspace:
        """
        Remove a user from a workspace.

        Returns the updated Workspace object.
        """
        workspace.users.remove(user_id)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace
