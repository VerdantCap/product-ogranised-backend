import logging
import uuid
from fastapi import Depends, HTTPException
from sqlalchemy import select, update, delete
from db.postgres import AsyncSession, get_postgres_session
from models.space_model import Space
from typing import List, Optional

# Set up a logger for the SpaceDAO
logger = logging.getLogger(__name__)

class SpaceDAO:
    """
    Data Access Object for Space.

    This class provides methods to perform CRUD operations on Space objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    async def create_space(self, space: Space) -> Space:
        """
        Create a new space record in the database.
        Returns the created and refreshed Space object.
        """
        self.db.add(space)
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def get_space_by_id(self, space_id: str) -> Optional[Space]:
        """
        Retrieve a space record by its ID.
        Returns the Space object if found, otherwise None.
        """
        query = select(Space).where(Space.id == space_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_spaces_by_workspace_id(self, workspace_id: str) -> List[Space]:
        """
        Retrieve all spaces for a specific workspace.
        Returns a list of Space objects.
        """
        query = select(Space).where(Space.workspace_id == workspace_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_spaces_by_user_id(self, user_id: str) -> List[Space]:
        """
        Retrieve all spaces for a specific user.
        Returns a list of Space objects.
        """
        query = select(Space).where(Space.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_spaces_by_workspace_and_user(self, workspace_id: str, user_id: str) -> List[Space]:
        """
        Retrieve all spaces for a specific workspace and user.
        Returns a list of Space objects.
        """
        query = select(Space).where(
            (Space.workspace_id == workspace_id) & 
            (Space.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_space_by_type_workspace_user(self, spacetype: str, workspace_id: str, user_id: str) -> Optional[Space]:
        """
        Retrieve a space by its type, workspace ID, and user ID.
        Returns the Space object if found, otherwise None.
        """
        query = select(Space).where(
            (Space.spacetype == spacetype) & 
            (Space.workspace_id == workspace_id) & 
            (Space.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_space(self, space: Space) -> Space:
        """
        Update an existing space record in the database.
        Returns the updated Space object.
        """
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def toggle_space_status(self, space: Space) -> Space:
        """
        Toggle the status of a space.
        Returns the updated Space object.
        """
        space.status = not space.status
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def delete_space(self, space_id: str) -> None:
        """
        Delete a space record from the database.
        """
        delete_query = delete(Space).where(Space.id == space_id)
        await self.db.execute(delete_query)
        await self.db.commit()

    async def create_or_toggle_space(self, spacetype: str, workspace_id: str, user_id: str) -> Space:
        """
        Create a new space if it doesn't exist, or toggle its status if it does.
        Returns the created or updated Space object.
        """
        # Check if the space already exists
        space = await self.get_space_by_type_workspace_user(spacetype, workspace_id, user_id)
        
        if space:
            # Toggle the status if the space exists
            return await self.toggle_space_status(space)
        else:
            # Create a new space if it doesn't exist
            space_id = f"space_{str(uuid.uuid4())}"
            new_space = Space(
                id=space_id,
                spacetype=spacetype,
                workspace_id=workspace_id,
                user_id=user_id,
                status=True  # New spaces are enabled by default
            )
            return await self.create_space(new_space)

    async def get_enabled_spaces(self, workspace_id: str, user_id: str) -> List[str]:
        """
        Get a list of enabled space types for a specific workspace and user.
        Returns a list of space type strings.
        """
        spaces = await self.get_spaces_by_workspace_and_user(workspace_id, user_id)
        return [space.spacetype for space in spaces if space.status]
