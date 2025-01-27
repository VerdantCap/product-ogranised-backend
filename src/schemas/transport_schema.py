from pydantic import BaseModel 
from typing import Optional
from datetime import datetime
from models.item_model import Item

class TransportBase(BaseModel):
    item_id: int
    type: str
    provider: str
    booking_reference: Optional[str] = None
    departure_location: str
    arrival_location: str
    departure_time: datetime
    arrival_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    item: Item

class TransportCreate(BaseModel):
    item_id: int
    type: str
    provider: str
    booking_reference: Optional[str] = None
    departure_location: str
    arrival_location: str
    departure_time: datetime
    arrival_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class TransportUpdate(BaseModel):
    type: Optional[str] = None
    provider: Optional[str] = None
    booking_reference: Optional[str] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None