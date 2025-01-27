from pydantic import BaseModel 
from typing import Optional
from models.item_model import Item
from datetime import date, datetime

class Accommodation(BaseModel):
    item_id: str
    type: str
    provider: str
    booking_ref: Optional[str]
    location: str
    departure_date: date
    arrival_date: date
    deposit_date: date
    
    total_cost: float = None
    total_cost: Optional[str] = None
    notes: Optional[str] = None
    items: Item

class AccommodationCreate(BaseModel):
    item_id: int
    type: str
    provider: str
    booking_reference: Optional[str] = None
    location: str
    check_in: datetime
    check_out: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class AccommodationUpdate(BaseModel):
    type: Optional[str] = None
    provider: Optional[str] = None
    booking_reference: Optional[str] = None
    location: Optional[str] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
