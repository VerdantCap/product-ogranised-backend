import logging
from fastapi import Depends
from typing import List
from sqlalchemy import asc
from models.event_model import Event
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime

logger = logging.getLogger(__name__)

class EventDAO:
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db
    
    def create_event(self, event: Event):
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update_event(self, event: Event):
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def delete_event(self, event: Event):
        self.db.delete(event)
        self.db.commit()
        return event

    def get_by_id(self, event_id: str):
        return self.db.query(Event).filter(Event.id == event_id).first()

    def get_by_workspace( self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Event]:
        return self.db.query(Event).filter(Event.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()

    def get_by_date_range( self, workspace_id: str, start_at: datetime, end_at: datetime) -> List[Event]:
        return self.db.query(Event).filter(Event.workspace_id == workspace_id,
        Event.start_at >= start_at, Event.start_at <= end_at
        ).all()

    def get_upcoming(
        self,
        workspace_id: str
    ) -> List[Event]:
        return self.db.query(Event).filter(
            Event.workspace_id == workspace_id,
            Event.start_at > datetime.now()
        ).order_by(asc(Event.start_at)).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Event]:
        return self.db.query(Event).offset(skip).limit(limit).all()