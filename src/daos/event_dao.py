import logging
from fastapi import Depends
from typing import List
from sqlalchemy import asc
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
    
    def create_event(self, event: Event):
        """
        Create a new event record in the database.

        Returns the created Event object.
        """
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update_event(self, event: Event):
        """
        Update an existing event record in the database.

        Returns the updated Event object.
        """
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def delete_event(self, event: Event):
        """
        Delete an event record from the database.

        Returns the deleted Event object.
        """
        self.db.delete(event)
        self.db.commit()
        return event

    def get_by_id(self, event_id: str):
        """
        Retrieve an event record by its ID.

        Returns the Event object if found, otherwise None.
        """
        return self.db.query(Event).filter(Event.id == event_id).first()

    def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Event]:
        """
        Retrieve event records by workspace ID with pagination.

        Returns a list of Event objects.
        """
        return self.db.query(Event).filter(Event.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()

    def get_by_date_range(self, workspace_id: str, start_at: datetime, end_at: datetime) -> List[Event]:
        """
        Retrieve event records by workspace ID and date range.

        Returns a list of Event objects.
        """
        return self.db.query(Event).filter(Event.workspace_id == workspace_id,
        Event.start_at >= start_at, Event.start_at <= end_at
        ).all()

    def get_upcoming(self, workspace_id: str) -> List[Event]:
        """
        Retrieve upcoming event records by workspace ID.

        Returns a list of Event objects ordered by start date.
        """
        return self.db.query(Event).filter(
            Event.workspace_id == workspace_id,
            Event.start_at > datetime.now()
        ).order_by(asc(Event.start_at)).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Event]:
        """
        Retrieve multiple event records with pagination.

        Returns a list of Event objects.
        """
        return self.db.query(Event).offset(skip).limit(limit).all()
