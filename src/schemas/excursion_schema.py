from pydantic import BaseModel 
from typing import Optional
from datetime import datetime
from models.item_model import Item

class Excursion(BaseModel):
    item_id: int
    type: str
    provider: str
    booking_ref: Optional[str]
    location: str
    start_time: datetime
    end_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    item: Item

class ExcursionCreate(BaseModel):
    item_id: int
    type: str
    provider: str
    booking_ref: Optional[str] = None
    location: str
    start_time: datetime
    end_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class ExcursionUpdate(BaseModel):
    type: Optional[str] = None
    provider: Optional[str] = None
    booking_ref: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


