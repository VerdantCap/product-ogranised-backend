import logging
from fastapi import Depends
from typing import List, Optional
from sqlalchemy import asc, desc
from uuid import uuid4
from datetime import datetime

from models.activity_model import Activity
from db.postgres import AsyncSession, get_postgres_session

# Set up a logger for the ActivityDAO
logger = logging.getLogger(__name__)

class ActivityDAO:
    """
    Data Access Object for Activity.

    This class provides methods to perform CRUD operations on Activity objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    async def create_activity(self, user_id: str, workspace_id: str, activity_type: str, 
                        entity_id: Optional[str] = None, entity_type: Optional[str] = None, 
                        details: Optional[dict] = None) -> Activity:
        """
        Create a new activity record in the database.

        Returns the created Activity object.
        """
        activity = Activity(
            id=str(uuid4()),
            user_id=user_id,
            workspace_id=workspace_id,
            type=activity_type,
            entity_id=entity_id,
            entity_type=entity_type,
            details=details or {},
            created_at=datetime.now()
        )
        
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def get_by_id(self, activity_id: str) -> Optional[Activity]:
        """
        Retrieve an activity record by its ID.

        Returns the Activity object if found, otherwise None.
        """
        from sqlalchemy import select
        query = select(Activity).where(Activity.id == activity_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Activity]:
        """
        Retrieve activity records by workspace ID with pagination.

        Returns a list of Activity objects.
        """
        from sqlalchemy import select
        query = select(Activity).where(
            Activity.workspace_id == workspace_id
        ).order_by(desc(Activity.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user(self, user_id: str, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Activity]:
        """
        Retrieve activity records by user ID and workspace ID with pagination.

        Returns a list of Activity objects.
        """
        from sqlalchemy import select
        query = select(Activity).where(
            Activity.user_id == user_id,
            Activity.workspace_id == workspace_id
        ).order_by(desc(Activity.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_entity(self, entity_id: str, entity_type: str, skip: int = 0, limit: int = 100) -> List[Activity]:
        """
        Retrieve activity records by entity ID and entity type with pagination.

        Returns a list of Activity objects.
        """
        from sqlalchemy import select
        query = select(Activity).where(
            Activity.entity_id == entity_id,
            Activity.entity_type == entity_type
        ).order_by(desc(Activity.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_activities(self, workspace_id: str, limit: int = 10) -> List[Activity]:
        """
        Retrieve recent activity records by workspace ID.

        Returns a list of Activity objects ordered by creation date.
        """
        from sqlalchemy import select
        query = select(Activity).where(
            Activity.workspace_id == workspace_id
        ).order_by(desc(Activity.created_at)).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_activity(self, activity_id: str, activity_type: str, 
                        entity_id: Optional[str] = None, entity_type: Optional[str] = None, 
                        details: Optional[dict] = None) -> Activity:
        """
        Update an existing activity record in the database.

        Returns the updated Activity object.
        """
        activity = await self.get_by_id(activity_id)
        if not activity:
            return None
            
        # Update activity fields
        activity.type = activity_type
        activity.entity_id = entity_id
        activity.entity_type = entity_type
        activity.details = details or {}
        
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def delete_activity(self, activity: Activity) -> Activity:
        """
        Delete an activity record from the database.

        Returns the deleted Activity object.
        """
        self.db.delete(activity)
        await self.db.commit()
        return activity
