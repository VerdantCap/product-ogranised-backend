from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EventBase(Model):  # Assuming Model is the base class from the ORM
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None

    def casts(self) -> dict:
        return {
            "start_at": "datetime",
            "end_at": "datetime"
        }

class EventCreate(EventBase):
    pass
