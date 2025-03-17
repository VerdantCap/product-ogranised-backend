import logging
from fastapi import Depends
from typing import List, Optional
from sqlalchemy import asc, select
from models.event_model import Event
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime

# Set up a logger for the EventDAO
logger = logging.getLogger(__name__)

class EventDAO:
    """
    Data Access Object for Event.

    This class provides methods to perform CRUD operations on Event objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db
    
    async def create_event(self, event: Event):
        """
        Create a new event record in the database.

        Returns the created Event object.
        """
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def update_event(self, event: Event):
        """
        Update an existing event record in the database.

        Returns the updated Event object.
        """
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event
    
    async def delete_event(self, event: Event):
        """
        Delete an event record from the database.

        Returns the deleted Event object.
        """
        self.db.delete(event)
        await self.db.commit()
        return event

    async def get_by_id(self, event_id: str) -> Optional[Event]:
        """
        Retrieve an event record by its ID.

        Returns the Event object if found, otherwise None.
        """
        query = select(Event).where(Event.id == event_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Event]:
        """
        Retrieve event records by workspace ID with pagination.

        Returns a list of Event objects.
        """
        query = select(Event).where(Event.workspace_id == workspace_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_date_range(self, workspace_id: str, start_at: datetime, end_at: datetime) -> List[Event]:
        """
        Retrieve event records by workspace ID and date range.

        Returns a list of Event objects.
        """
        query = select(Event).where(
            Event.workspace_id == workspace_id,
            Event.start_at >= start_at, 
            Event.start_at <= end_at
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Event]:
        """
        Retrieve upcoming event records by workspace ID.

        Returns a list of Event objects ordered by start date.
        """
        query = select(Event).where(
            Event.workspace_id == workspace_id,
            Event.start_at > datetime.now()
        ).order_by(asc(Event.start_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_upcoming_events(self, workspace_id: str, from_date: datetime, skip: int = 0, limit: int = 100) -> List[Event]:
        """
        Retrieve upcoming event records by workspace ID starting from a specific date.

        Args:
            workspace_id: The ID of the workspace to filter events by
            from_date: The date from which to retrieve events
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            A list of Event objects ordered by start date.
        """
        query = select(Event).where(
            Event.workspace_id == workspace_id,
            Event.start_at > from_date
        ).order_by(asc(Event.start_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Event]:
        """
        Retrieve multiple event records with pagination.

        Returns a list of Event objects.
        """
        query = select(Event).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
