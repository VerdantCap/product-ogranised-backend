from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, condecimal
from typing import Optional, List
from datetime import date, time

class ExcursionBase(Model):  # Assuming Model is the base class from the ORM
    item_id: int
    name: str
    booking_ref: Optional[str] = None
    provider: Optional[str] = None
    excursion_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    contact_number: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    total_cost: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    deposit_paid: Optional[bool] = None
    deposit_amount: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    deposit_date: Optional[date] = None
    remaining_balance: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    balance_due_date: Optional[date] = None
    notes: Optional[str] = None
    attachments: Optional[List[str]] = None

    def item(self):
        return relationship("Item", back_populates="excursions")

class ExcursionCreate(ExcursionBase):
    pass

class ExcursionUpdate(ExcursionBase):
    pass

class ExcursionInDB(ExcursionBase):
    id: int

    class Config:
        orm_mode = True
