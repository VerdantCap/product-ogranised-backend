import logging
from fastapi import Depends, HTTPException
from typing import Optional, List, Dict, Any, Tuple
from models.workspace_model import Workspace
from models.user_model import User
from models.association_tables import user_workspace
from sqlalchemy import or_, select, update, delete, join
from sqlalchemy.orm import joinedload
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime
from enums import WorkspaceRole

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

    async def set_spaces(self, workspace: Workspace, selected_spaces: list) -> Workspace: 
        """
        Set the order of spaces in a workspace.

        Updates the spaces_order field in the database.
        Returns the updated Workspace object.
        """
        workspace.spaces_order = selected_spaces
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def toggle_space(self, workspace: Workspace, space_value: str) -> Workspace:
        """
        Toggle a space in a workspace's space order.

        Returns the updated Workspace object.
        """
        # Ensure space_value is a valid ItemSpace value
        from enums import ItemSpace
        valid_spaces = [space.value for space in ItemSpace]
        if space_value not in valid_spaces:
            raise HTTPException(
                status_code=422, 
                detail=f"Invalid space value: {space_value}. Valid values are: {', '.join(valid_spaces)}"
            )
            
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
        
    async def get_workspace_members(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all members of a workspace with their roles.
        
        Returns a list of dictionaries containing user information and their role in the workspace.
        """
        # Query to get all users associated with the workspace
        query = (
            select(User, user_workspace.c.role)
            .join(user_workspace, User.id == user_workspace.c.user_id)
            .where(user_workspace.c.workspace_id == workspace_id)
        )
        result = await self.db.execute(query)
        
        # Get the workspace to check the owner
        workspace = await self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        members = []
        for user, role in result:
            # If the user is the owner, set role to 'owner' regardless of what's in the association table
            if user.id == workspace.owner_id:
                role = WorkspaceRole.OWNER.value
                
            members.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": role,
                "avatar_url": user.avatar_url
            })
            
        return members
    
    async def add_workspace_member(self, workspace_id: str, user_id: str, role: str = WorkspaceRole.VIEWER.value) -> None:
        """
        Add a user to a workspace with a specific role.
        
        Args:
            workspace_id: The ID of the workspace
            user_id: The ID of the user to add
            role: The role to assign to the user (default: viewer)
        """
        # Check if the user is already a member
        query = (
            select(user_workspace)
            .where(
                (user_workspace.c.workspace_id == workspace_id) & 
                (user_workspace.c.user_id == user_id)
            )
        )
        result = await self.db.execute(query)
        existing = result.first()
        
        if existing:
            # User is already a member, update their role
            update_query = (
                update(user_workspace)
                .where(
                    (user_workspace.c.workspace_id == workspace_id) & 
                    (user_workspace.c.user_id == user_id)
                )
                .values(role=role, updated_at=datetime.utcnow())
            )
            await self.db.execute(update_query)
        else:
            # Add the user to the workspace with the specified role
            insert_query = user_workspace.insert().values(
                user_id=user_id,
                workspace_id=workspace_id,
                role=role,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await self.db.execute(insert_query)
        
        await self.db.commit()
    
    async def remove_workspace_member(self, workspace_id: str, user_id: str) -> None:
        """
        Remove a user from a workspace.
        
        Args:
            workspace_id: The ID of the workspace
            user_id: The ID of the user to remove
        """
        # Get the workspace to check if the user is the owner
        workspace = await self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        # Cannot remove the owner
        if user_id == workspace.owner_id:
            raise HTTPException(
                status_code=400, 
                detail="Cannot remove the workspace owner. Transfer ownership first."
            )
        
        # Remove the user from the workspace
        delete_query = (
            delete(user_workspace)
            .where(
                (user_workspace.c.workspace_id == workspace_id) & 
                (user_workspace.c.user_id == user_id)
            )
        )
        await self.db.execute(delete_query)
        await self.db.commit()
    
    async def update_member_role(self, workspace_id: str, user_id: str, role: str) -> None:
        """
        Update a user's role in a workspace.
        
        Args:
            workspace_id: The ID of the workspace
            user_id: The ID of the user
            role: The new role to assign
        """
        # Get the workspace to check if the user is the owner
        workspace = await self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        # Cannot change the owner's role
        if user_id == workspace.owner_id and role != WorkspaceRole.OWNER.value:
            raise HTTPException(
                status_code=400, 
                detail="Cannot change the workspace owner's role. Transfer ownership first."
            )
        
        # Update the user's role
        update_query = (
            update(user_workspace)
            .where(
                (user_workspace.c.workspace_id == workspace_id) & 
                (user_workspace.c.user_id == user_id)
            )
            .values(role=role, updated_at=datetime.utcnow())
        )
        await self.db.execute(update_query)
        await self.db.commit()
    
    async def transfer_ownership(self, workspace_id: str, current_owner_id: str, new_owner_id: str) -> None:
        """
        Transfer ownership of a workspace from one user to another.
        
        Args:
            workspace_id: The ID of the workspace
            current_owner_id: The ID of the current owner
            new_owner_id: The ID of the new owner
        """
        # Get the workspace
        workspace = await self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        # Verify the current owner
        if workspace.owner_id != current_owner_id:
            raise HTTPException(status_code=403, detail="Only the workspace owner can transfer ownership")
        
        # Update the workspace owner
        workspace.owner_id = new_owner_id
        
        # Update the roles in the association table
        # Set the new owner's role to 'owner'
        await self.update_member_role(workspace_id, new_owner_id, WorkspaceRole.OWNER.value)
        
        # Set the previous owner's role to 'admin'
        await self.update_member_role(workspace_id, current_owner_id, WorkspaceRole.ADMIN.value)
        
        await self.db.commit()
        await self.db.refresh(workspace)
